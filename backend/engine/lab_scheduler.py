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


class LabScheduler:
    def __init__(self, state, context):
        self.state = state
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
        
        self.labs = self.branch_data.get('sharedLabs', [])
        # Fallback if sharedLabs is empty but we are in testing
        if not self.labs and 'labs' in self.branch_data:
             self.labs = [{"name": l} for l in self.branch_data['labs']]
             
        self.lab_batches_per_year = self.branch_data.get('labBatchesPerYear', {})
        
        # Get teachers mapped to subjects
        self.subject_teachers = self._map_teachers_to_subjects()

    def _map_teachers_to_subjects(self):
        """Map subject names to available teachers."""
        mapping = {}
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
                    if s not in mapping: mapping[s] = []
                    if teacher not in mapping[s]:
                        mapping[s].append(teacher)
        
        # 2. Fallback to teacher 'subjects' list
        for teacher in teachers:
            t_name = teacher.get('name')
            t_subjects = teacher.get('subjects', [])
            if isinstance(t_subjects, str):
                t_subjects = [x.strip() for x in t_subjects.split(',')]
            for sub in t_subjects:
                if sub not in mapping: mapping[sub] = []
                if t_name not in mapping[sub]:
                    mapping[sub].append(t_name)

        return mapping

    def schedule_class_labs(self, class_info):
        """
        Schedule labs ensuring EVERY batch covers ALL lab subjects.
        """
        if not isinstance(class_info, dict):
            raise TypeError(f"Expected class_info dict, got {type(class_info)}")
            
        year = class_info.get('year')
        division = class_info.get('division')
        
        # Get batches (e.g., 3)
        num_batches = int(self.lab_batches_per_year.get(year, 3))
        batches = [f"B{b+1}" for b in range(num_batches)]
        
        # Get required lab subjects for this year (uses robust is_lab_subject)
        lab_subjects = [
            s for s in self.smart_input.get('subjects', []) 
            if s.get('year') == year 
            and (not s.get('division') or s.get('division') == division)
            and is_lab_subject(s)
        ]

        if not lab_subjects:
            print(f"  No verified lab subjects for {year}-{division}")
            return True 

        print(f"  Scheduling labs for {year}-{division} (Batches: {batches})")
        print(f"  Required Labs: {[s['name'] for s in lab_subjects]}")
        
        standard_duration = 2 
        success_count = 0
        
        for batch in batches:
            batch_index = int(batch[1:]) - 1 if batch[1:].isdigit() else 0
            rotation = batch_index % len(lab_subjects)
            subjects_to_schedule = lab_subjects[rotation:] + lab_subjects[:rotation]
            
            completed_subjects = 0
            
            for subject in subjects_to_schedule:
                duration = int(subject.get('sessionLength') or subject.get('slots') or standard_duration)
                
                if self._assign_batch_subject(year, division, batch, subject, duration):
                    completed_subjects += 1
                else:
                    print(f"    ❌ Failed to schedule {subject['name']} for {batch}")
            
            if completed_subjects == len(lab_subjects):
                success_count += 1
            else:
                print(f"  ⚠️  {batch} only completed {completed_subjects}/{len(lab_subjects)} labs")
                
        print(f"  Lab Summary for {year}-{division}: {success_count}/{num_batches} batches fully scheduled.")
        return success_count == num_batches

    def _assign_batch_subject(self, year, division, batch, subject, duration):
        """Find a valid window and assign specific lab subject to specific batch."""
        windows = self._get_valid_windows(year, division, duration)
        failure_reasons = set()
        
        # Pass 1: Strict 1-lab-per-day rule
        for window in windows:
            day = window['day']
            start_slot = window['start_slot']
            
            if not self._is_batch_free(day, start_slot, duration, year, division, batch):
                failure_reasons.add(f"Batch {batch} busy")
                continue
                
            if self._does_batch_have_lab_on_day(year, division, batch, day):
                failure_reasons.add(f"Batch {batch} already has lab on {day}")
                continue
                
            lab_room = self._find_lab_room(subject, day, start_slot, duration)
            if not lab_room:
                 failure_reasons.add("No Lab Room")
                 continue
                 
            teacher = None
            if hasattr(self.state, 'load_manager') and self.state.load_manager:
                teacher = self.state.load_manager.get_best_teacher_for_lab(
                    subject['name'], year, division, batch, day, start_slot, duration, self.state
                )
            if not teacher:
                teacher = self._pick_fallback_teacher(subject, day, start_slot, duration)

            if not teacher:
                 failure_reasons.add(f"No Teacher ({subject.get('name')})")
                 continue
            
            self._commit_assignment(year, division, batch, subject, teacher, lab_room, day, start_slot, duration)
            print(f"    Assigned {subject['name']} to {batch} on {day} slot {start_slot} (Duration: {duration})")
            return True

        # Pass 2: Relax 1-lab-per-day requirement if tight on days
        for window in windows:
            day = window['day']
            start_slot = window['start_slot']
            
            if not self._is_batch_free(day, start_slot, duration, year, division, batch):
                continue
            lab_room = self._find_lab_room(subject, day, start_slot, duration)
            if not lab_room:
                lab_room = "Lab-1"
            teacher = None
            if hasattr(self.state, 'load_manager') and self.state.load_manager:
                teacher = self.state.load_manager.get_best_teacher_for_lab(
                    subject['name'], year, division, batch, day, start_slot, duration, self.state
                )
            if not teacher:
                teacher = self._pick_fallback_teacher(subject, day, start_slot, duration)

            self._commit_assignment(year, division, batch, subject, teacher, lab_room, day, start_slot, duration)
            print(f"    Assigned (Pass 2) {subject['name']} to {batch} on {day} slot {start_slot}")
            return True
            
        print(f"    ❌ Failed to schedule {subject['name']} for {batch}. Reasons: {list(failure_reasons)[:3]}")
        return False

    def _pick_fallback_teacher(self, subject, day, start_slot, duration):
        all_teachers = self.smart_input.get('teachers', [])
        for t in all_teachers:
            t_name = t.get('name') if isinstance(t, dict) else str(t)
            if t_name and self.state.is_teacher_available(t_name, day, start_slot):
                return t_name
        return "TBA"

    def _is_batch_free(self, day, start_slot, duration, year, division, batch):
        """Check if this specific batch is free during the window."""
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
        """Check if this batch already has a lab scheduled on this day."""
        from utils.time_utils import calculate_time_slots
        time_config = calculate_time_slots(self.branch_data)
        total_slots = time_config['total_slots']
        
        for slot in range(total_slots):
             assignments = self.state.get_slot_assignment(day, slot, year, division)
             if assignments:
                 slot_assignments = assignments if isinstance(assignments, list) else [assignments]
                 for a in slot_assignments:
                     if isinstance(a, dict) and a.get('batch') == batch and a.get('type') == 'LAB':
                         return True
        return False

    def _find_lab_room(self, subject, day, start_slot, duration):
        """Find a lab room available for the entire duration."""
        for lab in self.labs:
            name = lab['name'] if isinstance(lab, dict) else str(lab)
            available = True
            for offset in range(duration):
                if not self.state.is_room_available(name, day, start_slot + offset):
                    available = False
                    break
            if available:
                return name
        if self.labs:
            first = self.labs[0]
            return first['name'] if isinstance(first, dict) else str(first)
        return "Lab-1"

    def _commit_assignment(self, year, division, batch, subject, teacher, room, day, start, duration):
        for offset in range(duration):
            assignment = {
                "day": day,
                "slot": start + offset,
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
            self.state.assign_slot(assignment, lock=True)

    def _get_consecutive_windows(self, day, duration, total_slots, recess_slot):
        """
        Return start indices for all consecutive windows of `duration`
        slots on `day` that do NOT straddle the recess boundary.
        """
        windows = []
        for start in range(total_slots - duration + 1):
            if recess_slot is not None and (start < recess_slot and (start + duration) > recess_slot):
                continue
            windows.append(start)
        return windows

    def _count_labs_on_day(self, year, division, day):
        """
        Count how many DISTINCT lab subjects are already scheduled for
        any batch of this division on this day.
        """
        from utils.time_utils import calculate_time_slots
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
        """
        Generate `duration`-slot windows that are safe to schedule a lab in.
        Uses _get_consecutive_windows() to guarantee no window straddles recess.
        """
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



    # Legacy helpers removed (assign_session, can_schedule_session) as they were cycle-based


    def _get_available_labs(self, day, slot):
        """Return list of lab objects free at this time."""
        free = []
        for lab in self.labs:
            if self.state.is_room_available(lab['name'], day, slot):
                free.append(lab)
        return free

    def _get_available_teachers(self, day, slot):
        """Return list of teacher objects free at this time."""
        all_teachers = self.smart_input.get('teachers', [])
        free = []
        for t in all_teachers:
            if self.state.is_teacher_available(t['name'], day, slot):
                free.append(t)
        return free

    def _pick_best_teacher(self, available_teachers, subject, offset):
        """Pick a teacher. Prefer subject specialist."""
        # Check explicit map
        specialists = self.subject_teachers.get(subject['name'], [])
        
        for t in available_teachers:
            if t['name'] in specialists:
                return t
        
        # Fallback: Just take the first one (or shuffled by offset to avoid bias)
        if available_teachers:
            return available_teachers[0]
        return None
