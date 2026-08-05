import itertools

def is_lab_subject(s):
    if not isinstance(s, dict):
        return False
    if s.get('isPractical') is True or str(s.get('isPractical')).lower() in ('true', '1'):
        return True
    stype = str(s.get('type', '')).strip().upper()
    if stype in ('PRACTICAL', 'LAB', 'LABS', 'PRACTICALS'):
        return True
    sname = str(s.get('name', '')).strip().upper()
    if sname.endswith(' LAB') or sname.endswith(' L') or 'LAB' in sname or 'PRACTICAL' in sname:
        return True
    return False

def matches_year(subj_year, target_year):
    if not subj_year:
        return True
    sy = str(subj_year).strip().upper()
    ty = str(target_year).strip().upper()
    if sy == ty:
        return True
    aliases = {
        'SE': ['SECOND YEAR', 'SE', '2ND YEAR', 'II'],
        'TE': ['THIRD YEAR', 'TE', '3RD YEAR', 'III'],
        'BE': ['FINAL YEAR', 'BE', '4TH YEAR', 'IV', 'BACHELOR OF ENGINEERING']
    }
    for key, vals in aliases.items():
        if (ty == key or ty in vals) and (sy == key or sy in vals):
            return True
    return sy.replace('-', '').replace(' ', '') == ty.replace('-', '').replace(' ', '')

def matches_division(subj_div, target_div, target_year=None):
    if not subj_div:
        return True
    if isinstance(subj_div, list):
        return any(matches_division(d, target_div, target_year) for d in subj_div)
    sd = str(subj_div).strip().upper()
    td = str(target_div).strip().upper()
    if not sd or sd in ("ALL", "NONE", "NULL"):
        return True
    if sd == td:
        return True
    if target_year:
        ty = str(target_year).strip().upper()
        sd = sd.replace(ty, '').strip()
        td = td.replace(ty, '').strip()
    sd_clean = sd.replace('-', '').replace('_', '').replace(' ', '')
    td_clean = td.replace('-', '').replace('_', '').replace(' ', '')
    return sd_clean == td_clean


class LabScheduler:
    def __init__(self, state, context):
        self.state = state
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})

        self.labs = self.branch_data.get('sharedLabs', [])
        if not self.labs and 'labs' in self.branch_data:
            self.labs = [{"name": l} for l in self.branch_data['labs']]

        self.lab_batches_per_year = self.branch_data.get('labBatchesPerYear', {})
        self.subject_teachers = self._map_teachers_to_subjects()

    def _map_teachers_to_subjects(self):
        """Map subject names (raw and canonical IDs) to available teachers."""
        mapping = {}
        try:
            from .diagnostics import get_canonical_subject_id
        except ImportError:
            def get_canonical_subject_id(x): return str(x).upper()

        teachers = self.smart_input.get('teachers', [])

        # 1. Use explicit mapping if available
        teacher_subject_map = self.smart_input.get('teacherSubjectMap', [])
        for entry in teacher_subject_map:
            sub = entry.get('subjectName')
            teacher = entry.get('teacherName')
            if sub and teacher:
                if isinstance(sub, str) and ',' in sub:
                    subs = [x.strip() for x in sub.split(',')]
                elif isinstance(sub, list):
                    subs = sub
                else:
                    subs = [str(sub)]
                for s in subs:
                    cid = get_canonical_subject_id(s)
                    for k in (s, cid):
                        if k not in mapping: mapping[k] = []
                        if teacher not in mapping[k]:
                            mapping[k].append(teacher)

        # 2. Fallback to teacher 'subjects' list
        for teacher in teachers:
            t_name = teacher.get('name')
            t_subjects = teacher.get('subjects', [])
            if isinstance(t_subjects, str):
                t_subjects = [x.strip() for x in t_subjects.split(',')]
            for sub in t_subjects:
                cid = get_canonical_subject_id(sub)
                for k in (sub, cid):
                    if k not in mapping: mapping[k] = []
                    if t_name not in mapping[k]:
                        mapping[k].append(t_name)

        return mapping


    def schedule_class_labs(self, class_info):
        """
        Schedule practicals using independent sub-batch parallel rotation.
        """
        if not isinstance(class_info, dict):
            raise TypeError(f"Expected class_info dict, got {type(class_info)}")

        year = class_info.get('year')
        division = class_info.get('division')

        num_batches = int(self.lab_batches_per_year.get(year, 3))
        batches = [f"B{b+1}" for b in range(num_batches)]

        lab_subjects = [
            s for s in self.smart_input.get('subjects', [])
            if matches_year(s.get('year'), year)
            and matches_division(s.get('division'), division, year)
            and is_lab_subject(s)
        ]

        if not lab_subjects:
            print(f"  No verified lab subjects for {year}-{division}")
            return True

        # STEP 3 Diagnostic: Print Practical Variable Creation
        creation_results = {}
        for s in lab_subjects:
            sname = s['name']
            mapped_t = self.subject_teachers.get(sname, [])
            if not mapped_t:
                creation_results[sname] = {'created': False, 'reason': 'No valid teacher'}
            elif not self.labs:
                creation_results[sname] = {'created': False, 'reason': 'No valid lab'}
            else:
                creation_results[sname] = {'created': True}

        try:
            from .diagnostics import print_step3_variable_creation
            print_step3_variable_creation(f"{year}-{division}", lab_subjects, creation_results)
        except Exception:
            pass

        print(f"  Scheduling parallel rotated labs for {year}-{division} (Batches: {batches})")
        print(f"  Required Labs ({len(lab_subjects)}): {[s['name'] for s in lab_subjects]}")

        remaining = {b: [s['name'] for s in lab_subjects] for b in batches}
        subject_map = {s['name']: s for s in lab_subjects}

        standard_duration = 2
        windows = self._get_valid_windows(year, division, duration=standard_duration)

        for window in windows:
            day = window['day']
            start_slot = window['start_slot']
            duration = window['duration']

            active_batches = []
            for b in batches:
                if not remaining[b]:
                    continue
                if not self._is_batch_free(day, start_slot, duration, year, division, b):
                    try:
                        from .diagnostics import print_step5_rejected_candidate
                        print_step5_rejected_candidate(day, f"{start_slot}-{start_slot+duration-1}", f"Batch {b} Busy")
                    except Exception:
                        pass
                    continue
                if self._does_batch_have_lab_on_day(year, division, b, day):
                    try:
                        from .diagnostics import print_step5_rejected_candidate
                        print_step5_rejected_candidate(day, f"{start_slot}-{start_slot+duration-1}", f"Batch {b} Already Has Lab On {day}")
                    except Exception:
                        pass
                    continue
                active_batches.append(b)

            if not active_batches:
                continue

            assignment = self._find_parallel_rotation_block(
                year, division, active_batches, remaining, subject_map, day, start_slot, duration
            )

            if assignment:
                for b, (subj_name, teacher, room) in assignment.items():
                    subj_obj = subject_map[subj_name]
                    subj_dur = int(subj_obj.get('sessionLength') or subj_obj.get('slots') or duration)
                    self._commit_assignment(year, division, b, subj_obj, teacher, room, day, start_slot, subj_dur)
                    remaining[b].remove(subj_name)

                    try:
                        from .diagnostics import print_step4_attempt
                        print_step4_attempt(
                            div=f"{year}-{division}",
                            batch=b,
                            subject=subj_name,
                            teacher=teacher,
                            lab=room,
                            day=day,
                            slot=f"{start_slot}-{start_slot+subj_dur-1}",
                            result="SUCCESS"
                        )
                    except Exception:
                        pass

                    print(
                        f"    [Rotation] {year}-{division} {b} -> {subj_name} | "
                        f"Teacher: {teacher} | Room: {room} on {day} slot {start_slot}-{start_slot+subj_dur-1}"
                    )

            if all(len(rem) == 0 for rem in remaining.values()):
                break


        if any(len(rem) > 0 for rem in remaining.values()):
            print(f"  [WARNING] Parallel rotation pass incomplete. Running individual batch placement fallback...")
            for b in batches:
                for subj_name in list(remaining[b]):
                    subj_obj = subject_map[subj_name]
                    subj_dur = int(subj_obj.get('sessionLength') or subj_obj.get('slots') or standard_duration)
                    if self._assign_batch_subject(year, division, b, subj_obj, subj_dur):
                        remaining[b].remove(subj_name)

        all_done = all(len(rem) == 0 for rem in remaining.values())
        if all_done:
            print(f"  [OK] All lab subjects successfully scheduled for all batches in {year}-{division}.")
        else:
            incomplete_summary = {b: rem for b, rem in remaining.items() if rem}
            print(f"  [FAIL] Lab scheduling incomplete for {year}-{division}: {incomplete_summary}")

        return all_done

    def _find_parallel_rotation_block(self, year, division, active_batches, remaining, subject_map, day, start_slot, duration):
        all_needed_subjects = list(set(s for b in active_batches for s in remaining[b]))

        possible_tuples = []
        for proj in itertools.permutations(all_needed_subjects, len(active_batches)):
            if all(proj[i] in remaining[active_batches[i]] for i in range(len(active_batches))):
                possible_tuples.append(proj)

        for proj in possible_tuples:
            res = self._search_teachers_and_rooms(
                active_batches, proj, subject_map, day, start_slot, duration
            )
            if res:
                return res

        for k in range(len(active_batches) - 1, 0, -1):
            for batch_sub in itertools.combinations(active_batches, k):
                sub_needed = list(set(s for b in batch_sub for s in remaining[b]))
                for proj in itertools.permutations(sub_needed, len(batch_sub)):
                    if all(proj[i] in remaining[batch_sub[i]] for i in range(len(batch_sub))):
                        res = self._search_teachers_and_rooms(
                            batch_sub, proj, subject_map, day, start_slot, duration
                        )
                        if res:
                            return res

        return None

    def _search_teachers_and_rooms(self, batch_list, subject_tuple, subject_map, day, start_slot, duration):
        assigned_teachers = set()
        assigned_rooms = set()
        result = {}

        def backtrack(idx):
            if idx == len(batch_list):
                return True

            b = batch_list[idx]
            s_name = subject_tuple[idx]
            s_obj = subject_map[s_name]
            s_dur = int(s_obj.get('sessionLength') or s_obj.get('slots') or duration)

            candidate_teachers = self._get_available_mapped_teachers(
                s_name, day, start_slot, s_dur, exclude_teachers=assigned_teachers
            )
            candidate_rooms = self._get_available_lab_rooms(
                s_name, day, start_slot, s_dur, exclude_rooms=assigned_rooms
            )

            for t in candidate_teachers:
                for r in candidate_rooms:
                    assigned_teachers.add(t)
                    assigned_rooms.add(r)
                    result[b] = (s_name, t, r)

                    if backtrack(idx + 1):
                        return True

                    assigned_teachers.remove(t)
                    assigned_rooms.remove(r)
                    del result[b]

            return False

        if backtrack(0):
            return result
        return None

    def _get_available_mapped_teachers(self, subject_name, day, start_slot, duration, exclude_teachers=None):
        if exclude_teachers is None:
            exclude_teachers = set()

        try:
            from .diagnostics import get_canonical_subject_id
            cid = get_canonical_subject_id(subject_name)
        except ImportError:
            cid = str(subject_name).upper()

        mapped = list(self.subject_teachers.get(subject_name, []))
        cid_mapped = self.subject_teachers.get(cid, [])
        for t in cid_mapped:
            if t not in mapped:
                mapped.append(t)

        if hasattr(self.state, 'load_manager') and self.state.load_manager:
            lm_mapped = list(self.state.load_manager.subject_teacher_map.get(subject_name, []))
            if not lm_mapped:
                lm_mapped = list(self.state.load_manager.subject_teacher_map.get(cid, []))
            for t in lm_mapped:
                if t not in mapped:
                    mapped.append(t)

        available_teachers = []
        for t_name in mapped:
            if t_name in exclude_teachers:
                continue
            free = True
            for offset in range(duration):
                if not self.state.is_teacher_available(t_name, day, start_slot + offset):
                    free = False
                    break
            if free:
                available_teachers.append(t_name)

        return available_teachers


    def _get_available_lab_rooms(self, subject_dict_or_name, day, start_slot, duration, exclude_rooms=None):
        if exclude_rooms is None:
            exclude_rooms = set()

        available_rooms = []
        for lab in self.labs:
            name = lab['name'] if isinstance(lab, dict) else str(lab)
            if name in exclude_rooms:
                continue
            free = True
            for offset in range(duration):
                if not self.state.is_lab_globally_available(name, day, start_slot + offset):
                    free = False
                    break
                if not self.state.is_room_available(name, day, start_slot + offset):
                    free = False
                    break
            if free:
                available_rooms.append(name)

        return available_rooms

    def _assign_batch_subject(self, year, division, batch, subject, duration):
        windows = self._get_valid_windows(year, division, duration)

        for window in windows:
            day = window['day']
            start_slot = window['start_slot']

            if not self._is_batch_free(day, start_slot, duration, year, division, batch):
                continue

            if self._does_batch_have_lab_on_day(year, division, batch, day):
                continue

            lab_rooms = self._get_available_lab_rooms(subject, day, start_slot, duration)
            if not lab_rooms:
                continue

            teachers = self._get_available_mapped_teachers(subject['name'], day, start_slot, duration)
            if not teachers:
                continue

            lab_room = lab_rooms[0]
            teacher = teachers[0]

            self._commit_assignment(year, division, batch, subject, teacher, lab_room, day, start_slot, duration)
            print(f"    Assigned {subject['name']} to {batch} on {day} slot {start_slot} (Duration: {duration})")
            return True

        return False

    def _is_batch_free(self, day, start_slot, duration, year, division, batch):
        for offset in range(duration):
            slot_idx = start_slot + offset
            assignments = self.state.get_slot_assignment(day, slot_idx, year, division)
            if assignments:
                slot_assignments = assignments if isinstance(assignments, list) else [assignments]
                for a in slot_assignments:
                    if isinstance(a, dict):
                        if a.get('batch') == batch:
                            return False
                        if a.get('type') == 'THEORY':
                            return False
        return True

    def _does_batch_have_lab_on_day(self, year, division, batch, day):
        filled_slots = getattr(self.state, 'slots', [])
        for a in filled_slots:
            if isinstance(a, dict):
                if (a.get('type') == 'LAB'
                        and a.get('day') == day
                        and a.get('batch') == batch
                        and matches_year(a.get('year'), year)
                        and matches_division(a.get('division'), division, year)):
                    return True
        return False


    def _commit_assignment(self, year, division, batch, subject, teacher, room, day, start, duration):
        for offset in range(duration):
            slot_idx = start + offset
            assignment = {
                "day": day,
                "slot": slot_idx,
                "year": year,
                "division": division,
                "batch": batch,
                "subject": subject['name'],
                "teacher": teacher,
                "room": room,
                "type": "LAB",
                "isPractical": True,
                "sessionLength": duration,
                "id": f"LAB_{year}_{division}_{day}_{start}_{batch}_{offset}"
            }
            self.state.occupy_lab_globally(room, day, slot_idx, assignment)
            self.state.assign_slot(assignment, lock=True)
            if hasattr(self.state, 'load_manager') and self.state.load_manager:
                self.state.load_manager.record_assignment(teacher, day, slot_idx)

    def _get_consecutive_windows(self, day, duration, total_slots, recess_slot):
        windows = []
        for start in range(total_slots - duration + 1):
            if recess_slot is not None and (start < recess_slot and (start + duration) > recess_slot):
                continue
            windows.append(start)
        return windows

    def _count_labs_on_day(self, year, division, day):
        try:
            from utils.time_utils import calculate_time_slots
        except ImportError:
            from backend.utils.time_utils import calculate_time_slots
        time_config = calculate_time_slots(self.branch_data)
        total_slots = time_config['total_slots']

        lab_subjects_on_day = set()
        for slot in range(total_slots):
            assignments = self.state.get_slot_assignment(day, slot, year, division)
            if not assignments:
                continue
            slot_list = assignments if isinstance(assignments, list) else [assignments]
            for a in slot_list:
                if isinstance(a, dict) and a.get('type') == 'LAB':
                    lab_subjects_on_day.add(a.get('subject', ''))
        return len(lab_subjects_on_day)

    def _get_valid_windows(self, year, division, duration=2):
        windows = []
        days = self.branch_data.get('workingDays')
        if not days or not isinstance(days, list):
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        total_slots = getattr(self.state, 'total_slots', 8)
        recess_slot = getattr(self.state, 'recess_slot', None)

        for day in days:
            valid_starts = self._get_consecutive_windows(day, duration, total_slots, recess_slot)
            for i in valid_starts:
                windows.append({'day': day, 'start_slot': i, 'duration': duration})

        def day_score(w):
            return (
                self._count_labs_on_day(year, division, w['day']),
                w['start_slot']
            )

        windows.sort(key=day_score)
        return windows

    # ------------------------------------------------------------------
    # Step 7 — Diagnostic Reporting & Lab Coverage Validator
    # ------------------------------------------------------------------

    def run_division_diagnostic(self, year, division):
        """
        Generate the detailed diagnostic report required by the prompt.
        Returns (is_ok: bool, lines: list, failure_details: list).
        """
        lines = []
        failure_details = []
        div_id = f"{year}-{division}"

        lines.append("==============================")
        lines.append(f"DIVISION: {div_id}")
        lines.append("==============================")

        num_batches = int(self.lab_batches_per_year.get(year, 3))
        batches = [f"B{b+1}" for b in range(num_batches)]

        lab_subjects = [
            s for s in self.smart_input.get('subjects', [])
            if matches_year(s.get('year'), year)
            and matches_division(s.get('division'), division, year)
            and is_lab_subject(s)
        ]

        # 1. Required Lab Subjects
        lines.append("\nRequired Lab Subjects:")
        if not lab_subjects:
            lines.append("  (None found)")
            failure_details.append(f"Curriculum Not Loaded for {div_id}: No lab subjects matched filters.")
        else:
            for s in lab_subjects:
                lines.append(f"- {s['name']}")

        # 2. Teacher Mapping
        lines.append("\nTeacher Mapping:")
        mapped_teachers_per_subject = {}
        missing_mappings = []
        for s in lab_subjects:
            sname = s['name']
            all_mapped = list(self.subject_teachers.get(sname, []))
            if hasattr(self.state, 'load_manager') and self.state.load_manager:
                lm_mapped = list(self.state.load_manager.subject_teacher_map.get(sname, []))
                for t in lm_mapped:
                    if t not in all_mapped:
                        all_mapped.append(t)

            mapped_teachers_per_subject[sname] = all_mapped
            if all_mapped:
                lines.append(f"{sname} -> {', '.join(all_mapped)}")
            else:
                lines.append(f"{sname} -> [MISSING]")
                missing_mappings.append(sname)
                failure_details.append(
                    f"Teacher Missing / Invalid Subject Mapping for '{sname}' in {div_id}:\n"
                    f"  Requested subject: {sname}\n"
                    f"  Returned mapping: []\n"
                    f"  Expected mapping: Mapped teacher in teacherSubjectMap or teacher.subjects list"
                )

        # 3. Generated Practical Variables
        lines.append("\nGenerated Practical Variables:")
        subject_status = {}
        for s in lab_subjects:
            sname = s['name']
            placed_any = any(
                self._count_lab_sessions_for_batch(year, division, sname, b) > 0
                for b in batches
            )
            if placed_any:
                lines.append(f"{sname} [OK]")
                subject_status[sname] = True
            else:
                lines.append(f"{sname} [FAIL]")
                subject_status[sname] = False
                if not mapped_teachers_per_subject.get(sname):
                    reason = "Teacher Missing"
                elif not self.labs:
                    reason = "Lab Missing"
                else:
                    reason = "Teacher Busy / Lab Busy / Placement Window Exhausted"
                failure_details.append(f"Variable Not Created for '{sname}' in {div_id}: Reason = {reason}")

        # 4. Atomic Placement Status
        lines.append("\nAtomic Placement Status:")
        batch_status = {}
        all_batches_ready = True
        for b in batches:
            b_complete = (len(lab_subjects) > 0) and all(
                self._count_lab_sessions_for_batch(year, division, s['name'], b) > 0
                for s in lab_subjects
            )
            if b_complete:
                lines.append(f"{b} Ready [OK]")
                batch_status[b] = True
            else:
                lines.append(f"{b} Ready [FAIL]")
                batch_status[b] = False
                all_batches_ready = False

        div_failed = (not lab_subjects) or (len(missing_mappings) > 0) or any(not v for v in subject_status.values()) or (not all_batches_ready)
        if div_failed:
            lines.append("\nIf any fail, print why:")
            reasons_set = set()
            if not lab_subjects:
                reasons_set.add("Curriculum Not Loaded")
            if missing_mappings:
                reasons_set.add("Teacher Missing")
                reasons_set.add("Invalid Subject Mapping")
            if any(not v for v in subject_status.values()):
                reasons_set.add("Variable Not Created")
            if not self.labs:
                reasons_set.add("Lab Missing")
            if not all_batches_ready:
                reasons_set.add("Teacher Busy or Lab Busy during placement windows")
            for r in sorted(reasons_set):
                lines.append(f"- {r}")

            avail_labs = [l['name'] if isinstance(l, dict) else str(l) for l in self.labs]
            all_teachers = [t['name'] if isinstance(t, dict) else str(t) for t in self.smart_input.get('teachers', [])]
            req_teachers = list(set(t for ts in mapped_teachers_per_subject.values() for t in ts))

            lines.append("\nDiagnostic Placement Context:")
            lines.append(f"  Required Teachers: {req_teachers}")
            lines.append(f"  Available Teachers: {all_teachers[:10]}")
            lines.append(f"  Required Labs: {[s['name'] for s in lab_subjects]}")
            lines.append(f"  Available Labs: {avail_labs}")
            lines.append(f"  Reason placement failed: Incomplete batch practical coverage.")

        lines.append("==============================")
        return not div_failed, lines, failure_details

    def _count_lab_sessions_for_batch(self, year, division, subject_name, batch):
        filled_slots = getattr(self.state, 'slots', [])
        if not filled_slots and hasattr(self.state, 'get_filled_slots'):
            filled_slots = self.state.get_filled_slots()

        for a in filled_slots:
            if isinstance(a, dict):
                if (a.get('type') == 'LAB'
                        and a.get('subject') == subject_name
                        and a.get('batch') == batch
                        and matches_year(a.get('year'), year)
                        and matches_division(a.get('division'), division, year)):
                    return 1
        return 0


    def validate_lab_coverage(self, year, division):
        num_batches = int(self.lab_batches_per_year.get(year, 3))
        batches = [f"B{b+1}" for b in range(num_batches)]

        lab_subjects = [
            s for s in self.smart_input.get('subjects', [])
            if matches_year(s.get('year'), year)
            and matches_division(s.get('division'), division, year)
            and is_lab_subject(s)
        ]

        report = {}
        all_pass = True

        for subj in lab_subjects:
            name = subj['name']
            required = 1
            batch_results = {}
            subj_pass = True

            for batch in batches:
                scheduled = self._count_lab_sessions_for_batch(year, division, name, batch)
                batch_ok = scheduled >= required
                batch_results[batch] = {'scheduled': scheduled, 'pass': batch_ok}
                if not batch_ok:
                    subj_pass = False
                    all_pass = False

            report[name] = {
                'required': required,
                'batches': batch_results,
                'subject_pass': subj_pass,
            }

        slot_schedule = {}
        try:
            from utils.time_utils import calculate_time_slots
        except ImportError:
            from backend.utils.time_utils import calculate_time_slots

        time_config = calculate_time_slots(self.branch_data)
        total_slots = time_config['total_slots']
        days = self.branch_data.get('workingDays', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])

        for day in days:
            for slot in range(total_slots):
                assignments = self.state.get_slot_assignment(day, slot, year, division)
                if not assignments:
                    continue
                slot_list = assignments if isinstance(assignments, list) else [assignments]
                lab_assignments = [a for a in slot_list if isinstance(a, dict) and a.get('type') == 'LAB']
                if not lab_assignments:
                    continue

                seen_batches_in_slot = set()
                seen_subjects_in_slot = set()
                seen_teachers_in_slot = set()
                seen_rooms_in_slot = set()

                for a in lab_assignments:
                    b = a.get('batch')
                    s = a.get('subject')
                    t = a.get('teacher')
                    r = a.get('room')
                    sess_id = a.get('id', '')

                    if sess_id.endswith('_0') or not sess_id or '_0' in sess_id:
                        if s in seen_subjects_in_slot:
                            print(f"[FAIL] VALIDATION ERROR: Subject '{s}' assigned to multiple batches in {year}-{division} on {day} slot {slot}")
                            all_pass = False
                        seen_subjects_in_slot.add(s)

                        if b in seen_batches_in_slot:
                            print(f"[FAIL] VALIDATION ERROR: Batch '{b}' has multiple assignments in {year}-{division} on {day} slot {slot}")
                            all_pass = False
                        seen_batches_in_slot.add(b)

                        if t and t != 'TBA' and t in seen_teachers_in_slot:
                            print(f"[FAIL] VALIDATION ERROR: Teacher '{t}' assigned to multiple batches in {year}-{division} on {day} slot {slot}")
                            all_pass = False
                        if t: seen_teachers_in_slot.add(t)

                        if r and r in seen_rooms_in_slot:
                            print(f"[FAIL] VALIDATION ERROR: Lab Room '{r}' assigned to multiple batches in {year}-{division} on {day} slot {slot}")
                            all_pass = False
                        if r: seen_rooms_in_slot.add(r)

                        block_key = (day, slot)
                        if block_key not in slot_schedule:
                            slot_schedule[block_key] = []
                        slot_schedule[block_key].append({'batch': b, 'subject': s, 'teacher': t, 'room': r})

        return all_pass, report, slot_schedule

    def generate_lab_coverage_report(self, year, division):
        all_pass, report, slot_schedule = self.validate_lab_coverage(year, division)

        print("\n" + "="*60)
        print(f"LAB COVERAGE & ROTATION REPORT  {year}-{division}")
        print("="*60)

        print("\n--- Practical Block Schedule & Batch Assignments ---")
        if not slot_schedule:
            print("  [WARNING] No practical blocks scheduled!")
        else:
            for block_key, items in slot_schedule.items():
                day, start_slot = block_key
                print(f"\n  {year}-{division}  {day} Slot {start_slot}")
                for item in items:
                    b = item['batch']
                    s = item['subject']
                    t = item['teacher']
                    r = item['room']
                    print(f"    {b} -> {s} -> {t} -> {r}")

        print("\n--- Subject Completion per Batch ---")
        for subj_name, data in report.items():
            req = data['required']
            s_pass = data['subject_pass']
            icon = "PASS" if s_pass else "FAIL"
            print(f"  [{icon}] {subj_name}   Required={req}/week per batch")
            for batch, bd in data['batches'].items():
                sched = bd['scheduled']
                b_icon = "ok" if bd['pass'] else "MISSING"
                print(f"      {batch}: {sched}/{req}  {b_icon}")

        print("-" * 60)
        if all_pass:
            print("  OVERALL: [OK] ALL LAB CONSTRAINTS & ROTATIONS PASSED")
        else:
            print("  OVERALL: [FAIL] LAB SCHEDULE FAILED VALIDATION")
        print("="*60 + "\n")
        return all_pass
