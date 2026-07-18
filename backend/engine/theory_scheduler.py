"""
Theory Scheduler — CP-SAT Implementation

Replaces the previous greedy/heuristic theory scheduler with a Google OR-Tools
CP-SAT model.

INTEGRATION NOTES (from reading state_manager.py exactly):
  * assign_slot(assignment_dict, lock=False) — takes a SINGLE dict, no keyword args.
  * slot_grid[(day, slot, year, division)] may be a single dict OR a list of dicts
    when parallel batches occupy the same slot.  is_slot_free() calls .get() on the
    value — that crashes when the value is a list.  We guard against this in
    _read_lab_busy_slots() and in the model-constraint builder.
  * is_teacher_available(teacher, day, slot_index) — correct param order.
  * is_room_available(room, day, slot_index)  — correct param order.
  * teacher_assignments keys are (teacher, day, slot) tuples.
  * room_assignments keys are (room, day, slot) tuples.

All exceptions during extraction are RAISED, never swallowed.
"""

import logging
import time
import traceback
from collections import defaultdict

try:
    from ortools.sat.python import cp_model
    _ORTOOLS_AVAILABLE = True
except ImportError:
    _ORTOOLS_AVAILABLE = False
    cp_model = None

logger = logging.getLogger(__name__)


class TheoryScheduler:

    def __init__(self, state, load_manager, context):
        """
        Args:
            state:        TimetableState — already contains lab slot assignments.
            load_manager: TeacherLoadManager — used for pick_teacher() and
                          record_assignment() after CP-SAT finds a placement.
            context:      Dict with 'branchData' and 'smartInputData'.
        """
        self.state = state
        self.load_manager = load_manager
        self.context = context

        branch = context.get("branchData", {})
        smart = context.get("smartInputData", {})

        self.days = branch.get("workingDays", [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
        ])
        self.all_divisions = self._get_all_divisions(branch)
        self.year_of = self._build_year_map(branch)
        self.classrooms = self._get_classrooms(branch)

        # Recess: prefer the value already written by time_utils into branch_data,
        # then fall back to what TimetableState computed, then to -1 (no recess).
        self.recess_slot = (
            branch.get("_computed_recess_slot")
            or getattr(state, "recess_slot", None)
        )
        if self.recess_slot is None:
            self.recess_slot = -1   # sentinel: no recess

        self.all_slots = self._get_theory_slots(branch)

        # subject → [list of mapped teachers]
        # Use load_manager's comprehensive cache (built from teacherSubjectMap + teacher.subjects)
        if hasattr(load_manager, 'subject_teacher_cache') and load_manager.subject_teacher_cache:
            self.subj_teachers = load_manager.subject_teacher_cache
        elif hasattr(load_manager, '_build_subject_teacher_map'):
            self.subj_teachers = load_manager._build_subject_teacher_map()
        else:
            self.subj_teachers = defaultdict(list)
            for m in smart.get("teacherSubjectMap", []):
                s = m.get("subjectName", "")
                t = m.get("teacherName", "")
                if s and t and t not in self.subj_teachers[s]:
                    self.subj_teachers[s].append(t)

        # division → [list of theory subject names]
        self.div_subjects = self._build_div_subjects(branch, smart)

        # Read already-placed lab occupancy from state.
        # We must be safe against list values in slot_grid.
        self.lab_teacher_busy = self._read_lab_busy_slots()
        self.lab_room_busy = self._read_lab_room_busy()
        # Also track which (day, slot, year, div) cells are occupied by labs
        self.lab_cell_busy = self._read_lab_cell_busy()

    # ------------------------------------------------------------------
    # Helper: data extraction
    # ------------------------------------------------------------------

    def _get_all_divisions(self, branch):
        """Return ['SE-A', 'SE-B', 'TE-A', ...] from branchData."""
        result = []
        for year in branch.get("academicYears", []):
            for div in branch.get("divisions", {}).get(year, []):
                result.append(f"{year}-{div}")
        return result

    def _build_year_map(self, branch):
        """Return {'SE-A': 'SE', 'TE-A': 'TE', ...}."""
        m = {}
        for year in branch.get("academicYears", []):
            for div in branch.get("divisions", {}).get(year, []):
                m[f"{year}-{div}"] = year
        return m

    def _get_classrooms(self, branch):
        """Return flat list of classroom names."""
        rooms = branch.get("classrooms", [])
        if not rooms:
            rooms = branch.get("rooms", [])
        if isinstance(rooms, dict):
            return [
                r
                for v in rooms.values()
                for r in (v if isinstance(v, list) else [v])
            ]
        result = []
        for r in rooms:
            if isinstance(r, dict):
                result.append(r.get("name", str(r)))
            else:
                result.append(str(r))
        if not result:
            result = ["Room-101", "Room-102", "Room-103", "Room-104", "Room-105"]
        return result

    def _get_theory_slots(self, branch):
        """Return slot indices usable for theory (all teaching slots)."""
        start = self._parse_time(branch.get("startTime", "9:00 AM"))
        end = self._parse_time(branch.get("endTime", "5:00 PM"))
        dur = int(branch.get("lectureDuration", 60))
        if dur <= 0:
            dur = 60
        total = (end - start) // dur
        return list(range(total))

    def _build_div_subjects(self, branch, smart):
        """Return {'SE-A': ['COA', 'ESE', ...], ...} — theory subjects only."""
        div_subj = defaultdict(list)
        for subj in smart.get("subjects", []):
            # Skip practicals / labs
            stype = str(subj.get("type", "")).strip().upper()
            if subj.get("isPractical") or stype in ("LAB", "PRACTICAL"):
                continue
            if subj.get("type") == "Practical":
                continue

            year = subj.get("year", "")
            target = subj.get("division", "")
            year_divs = [
                f"{year}-{d}"
                for d in branch.get("divisions", {}).get(year, [])
            ]
            apply_to = (
                [f"{year}-{target}"]
                if target and target.lower() not in ("all", "", "none")
                else year_divs
            )
            for div in apply_to:
                if div in self.all_divisions and subj["name"] not in div_subj[div]:
                    div_subj[div].append(subj["name"])
        return div_subj

    def _safe_get_type(self, val):
        """
        Safely extract 'type' from a slot_grid value that may be a dict or a list.
        Returns the type string, or 'LAB' if value is a list (always occupied).
        """
        if isinstance(val, list):
            return "LAB"   # multi-batch slot → occupied
        if isinstance(val, dict):
            return val.get("type", "")
        return ""

    def _slot_grid_has_entry(self, day, slot, year, div):
        """
        True if slot_grid[(day, slot, year, div)] exists AND is non-empty.
        Safe against both dict and list values.
        """
        key = (day, slot, year, div)
        val = self.state.slot_grid.get(key)
        if val is None:
            return False
        if isinstance(val, list):
            return len(val) > 0
        return True   # single dict

    def _read_lab_busy_slots(self):
        """
        Return set of (teacher, day, slot) tuples already occupied by labs.
        teacher_assignments keys are (teacher, day, slot) — iterate keys directly.
        """
        return set(self.state.teacher_assignments.keys())

    def _read_lab_room_busy(self):
        """
        Return set of (room, day, slot) tuples already occupied by labs.
        room_assignments keys are (room, day, slot).
        """
        return set(self.state.room_assignments.keys())

    def _read_lab_cell_busy(self):
        """
        Return set of (day, slot, year, div) tuples occupied by any existing slot.
        Safe against list values in slot_grid.
        """
        busy = set()
        for key, val in self.state.slot_grid.items():
            if val is None:
                continue
            if isinstance(val, list) and len(val) == 0:
                continue
            busy.add(key)  # key = (day, slot, year, div)
        return busy

    def _parse_time(self, time_str):
        """Convert '9:00 AM' → minutes since midnight."""
        try:
            try:
                from backend.utils.time_utils import parse_time as _pt
            except ImportError:
                from utils.time_utils import parse_time as _pt
            t = _pt(str(time_str))
            if t is not None:
                return t.hour * 60 + t.minute
        except Exception:
            pass

        import re
        m = re.match(r'(\d+):(\d+)\s*(AM|PM)?', str(time_str).strip().upper())
        if not m:
            return 0
        h, mn, p = int(m.group(1)), int(m.group(2)), m.group(3)
        if p == "PM" and h != 12:
            h += 12
        if p == "AM" and h == 12:
            h = 0
        return h * 60 + mn

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def schedule(self):
        """
        Build the CP-SAT model, solve it, extract the solution, and write
        placements to state via state.assign_slot(dict).

        Returns dict with keys: status, time_ms, gaps, incomplete.
        Falls back to greedy if ortools is not installed.
        """
        if not _ORTOOLS_AVAILABLE:
            logger.warning(
                "[CP-SAT] ortools not installed. Falling back to legacy greedy scheduler."
            )
            return self._greedy_fallback()

        t0 = time.perf_counter()

        model = cp_model.CpModel()
        solver = cp_model.CpSolver()

        days_n = len(self.days)
        slots = self.all_slots

        if not slots:
            logger.error("[CP-SAT] No theory slots available (all slots reserved for recess?)")
            return {"status": "INFEASIBLE", "time_ms": 0, "gaps": -1, "incomplete": []}

        # ------------------------------------------------------------------
        # D1: Decision variables
        # x[(div, subj, di, si)] = 1  →  div has subj on days[di] slot si
        # ------------------------------------------------------------------
        x = {}
        for div in self.all_divisions:
            for subj in self.div_subjects.get(div, []):
                for di in range(days_n):
                    for si in slots:
                        x[(div, subj, di, si)] = model.new_bool_var(
                            f"x_{div}_{subj}_{di}_{si}"
                        )

        logger.info(f"[CP-SAT] {len(x)} variables created for {len(self.all_divisions)} divisions")

        # ------------------------------------------------------------------
        # D2: Exactly N lectures per subject per division
        # ------------------------------------------------------------------
        weekly_req = self._get_weekly_requirements()

        for div in self.all_divisions:
            for subj in self.div_subjects.get(div, []):
                required = weekly_req.get(subj, 3)
                model.add(
                    sum(
                        x[(div, subj, di, si)]
                        for di in range(days_n)
                        for si in slots
                        if (div, subj, di, si) in x
                    ) == required
                )

        # ------------------------------------------------------------------
        # D3: At most 1 subject per slot per division
        #     Force 0 if lab already occupies that slot.
        #     We use _slot_grid_has_entry() which is safe against list values.
        # ------------------------------------------------------------------
        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div

            for di in range(days_n):
                day_name = self.days[di]
                for si in slots:
                    cell_key = (day_name, si, yr, div_letter)

                    # Cell occupied by lab → force all theory vars to 0
                    if cell_key in self.lab_cell_busy:
                        for subj in self.div_subjects.get(div, []):
                            if (div, subj, di, si) in x:
                                model.add(x[(div, subj, di, si)] == 0)
                        continue

                    # At most 1 subject per slot per division
                    vars_here = [
                        x[(div, subj, di, si)]
                        for subj in self.div_subjects.get(div, [])
                        if (div, subj, di, si) in x
                    ]
                    if vars_here:
                        model.add(sum(vars_here) <= 1)

        # ------------------------------------------------------------------
        # D4: Teacher no-overlap (hard)
        # lab_teacher_busy = set of (teacher, day, slot) keys from state
        # ------------------------------------------------------------------
        all_teachers = {
            t for ts in self.subj_teachers.values() for t in ts
        }

        for teacher in all_teachers:
            for di in range(days_n):
                day_name = self.days[di]
                for si in slots:
                    # Teacher busy with lab → force all theory vars to 0
                    if (teacher, day_name, si) in self.lab_teacher_busy:
                        for div in self.all_divisions:
                            for subj in self.div_subjects.get(div, []):
                                if teacher in self.subj_teachers.get(subj, []):
                                    if (div, subj, di, si) in x:
                                        model.add(x[(div, subj, di, si)] == 0)
                        continue

                    # At most 1 theory class using this teacher per slot
                    uses = [
                        x[(div, subj, di, si)]
                        for div in self.all_divisions
                        for subj in self.div_subjects.get(div, [])
                        if teacher in self.subj_teachers.get(subj, [])
                        and (div, subj, di, si) in x
                    ]
                    if uses:
                        model.add(sum(uses) <= 1)

        # ------------------------------------------------------------------
        # D5: Classroom capacity constraint
        # lab_room_busy = set of (room, day, slot) keys from state
        # ------------------------------------------------------------------
        max_rooms = len(self.classrooms)

        for di in range(days_n):
            day_name = self.days[di]
            for si in slots:
                labs_using = sum(
                    1 for room in self.classrooms
                    if (room, day_name, si) in self.lab_room_busy
                )
                remaining = max_rooms - labs_using

                if remaining <= 0:
                    for div in self.all_divisions:
                        for subj in self.div_subjects.get(div, []):
                            if (div, subj, di, si) in x:
                                model.add(x[(div, subj, di, si)] == 0)
                    continue

                theory_here = [
                    x[(div, subj, di, si)]
                    for div in self.all_divisions
                    for subj in self.div_subjects.get(div, [])
                    if (div, subj, di, si) in x
                ]
                if theory_here:
                    model.add(sum(theory_here) <= remaining)

        # ------------------------------------------------------------------
        # D6: Gap Minimization & Daily Contiguity Objective
        # ------------------------------------------------------------------
        # Define cell occupancy per division-day-slot
        occ = {}
        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div

            for di in range(days_n):
                day_name = self.days[di]
                for si in slots:
                    cell_key = (day_name, si, yr, div_letter)
                    if cell_key in self.lab_cell_busy:
                        # Constant 1 if lab is here
                        bvar = model.new_bool_var(f"occ_lab_{div}_{di}_{si}")
                        model.add(bvar == 1)
                        occ[(div, di, si)] = bvar
                    else:
                        vars_here = [
                            x[(div, subj, di, si)]
                            for subj in self.div_subjects.get(div, [])
                            if (div, subj, di, si) in x
                        ]
                        if vars_here:
                            bvar = model.new_bool_var(f"occ_theory_{div}_{di}_{si}")
                            model.add(sum(vars_here) == bvar)
                            occ[(div, di, si)] = bvar
                        else:
                            bvar = model.new_bool_var(f"occ_empty_{div}_{di}_{si}")
                            model.add(bvar == 0)
                            occ[(div, di, si)] = bvar

        # Gap variables per division-day-slot
        all_gaps = []

        for div in self.all_divisions:
            for di in range(days_n):
                for idx, si in enumerate(slots):
                    before_vars = [occ[(div, di, k)] for k in slots if k < si]
                    after_vars = [occ[(div, di, k)] for k in slots if k > si]

                    if before_vars and after_vars:
                        has_before = model.new_bool_var(f"hb_{div}_{di}_{si}")
                        has_after = model.new_bool_var(f"ha_{div}_{di}_{si}")

                        model.add(sum(before_vars) >= 1).only_enforce_if(has_before)
                        model.add(sum(before_vars) == 0).only_enforce_if(has_before.Not())

                        model.add(sum(after_vars) >= 1).only_enforce_if(has_after)
                        model.add(sum(after_vars) == 0).only_enforce_if(has_after.Not())

                        is_gap = model.new_bool_var(f"gap_{div}_{di}_{si}")
                        occ_var = occ[(div, di, si)]
                        
                        model.add_bool_and([has_before, has_after, occ_var.Not()]).only_enforce_if(is_gap)
                        model.add_bool_or([has_before.Not(), has_after.Not(), occ_var]).only_enforce_if(is_gap.Not())
                        all_gaps.append(is_gap)

        # Early slot weight
        slot_weight = {si: (len(slots) - idx) for idx, si in enumerate(slots)}
        early_terms = [
            x[(div, subj, di, si)] * slot_weight.get(si, 1)
            for div in self.all_divisions
            for subj in self.div_subjects.get(div, [])
            for di in range(days_n)
            for si in slots
            if (div, subj, di, si) in x
        ]

        # Objective: Heavy Penalty for Gaps (-1000 per gap slot), Reward Early Slots
        obj_expr = sum(early_terms) - 1000 * sum(all_gaps)
        model.maximize(obj_expr)

        # ------------------------------------------------------------------
        # Solver parameters
        # ------------------------------------------------------------------
        solver.parameters.max_time_in_seconds = 30.0
        solver.parameters.num_search_workers = 4
        solver.parameters.log_search_progress = False
        solver.parameters.cp_model_presolve = True

        # ------------------------------------------------------------------
        # Solve
        # ------------------------------------------------------------------
        logger.info("[CP-SAT] Starting solve...")
        status_code = solver.solve(model)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        status_names = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        status_str = status_names.get(status_code, "UNKNOWN")
        logger.info(f"[CP-SAT] {status_str} in {elapsed_ms:.0f}ms")
        print(f"[CP-SAT] {status_str} in {elapsed_ms:.0f}ms")

        if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.error(
                "[CP-SAT] INFEASIBLE — check teacher mappings and classroom count."
            )
            return {
                "status": status_str,
                "time_ms": elapsed_ms,
                "gaps": -1,
                "incomplete": [],
            }

        # ------------------------------------------------------------------
        # Extract solution and write to state
        # ------------------------------------------------------------------
        logger.info("[CP-SAT] Beginning extraction of solved lectures")
        print("[CP-SAT] Beginning extraction of solved lectures")

        # Count how many variables the solver set to 1
        solved_count = sum(
            1
            for (div, subj, di, si) in x
            if solver.value(x[(div, subj, di, si)]) == 1
        )
        logger.info(f"[CP-SAT] Solver set {solved_count} variables to 1")
        print(f"[CP-SAT] Solver set {solved_count} lecture-slots to 1")

        written_count = 0
        incomplete = []

        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div

            for subj in self.div_subjects.get(div, []):
                required = weekly_req.get(subj, 3)
                placed = 0

                for di, day_name in enumerate(self.days):
                    for si in slots:
                        if (div, subj, di, si) not in x:
                            continue
                        if solver.value(x[(div, subj, di, si)]) != 1:
                            continue

                        logger.info(
                            f"[CP-SAT] Extracting {div} {subj} {day_name} slot={si}"
                        )
                        print(
                            f"[CP-SAT] Extracting: {div} | {subj} | {day_name} | slot {si}"
                        )

                        # Pick teacher — uses pick_teacher with fallbacks
                        teacher = self.load_manager.pick_teacher(subj, day_name, si)
                        if not teacher:
                            teacher = "TBA"

                        # Pick room — uses _pick_room with fallbacks
                        room = self._pick_room(day_name, si, year_div=div)
                        if not room:
                            room = f"Room-{div}"

                        # Build assignment dict — matches assign_slot(assignment_dict, lock=False) exactly
                        assignment = {
                            "day":      day_name,
                            "slot":     si,
                            "year":     yr,
                            "division": div_letter,
                            "subject":  subj,
                            "teacher":  teacher,
                            "room":     room,
                            "type":     "THEORY",
                        }

                        logger.info(
                            f"[CP-SAT] Writing slot: day={day_name!r} slot={si} "
                            f"year={yr!r} division={div_letter!r} "
                            f"subject={subj!r} teacher={teacher!r} room={room!r}"
                        )

                        # Write to state — RAISE on any failure, never swallow
                        try:
                            self.state.assign_slot(assignment)
                        except Exception as e:
                            logger.exception(
                                f"[CP-SAT] assign_slot FAILED for {div} {subj} "
                                f"{day_name} slot {si}: {e}"
                            )
                            print(
                                f"  ERROR: assign_slot raised for {div} {subj} "
                                f"{day_name} slot {si}:"
                            )
                            traceback.print_exc()
                            raise   # propagate — never swallow scheduling errors

                        logger.info("[CP-SAT] assign_slot completed successfully")
                        print(f"  OK: Written {div} {subj} {day_name} slot {si}")

                        # Update load tracking
                        self.load_manager.record_assignment(teacher, day_name, si)

                        # Mark room as used so subsequent picks in this batch avoid it
                        self.lab_room_busy.add((room, day_name, si))
                        # Update teacher busy set for subsequent constraint checks
                        self.lab_teacher_busy.add((teacher, day_name, si))
                        # Mark cell as used
                        self.lab_cell_busy.add((day_name, si, yr, div_letter))

                        placed += 1
                        written_count += 1

                if placed < required:
                    incomplete.append((div, subj, placed, required))

        # ------------------------------------------------------------------
        # Mandatory post-extraction validation
        # ------------------------------------------------------------------
        logger.info(f"[CP-SAT] Written lectures = {written_count} (solver set {solved_count} to 1)")
        print(f"\n[CP-SAT] Extraction complete: {written_count}/{solved_count} lectures written")

        if written_count < solved_count:
            msg = (
                f"[CP-SAT] WARNING: {solved_count - written_count} solved lectures were NOT written "
                f"(teacher/room unavailable at extraction time). "
                f"Incomplete: {incomplete}"
            )
            logger.warning(msg)
            print(msg)

        # Print division-level summary
        print("\n[CP-SAT] Division lecture summary:")
        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div
            for subj in self.div_subjects.get(div, []):
                expected = weekly_req.get(subj, 3)
                actual = self.state.get_subject_count(subj, yr, div_letter)
                status = "OK" if actual >= expected else f"MISSING {expected - actual}"
                print(f"  {div} | {subj}: {actual}/{expected} [{status}]")

        gaps = self._count_gaps()
        return {
            "status":     status_str,
            "time_ms":    elapsed_ms,
            "gaps":       gaps,
            "incomplete": incomplete,
        }

    # ------------------------------------------------------------------
    # Helpers for schedule()
    # ------------------------------------------------------------------

    def _get_weekly_requirements(self):
        """Return {subj_name: int} from subjects[].weeklyLectures. Default 3."""
        req = {}
        for subj in self.context.get("smartInputData", {}).get("subjects", []):
            name = subj.get("name", "")
            count = subj.get("weeklyLectures") or subj.get("lecturesPerWeek") or 3
            req[name] = int(count)
        return req

    def _pick_room(self, day_name, slot_idx, year_div=""):
        """
        Return first classroom not busy at this day+slot.
        Checks both the pre-built lab_room_busy set AND state.is_room_available().
        Falls back to a default classroom string if all are occupied.
        """
        for room in self.classrooms:
            if (room, day_name, slot_idx) in self.lab_room_busy:
                continue
            if not self.state.is_room_available(room, day_name, slot_idx):
                continue
            return room
        if self.classrooms:
            return self.classrooms[0]
        return f"Room-{year_div}" if year_div else "Room-101"

    def _count_gaps(self):
        """Count empty slots between first and last occupied slot per div per day."""
        total = 0
        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            dl = div.split("-")[1] if "-" in div else div
            for day_name in self.days:
                occupied = [
                    si for si in self.all_slots
                    if self._slot_grid_has_entry(day_name, si, yr, dl)
                ]
                if len(occupied) < 2:
                    continue
                for si in range(min(occupied), max(occupied) + 1):
                    if si == self.recess_slot:
                        continue
                    if not self._slot_grid_has_entry(day_name, si, yr, dl):
                        total += 1
        return total

    # ------------------------------------------------------------------
    # Greedy fallback (used only when ortools is not installed)
    # ------------------------------------------------------------------

    def _greedy_fallback(self):
        """
        Minimal greedy fallback so the scheduler does not hard-crash when
        ortools is unavailable.
        """
        logger.warning("[CP-SAT] Running greedy fallback — install ortools for optimal results.")
        incomplete = []
        weekly_req = self._get_weekly_requirements()

        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            dl = div.split("-")[1] if "-" in div else div

            for subj in self.div_subjects.get(div, []):
                required = weekly_req.get(subj, 3)
                placed = 0

                for di, day_name in enumerate(self.days):
                    if placed >= required:
                        break
                    for si in self.all_slots:
                        if placed >= required:
                            break
                        cell_key = (day_name, si, yr, dl)
                        if cell_key in self.lab_cell_busy:
                            continue
                        teacher = self.load_manager.pick_teacher(subj, day_name, si)
                        room = self._pick_room(day_name, si)
                        if not teacher or not room:
                            continue
                        assignment = {
                            "day": day_name, "slot": si,
                            "year": yr, "division": dl,
                            "subject": subj, "teacher": teacher,
                            "room": room, "type": "THEORY",
                        }
                        self.state.assign_slot(assignment)
                        self.load_manager.record_assignment(teacher, day_name, si)
                        self.lab_room_busy.add((room, day_name, si))
                        self.lab_teacher_busy.add((teacher, day_name, si))
                        self.lab_cell_busy.add(cell_key)
                        placed += 1

                if placed < required:
                    incomplete.append((div, subj, placed, required))

        return {
            "status": "FEASIBLE (greedy fallback)",
            "time_ms": 0,
            "gaps": self._count_gaps(),
            "incomplete": incomplete,
        }

    # ------------------------------------------------------------------
    # Legacy compatibility shim
    # ------------------------------------------------------------------

    _global_schedule_done = False

    def schedule_theory(self, class_info):
        """
        Legacy shim: called by old per-class loop in scheduler.py.
        Delegates to schedule() on first call and is a safe no-op thereafter.
        """
        if not TheoryScheduler._global_schedule_done:
            TheoryScheduler._global_schedule_done = True
            self.schedule()
        return True
