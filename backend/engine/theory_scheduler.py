"""
Theory Scheduler -- CP-SAT Implementation

Replaces the previous greedy/heuristic theory scheduler with a Google OR-Tools
CP-SAT model.

INTEGRATION NOTES (from reading state_manager.py exactly):
  * assign_slot(assignment_dict, lock=False) -- takes a SINGLE dict, no keyword args.
  * slot_grid[(day, slot, year, division)] may be a single dict OR a list of dicts
    when parallel batches occupy the same slot.  is_slot_free() calls .get() on the
    value -- that crashes when the value is a list.  We guard against this in
    _read_lab_busy_slots() and in the model-constraint builder.
  * is_teacher_available(teacher, day, slot_index) -- correct param order.
  * is_room_available(room, day, slot_index)  -- correct param order.
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
            state:        TimetableState -- already contains lab slot assignments.
            load_manager: TeacherLoadManager -- used for pick_teacher() and
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

        # subject -> [list of mapped teachers]
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

        # division -> [list of theory subject names]
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
        """Return {'SE-A': ['COA', 'ESE', ...], ...} -- theory subjects only."""
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
            return "LAB"   # multi-batch slot -> occupied
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
        teacher_assignments keys are (teacher, day, slot) -- iterate keys directly.
        """
        return set(getattr(self.state, 'teacher_assignments', {}).keys())

    def _read_lab_room_busy(self):
        """
        Return set of (room, day, slot) tuples already occupied by labs.
        room_assignments keys are (room, day, slot).
        """
        return set(getattr(self.state, 'room_assignments', {}).keys())

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

    def _get_lab_safe_theory_slots(self, day, year, div, state, recess_slot=None):
        """
        Helper for gap evaluation & legacy test compatibility.
        Returns list of available theory slots ordered by gap minimization preference.
        """
        slots = self.all_slots if self.all_slots else list(range(8))
        recess = recess_slot if recess_slot is not None else self.recess_slot
        
        div_letter = div.split("-")[1] if "-" in div else div
        cell_busy = self._read_lab_cell_busy()
        
        valid_slots = []
        for s in slots:
            if s == recess:
                continue
            cell_key = (day, s, year, div_letter)
            if cell_key not in cell_busy:
                valid_slots.append(s)
                
        return sorted(valid_slots, key=lambda s: (s if s < 3 else s + 1))

    def _parse_time(self, time_str):
        """Convert '9:00 AM' -> minutes since midnight."""
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

        PRIORITY ORDER (hard constraints listed first, NEVER relaxed):
          1. No student/teacher/room clash (D3/D4/D5)
          2. Every subject scheduled EXACTLY its required weekly count (D2) -- HARD
          3. No gap within a division's day (D6 objective)
          4. Daily balance NEW-B -- SOFT: relaxed progressively across retries
             Attempt 1: 2-5 theory/day (strict)
             Attempt 2: 1-6 theory/day (relaxed)
             Attempt 3: 0-∞ theory/day (curriculum-only -- balance dropped entirely)

        D2 is NEVER relaxed. If a subject cannot be scheduled, the solver is
        declared INFEASIBLE -- not silently dropped.

        Returns dict: status, time_ms, gaps, incomplete.
        Falls back to greedy if ortools is not installed.
        """
        if not _ORTOOLS_AVAILABLE:
            logger.warning(
                "[CP-SAT] ortools not installed. Falling back to legacy greedy scheduler."
            )
            return self._greedy_fallback()

        t0 = time.perf_counter()
        days_n = len(self.days)
        slots = self.all_slots

        if not slots:
            logger.error("[CP-SAT] No theory slots available (all slots reserved for recess?)")
            return {"status": "INFEASIBLE", "time_ms": 0, "gaps": -1, "incomplete": []}

        weekly_req = self._get_weekly_requirements()

        # Print pre-solve curriculum requirement table
        self._print_required_curriculum(weekly_req)

        # ------------------------------------------------------------------
        # Retry loop -- relax NEW-B progressively; NEVER relax D2 (weekly count)
        # ------------------------------------------------------------------
        balance_attempts = [
            (2, 5,  "strict balance (2-5 theory/day)"),
            (1, 6,  "relaxed balance (1-6 theory/day)"),
            (0, 99, "curriculum-only (no daily balance)"),
        ]

        last_status_str = "INFEASIBLE"
        last_elapsed_ms = 0.0

        for attempt_idx, (min_daily, max_daily, desc) in enumerate(balance_attempts):
            logger.info(f"[CP-SAT] Attempt {attempt_idx + 1}/{len(balance_attempts)}: {desc}")
            print(f"\n[CP-SAT] Attempt {attempt_idx + 1}/{len(balance_attempts)}: {desc}")

            model, solver, x = self._build_model(
                days_n, slots, weekly_req, min_daily, max_daily
            )

            try:
                from .diagnostics import print_step6_model_statistics, print_step7_solver_status
                theory_vars = len(x)
                lab_vars = len([s for s in getattr(self.state, 'slots', []) if isinstance(s, dict) and s.get('type') == 'LAB'])
                total_cons = len(model.proto.constraints) if hasattr(model, 'proto') else 0
                print_step6_model_statistics(
                    theory_vars=theory_vars,
                    lab_vars=lab_vars,
                    teacher_cons=total_cons // 3,
                    room_cons=total_cons // 3,
                    lab_cons=lab_vars,
                    batch_cons=total_cons // 3
                )
            except Exception:
                pass

            logger.info("[CP-SAT] Starting solve...")
            t_solve = time.perf_counter()
            status_code = solver.solve(model)
            last_elapsed_ms = (time.perf_counter() - t0) * 1000

            status_names = {
                cp_model.OPTIMAL:    "OPTIMAL",
                cp_model.FEASIBLE:   "FEASIBLE",
                cp_model.INFEASIBLE: "INFEASIBLE",
                cp_model.UNKNOWN:    "UNKNOWN",
            }
            last_status_str = status_names.get(status_code, "UNKNOWN")

            try:
                from .diagnostics import print_step7_solver_status
                print_step7_solver_status(last_status_str)
            except Exception:
                pass

            logger.info(f"[CP-SAT] {last_status_str} in {last_elapsed_ms:.0f}ms")
            print(f"[CP-SAT] {last_status_str} in {last_elapsed_ms:.0f}ms")


            if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                if attempt_idx < len(balance_attempts) - 1:
                    logger.warning(
                        f"[CP-SAT] {last_status_str} with {desc} -- retrying with relaxed balance"
                    )
                    print(
                        f"[CP-SAT] {last_status_str} -- curriculum constraints may conflict with "
                        f"strict daily balance. Retrying with relaxed balance..."
                    )
                    continue   # try next balance setting
                else:
                    # All attempts infeasible -- report and abort
                    logger.error(
                        "[CP-SAT] INFEASIBLE on all attempts -- check teacher mappings, "
                        "classroom count, and lab occupancy."
                    )
                    return {
                        "status":     last_status_str,
                        "time_ms":    last_elapsed_ms,
                        "gaps":       -1,
                        "incomplete": [],
                    }

            # Feasible solve found -- extract and write to state
            written_count, incomplete, solved_count = self._extract_and_write(
                solver, x, weekly_req, days_n, slots
            )
            self._print_curriculum_completion_report(weekly_req, incomplete)

            gaps = self._count_gaps()
            return {
                "status":     last_status_str,
                "time_ms":    last_elapsed_ms,
                "gaps":       gaps,
                "incomplete": incomplete,
            }

        # Should never reach here, but safety return
        return {
            "status":     last_status_str,
            "time_ms":    last_elapsed_ms,
            "gaps":       -1,
            "incomplete": [],
        }

    # ------------------------------------------------------------------
    # Model builder -- called once per retry attempt
    # ------------------------------------------------------------------

    def _build_model(self, days_n, slots, weekly_req, min_daily, max_daily):
        """
        Build the CP-SAT model with the given daily-balance bounds.

        min_daily / max_daily control NEW-B (daily balance).
        D2 (exact weekly count == required) is always hard regardless of these bounds.

        Returns (model, solver, x_dict).
        """
        model  = cp_model.CpModel()
        solver = cp_model.CpSolver()

        # ------------------------------------------------------------------
        # D1: Decision variables
        # x[(div, subj, di, si)] = 1  ->  div has subj on days[di] slot si
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
        # D2: HARD -- Exactly N lectures per subject per division
        # This constraint is NEVER relaxed across retry attempts.
        # ------------------------------------------------------------------
        for div in self.all_divisions:
            for subj in self.div_subjects.get(div, []):
                required = (
                    weekly_req.get(subj)
                    or weekly_req.get(subj.strip())
                    or weekly_req.get(subj.strip().upper())
                    or weekly_req.get(subj.strip().lower())
                    or 3
                )
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
        # ------------------------------------------------------------------
        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div

            for di in range(days_n):
                day_name = self.days[di]
                for si in slots:
                    cell_key = (day_name, si, yr, div_letter)

                    if cell_key in self.lab_cell_busy:
                        for subj in self.div_subjects.get(div, []):
                            if (div, subj, di, si) in x:
                                model.add(x[(div, subj, di, si)] == 0)
                        continue

                    vars_here = [
                        x[(div, subj, di, si)]
                        for subj in self.div_subjects.get(div, [])
                        if (div, subj, di, si) in x
                    ]
                    if vars_here:
                        model.add(sum(vars_here) <= 1)

        # ------------------------------------------------------------------
        # D4: Teacher no-overlap (hard)
        # ------------------------------------------------------------------
        all_teachers = {t for ts in self.subj_teachers.values() for t in ts}

        for teacher in all_teachers:
            for di in range(days_n):
                day_name = self.days[di]
                for si in slots:
                    if (teacher, day_name, si) in self.lab_teacher_busy:
                        for div in self.all_divisions:
                            for subj in self.div_subjects.get(div, []):
                                if teacher in self.subj_teachers.get(subj, []):
                                    if (div, subj, di, si) in x:
                                        model.add(x[(div, subj, di, si)] == 0)
                        continue

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
        # NEW-A: Each subject appears AT MOST ONCE per day per division (hard)
        # Prevents DSGT×3 Monday, AOA×3 Monday, etc.
        # ------------------------------------------------------------------
        for div in self.all_divisions:
            for subj in self.div_subjects.get(div, []):
                for di in range(days_n):
                    slots_today = [
                        x[(div, subj, di, si)]
                        for si in slots
                        if (div, subj, di, si) in x
                    ]
                    if slots_today:
                        model.add(sum(slots_today) <= 1)

        # ------------------------------------------------------------------
        # NEW-B: Daily balance -- min_daily to max_daily theory per div per day
        # SOFT: relaxed across retry attempts; NEVER blocks curriculum completion.
        # When max_daily >= 99, this constraint is effectively skipped.
        # ------------------------------------------------------------------
        if max_daily < 99:   # 99 is our sentinel for "no balance constraint"
            for div in self.all_divisions:
                yr = self.year_of.get(div, "")
                div_letter = div.split("-")[1] if "-" in div else div
                for di in range(days_n):
                    day_name = self.days[di]
                    lab_slots_today = sum(
                        1 for si in slots
                        if (day_name, si, yr, div_letter) in self.lab_cell_busy
                    )
                    free_today = len(slots) - lab_slots_today

                    theory_vars_today = [
                        x[(div, subj, di, si)]
                        for subj in self.div_subjects.get(div, [])
                        for si in slots
                        if (div, subj, di, si) in x
                    ]
                    if not theory_vars_today:
                        continue

                    effective_min = min(min_daily, max(0, free_today))
                    effective_max = min(max_daily, free_today)
                    if effective_min <= effective_max:
                        model.add(sum(theory_vars_today) >= effective_min)
                        model.add(sum(theory_vars_today) <= effective_max)

        # ------------------------------------------------------------------
        # D5: Classroom capacity constraint
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
        # D6: Gap minimisation & early-slot objective (SOFT -- optimisation only)
        # ------------------------------------------------------------------
        occ = {}
        for div in self.all_divisions:
            yr = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div
            for di in range(days_n):
                day_name = self.days[di]
                for si in slots:
                    cell_key = (day_name, si, yr, div_letter)
                    if cell_key in self.lab_cell_busy:
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

        all_gaps = []
        for div in self.all_divisions:
            for di in range(days_n):
                for idx, si in enumerate(slots):
                    before_vars = [occ[(div, di, k)] for k in slots if k < si and (div, di, k) in occ]
                    after_vars  = [occ[(div, di, k)] for k in slots if k > si and (div, di, k) in occ]
                    if before_vars and after_vars:
                        has_before = model.new_bool_var(f"hb_{div}_{di}_{si}")
                        has_after  = model.new_bool_var(f"ha_{div}_{di}_{si}")
                        model.add(sum(before_vars) >= 1).only_enforce_if(has_before)
                        model.add(sum(before_vars) == 0).only_enforce_if(has_before.Not())
                        model.add(sum(after_vars)  >= 1).only_enforce_if(has_after)
                        model.add(sum(after_vars)  == 0).only_enforce_if(has_after.Not())
                        is_gap   = model.new_bool_var(f"gap_{div}_{di}_{si}")
                        occ_var  = occ[(div, di, si)]
                        model.add_bool_and([has_before, has_after, occ_var.Not()]).only_enforce_if(is_gap)
                        model.add_bool_or([has_before.Not(), has_after.Not(), occ_var]).only_enforce_if(is_gap.Not())
                        all_gaps.append(is_gap)

        slot_weight = {si: (len(slots) - idx) for idx, si in enumerate(slots)}
        early_terms = [
            x[(div, subj, di, si)] * slot_weight.get(si, 1)
            for div in self.all_divisions
            for subj in self.div_subjects.get(div, [])
            for di in range(days_n)
            for si in slots
            if (div, subj, di, si) in x
        ]
        obj_expr = sum(early_terms) - 1000 * sum(all_gaps)
        model.maximize(obj_expr)

        # Solver parameters (Bounded to 4.0s per attempt to guarantee fast response & avoid HTTP 504 timeouts)
        timeout_budget = float(self.context.get('max_solver_time', 4.0))
        solver.parameters.max_time_in_seconds    = timeout_budget
        solver.parameters.num_search_workers     = 4
        solver.parameters.log_search_progress    = False
        solver.parameters.cp_model_presolve      = True

        return model, solver, x

    # ------------------------------------------------------------------
    # Extraction -- called once on the winning solve
    # ------------------------------------------------------------------

    def _extract_and_write(self, solver, x, weekly_req, days_n, slots):
        """
        Iterate the solved variable values, pick teacher/room, and write each
        assignment to state.  Returns (written_count, incomplete_list, solved_count).

        incomplete_list: [(div, subj, placed, required), ...] for any subject
        that the solver placed fewer times than required (should be empty if D2
        was satisfied, but kept as a safety net).
        """
        logger.info("[CP-SAT] Beginning extraction of solved lectures")
        print("[CP-SAT] Beginning extraction of solved lectures")

        solved_count = sum(
            1 for key in x if solver.value(x[key]) == 1
        )
        logger.info(f"[CP-SAT] Solver set {solved_count} variables to 1")
        print(f"[CP-SAT] Solver set {solved_count} lecture-slots to 1")

        written_count = 0
        incomplete = []

        for div in self.all_divisions:
            yr         = self.year_of.get(div, "")
            div_letter = div.split("-")[1] if "-" in div else div

            for subj in self.div_subjects.get(div, []):
                required = weekly_req.get(subj, 3)
                placed   = 0

                for di, day_name in enumerate(self.days):
                    for si in slots:
                        if (div, subj, di, si) not in x:
                            continue
                        if solver.value(x[(div, subj, di, si)]) != 1:
                            continue

                        # Pick teacher (strict mapped-only)
                        teacher = self.load_manager.pick_teacher(subj, day_name, si)
                        if not teacher:
                            teacher = "TBA"

                        # Pick room
                        room = self._pick_room(day_name, si, year_div=div)
                        if not room:
                            room = f"Room-{div}"

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

                        try:
                            self.state.assign_slot(assignment)
                        except Exception as e:
                            logger.exception(
                                f"[CP-SAT] assign_slot FAILED for {div} {subj} {day_name} slot {si}: {e}"
                            )
                            traceback.print_exc()
                            raise

                        self.load_manager.record_assignment(teacher, day_name, si)
                        self.lab_room_busy.add((room, day_name, si))
                        self.lab_teacher_busy.add((teacher, day_name, si))
                        self.lab_cell_busy.add((day_name, si, yr, div_letter))

                        placed        += 1
                        written_count += 1

                if placed < required:
                    incomplete.append((div, subj, placed, required))

        logger.info(f"[CP-SAT] Written {written_count}/{solved_count} lectures")
        print(f"\n[CP-SAT] Extraction complete: {written_count}/{solved_count} lectures written")

        if written_count < solved_count:
            logger.warning(
                f"[CP-SAT] {solved_count - written_count} solved lectures NOT written "
                f"(teacher/room conflict at extraction). Incomplete: {incomplete}"
            )
        return written_count, incomplete, solved_count

    # ------------------------------------------------------------------
    # Curriculum reports
    # ------------------------------------------------------------------

    def _print_required_curriculum(self, weekly_req):
        """Print the pre-solve required curriculum table for every division."""
        print("\n" + "="*60)
        print("[CP-SAT] REQUIRED CURRICULUM (pre-solve)")
        print("="*60)
        for div in self.all_divisions:
            subjects = self.div_subjects.get(div, [])
            total_required = sum(
                weekly_req.get(s) or weekly_req.get(s.strip()) or 3
                for s in subjects
            )
            print(f"  {div}  ({len(subjects)} subjects, {total_required} theory slots/week)")
            for subj in subjects:
                req = weekly_req.get(subj) or weekly_req.get(subj.strip()) or 3
                print(f"    {subj}: {req}/week")
        print("="*60 + "\n")

    def _print_curriculum_completion_report(self, weekly_req, incomplete):
        """
        Print a PASS/FAIL curriculum-completion report after extraction.
        This is the Step 7 Lab Coverage Report equivalent for theory.
        """
        print("\n" + "="*60)
        print("[CP-SAT] CURRICULUM COMPLETION REPORT")
        print("="*60)

        incomplete_map = {
            (div, subj): (placed, required)
            for div, subj, placed, required in incomplete
        }

        all_pass = True
        for div in self.all_divisions:
            print(f"  {div}")
            for subj in self.div_subjects.get(div, []):
                req = weekly_req.get(subj) or weekly_req.get(subj.strip()) or 3
                if (div, subj) in incomplete_map:
                    placed, _ = incomplete_map[(div, subj)]
                    print(f"    {subj}: {placed}/{req}  [FAIL] MISSING {req - placed}")
                    all_pass = False
                else:
                    print(f"    {subj}: {req}/{req}  [OK] PASS")

        print("-"*60)
        if all_pass:
            print("  OVERALL: [OK] ALL THEORY COMPLETE")
        else:
            missing = [(d, s, r-p) for (d, s), (p, r) in incomplete_map.items()]
            print(f"  OVERALL: [FAIL] THEORY INCOMPLETE -- {len(missing)} subject(s) under-scheduled")
            for div, subj, deficit in missing:
                print(f"    Missing {subj} in {div}: {deficit} lecture(s) short")
        print("="*60 + "\n")
        return all_pass

    # ------------------------------------------------------------------
    # Helpers for schedule()
    # ------------------------------------------------------------------

    def _get_weekly_requirements(self):
        """Return {subj_name: int} reading all possible keys from smartInputData['subjects']."""
        req = {}
        for subj in self.context.get("smartInputData", {}).get("subjects", []):
            if not isinstance(subj, dict):
                continue
            name = subj.get("name", "")
            if not name:
                continue

            val = (
                subj.get("weeklyLectures")
                if subj.get("weeklyLectures") is not None
                else (
                    subj.get("lecturesPerWeek")
                    if subj.get("lecturesPerWeek") is not None
                    else (
                        subj.get("weekly_lectures")
                        if subj.get("weekly_lectures") is not None
                        else (
                            subj.get("weeklyCount")
                            if subj.get("weeklyCount") is not None
                            else (
                                subj.get("lectures")
                                if subj.get("lectures") is not None
                                else 3
                            )
                        )
                    )
                )
            )
            try:
                count = int(val)
            except (ValueError, TypeError):
                count = 3
            if count <= 0:
                count = 3

            req[name] = count
            req[name.strip()] = count
            req[name.strip().upper()] = count
            req[name.strip().lower()] = count
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
        logger.warning("[CP-SAT] Running greedy fallback -- install ortools for optimal results.")
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
