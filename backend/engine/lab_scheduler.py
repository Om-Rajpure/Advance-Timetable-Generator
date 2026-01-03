"""
Lab Scheduler

Handles the scheduling of lab sessions.
Labs are rigid constraints (consecutive slots, parallel resources) and are scheduled FIRST.
"""
import random

class LabScheduler:
    def __init__(self, state, context):
        self.state = state
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
        
        self.labs = self.branch_data.get('sharedLabs', [])
        # Fallback if sharedLabs is empty but we are in testing? (Handling test data structure)
        if not self.labs and 'labs' in self.branch_data:
             # Legacy/Test data support
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
                if sub not in mapping: mapping[sub] = []
                mapping[sub].append(teacher)
        
        # 2. Fallback to teacher 'subjects' list if map is empty/incomplete
        for teacher in teachers:
            t_name = teacher.get('name')
            t_subjects = teacher.get('subjects', [])
            for sub in t_subjects:
                if sub not in mapping: mapping[sub] = []
                if t_name not in mapping[sub]:
                    mapping[sub].append(t_name)
                    
        return mapping

    def schedule_class_labs(self, class_info):
        """
        Schedule labs ensuring EVERY batch covers ALL lab subjects.
        Algorithm: Batch-Complete (Iterate Batch -> Iterate Subjects -> Find Slot)
        """
        if not isinstance(class_info, dict):
            raise TypeError(f"Expected class_info dict, got {type(class_info)}")
            
        year = class_info.get('year')
        division = class_info.get('division')
        
        # Get batches (e.g., 3)
        num_batches = int(self.lab_batches_per_year.get(year, 3))
        batches = [f"B{b+1}" for b in range(num_batches)]
        
        # Get required lab subjects for this year
        lab_subjects = [
            s for s in self.smart_input.get('subjects', []) 
            if s.get('year') == year and (s.get('isPractical') or s.get('type') == 'Practical')
        ]
        
        if not lab_subjects:
            print(f"  No verified lab subjects for {year}-{division}")
            return True 

        print(f"  Scheduling labs for {year}-{division} (Batches: {batches})")
        print(f"  Required Labs: {[s['name'] for s in lab_subjects]}")
        
        # Standardize duration (e.g., 2 hours)
        standard_duration = 2
        
        # Scheduling Loop
        success_count = 0
        
        for batch in batches:
            # Each batch must do ALL subjects exactly once per week
            # We shuffle subjects to reduce collision probability with other batches
            # (e.g. Batch A does S1 first, Batch B does S2 first)
            
            # Simple offset rotation based on batch index to align parallel sessions better
            batch_index = int(batch[1:]) - 1 # 'B1' -> 0
            
            # Create a rotated copy of subjects for this batch preference
            # If subjects are [L1, L2, L3]
            # B1 (idx 0) prefers order [L1, L2, L3]
            # B2 (idx 1) prefers order [L2, L3, L1]
            rotation = batch_index % len(lab_subjects)
            subjects_to_schedule = lab_subjects[rotation:] + lab_subjects[:rotation]
            
            completed_subjects = 0
            
            for subject in subjects_to_schedule:
                # Find a slot for this (Batch + Subject)
                if self._assign_batch_subject(year, division, batch, subject, standard_duration):
                    completed_subjects += 1
                else:
                    print(f"    ❌ Failed to schedule {subject['name']} for {batch}")
            
                
            if completed_subjects == len(lab_subjects):
                success_count += 1
            else:
                print(f"  ⚠️  {batch} only completed {completed_subjects}/{len(lab_subjects)} labs")
                # User Requirement: Each batch must get ALL lab subjects.
                # If we fail here, we should probably flag it strongly.
                pass
                
        # STRICT VALIDATION: Check if we actually scheduled anything
        total_labs_placed = success_count * len(lab_subjects) 
        print(f"  📊 Lab Summary for {year}-{division}: {success_count}/{num_batches} batches fully scheduled.")
        
        # If any batch failed to get ALL labs, we should technically consider this a partial failure.
        # But we don't want to crash unless count is 0.
        
        if success_count == 0 and len(lab_subjects) > 0:
            print("  ❌ CRITICAL: No batches completed their lab requirements!")
            raise RuntimeError(f"Lab scheduling failed. No batches could be scheduled for {len(lab_subjects)} required labs. Check Room/Teacher availability. Debug logs above.")
            
        return success_count == num_batches

    def _assign_batch_subject(self, year, division, batch, subject, duration):
        """Find a valid window and assign specific lab subject to specific batch."""
        
        windows = self._get_valid_windows(year, division, duration)
        
        failure_reasons = set()
        
        for window in windows:
            day = window['day']
            start_slot = window['start_slot']
            
            # 1. Check if Batch is free
            if not self._is_batch_free(day, start_slot, duration, year, division, batch):
                failure_reasons.add(f"Batch {batch} busy")
                continue
                
            # 2. Check Lab Room Availability
            lab_room = self._find_lab_room(subject, day, start_slot, duration)
            if not lab_room:
                 failure_reasons.add("No Lab Room")
                 continue
                 
            # 3. Check Teacher Availability
            teacher = self._find_teacher(subject, day, start_slot, duration)
            if not teacher:
                 failure_reasons.add(f"No Teacher ({subject.get('name')})")
                 continue
            
            # 4. ASSIGN
            self._commit_assignment(year, division, batch, subject, teacher, lab_room, day, start_slot, duration)
            print(f"    ✅ Assigned {subject['name']} to {batch} on {day} slot {start_slot}")
            return True
            
        # Log failure details if not assigned
        print(f"    ❌ Failed to schedule {subject['name']} for {batch}. Reasons: {list(failure_reasons)[:3]}")
        return False

    def _is_batch_free(self, day, start_slot, duration, year, division, batch):
        """Check if this specific batch is free during the window."""
        for offset in range(duration):
            slot_idx = start_slot + offset
            
            # Access underlying grid directly or through helper if it existed
            # Grid stores: list of assignments at (d, s, y, div)
            assignments = self.state.get_slot_assignment(day, slot_idx, year, division)
            
            if assignments:
                # IMPORTANT: Parallel Batch Logic
                # We are checking if 'batch' is free.
                # A slot is BLOCKED for 'batch' ONLY if:
                # 1. 'batch' is already assigned here.
                # 2. The slot is a WHOLE CLASS session (THEORY) which blocks everyone.
                
                # Check list of assignments in this slot
                slot_assignments = assignments if isinstance(assignments, list) else [assignments]
                
                for a in slot_assignments:
                    # Case 1: Same batch already occupied
                    if a.get('batch') == batch:
                        return False
                        
                    # Case 2: Theory class occupies the whole division (all batches blocked)
                    if a.get('type') == 'THEORY':
                        return False
                        
                    # Case 3: Another batch is here (e.g., 'B2' is here, we are 'B1')
                    # This is ALLOWED for Labs. We continue checking other assignments.
            
            # If we pass all checks, the slot is free for THIS batch
            # (even if other batches are present)
        return True

    def _find_lab_room(self, subject, day, start_slot, duration):
        """Find a lab room available for the entire duration."""
        # Prefer mapped room if any logic exists (not currently detailed)
        # Iterate all shared labs
        
        for lab in self.labs:
            name = lab['name']
            available = True
            for offset in range(duration):
                if not self.state.is_room_available(name, day, start_slot + offset):
                    available = False
                    break
            
            if available:
                return name # Return first available
        return None

    def _find_teacher(self, subject, day, start_slot, duration):
        """Find a teacher available for entire duration."""
        # Use existing map logic
        mapped_teachers = self.subject_teachers.get(subject['name'], [])
        
        # Try mapped teachers first
        for t_name in mapped_teachers:
            available = True
            for offset in range(duration):
                if not self.state.is_teacher_available(t_name, day, start_slot + offset):
                    available = False
                    break
            if available:
                return t_name
                
        # Fallback? Strict mode says we might fail. 
        # But let's try ANY teacher if none mapped (unless strict subject specialist required)
        # For labs, usually strict.
        return None

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
                "id": f"LAB_{year}_{division}_{day}_{start}_{batch}_{offset}"
            }
            # Lock ensures Theory doesn't overwrite it later
            self.state.assign_slot(assignment, lock=True)

    def _get_valid_windows(self, year, division, duration=2):
        """
        Generate `duration`-slot windows.
        Prioritize early slots to allow Theory to fill later slots?
        Actually Labs often are afternoon. But let's keep standard generation.
        """
        windows = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # Determine slots
        from utils.time_utils import calculate_time_slots
        time_config = calculate_time_slots(self.branch_data)
        slots = time_config['total_slots']
        recess_slot = time_config['recess_slot']
        
        # Randomize days to distribute?
        # random.shuffle(days) 
        
        for day in days:
            # Simple slide
            for i in range(1, slots - duration + 2):
                # Check recess
                indices = range(i, i + duration)
                if recess_slot is not None and recess_slot in indices:
                    continue
                
                windows.append({'day': day, 'start_slot': i, 'duration': duration})
                
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
        return available_teachers[0]
