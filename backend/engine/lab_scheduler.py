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
        Schedule labs for a specific Class Object.
        Returns True if successful, False otherwise.
        """
        if not isinstance(class_info, dict):
            raise TypeError(f"Expected class_info dict, got {type(class_info)}")
            
        year = class_info.get('year')
        division = class_info.get('division')
        num_batches = int(self.lab_batches_per_year.get(year, 3))
        
        # Identify lab sessions needed
        lab_sessions_to_schedule = []
        
        unique_lab_subjects = [
            s for s in self.smart_input.get('subjects', []) 
            if s.get('year') == year and (s.get('isPractical') or s.get('type') == 'Practical')
        ]
        
        if not unique_lab_subjects:
            print(f"  No verified lab subjects for {year}-{division}")
            return True # Nothing to schedule is a success
            
        # Standardize duration
        standard_duration = 2
        if unique_lab_subjects:
             standard_duration = int(unique_lab_subjects[0].get('sessionLength', 2))
             if standard_duration <= 0: standard_duration = 2
        
        # Max sessions needed (Cycles)
        max_sessions_needed = 0
        for s in unique_lab_subjects:
            weekly_slots = int(s.get('lecturesPerWeek', 2))
            duration = int(s.get('sessionLength', 2))
            if duration <= 0: duration = 2
            needed = max(1, weekly_slots // duration)
            if needed > max_sessions_needed: max_sessions_needed = needed

        windows = self._get_valid_windows(year, division, duration=standard_duration)
        
        # Loop cycles
        for cycle in range(max_sessions_needed):
            # For each cycle, we rotate the subjects for batches
            # Actually, simply placing a session rotates the batches internally in _assign_session
            # But wait, _assign_session assigns ALL batches at once for that window.
            # So we just need to schedule 'cycle' number of windows.
            # HOWEVER: Different batches do DIFFERENT subjects in parallel.
            # So 1 Window = 1 Session for ALL batches (where B1 does S1, B2 does S2...).
            
            # The rotation logic inside _assign_session (lines 276-279) handles "B1 gets S1, B2 gets S2".
            # Does the next window handle "B1 gets S2, B2 gets S3"?
            # _assign_session takes `session_index`.
            # We must vary `session_index` across windows/cycles to ensure rotation.
            
            # session_index should increment per cycle.
             
            session_index = cycle
             
            placed = False
            for window in windows:
                 # Check overlap with previous assignments (windows list is static?? No, _can_schedule checks state)
                 if self._can_schedule_session(window, num_batches, unique_lab_subjects, year, division):
                     if self._assign_session(window, num_batches, unique_lab_subjects, year, division, session_index):
                         placed = True
                         # Remove used window from candidates to avoid re-checking? 
                         # Ideally _can_schedule handles it, but optimization:
                         windows.remove(window) 
                         break
             
            if not placed:
                 print(f"Failed to place Lab Session Cycle {cycle} for {year}-{division}")
                 # For academic engine, we might want to continue even if one fails?
                 # But User said "Labs must occupy required count".
                 return False

        return True

    def _get_valid_windows(self, year, division, duration=2):
        """
        Generate `duration`-slot windows.
        Prioritize: Before Recess, End of Day.
        Excluding Recess crossover.
        """
        windows = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # Get slot info from state (calculated in generate_slot_grid)
        # Assuming generate_slot_grid has been called or we recalculate.
        # Ideally state initializes this.
        if hasattr(self.state, 'recess_slot'):
             recess_slot = self.state.recess_slot
             # How many slots total?
             # State uses time_utils but doesn't store total_slots publicly except implicitly.
             # Let's use time_utils here too to be safe.
             from utils.time_utils import calculate_time_slots
             time_config = calculate_time_slots(self.branch_data)
             slots = time_config['total_slots']
             recess_slot = time_config['recess_slot']
        else:
             # Fallback
             from utils.time_utils import calculate_time_slots
             time_config = calculate_time_slots(self.branch_data)
             slots = time_config['total_slots']
             recess_slot = time_config['recess_slot']
        
        # Candidate windows: (day, start_slot)
        for day in days:
            # Check all i to i + duration
            # Standardize to 1-based indexing to match Theory Scheduler
            # Slots 1 to N.
            # Valid start slots: 1 to (Total - Duration + 1)
            for i in range(1, slots - duration + 2):
                # CHECK RECESS OVERLAP
                # Window covers slots [i, i+1, ..., i+duration-1]
                window_indices = range(i, i + duration)
                
                hits_recess = False
                if recess_slot is not None:
                     if recess_slot in window_indices:
                         hits_recess = True
                
                if hits_recess:
                     continue
                
                windows.append({'day': day, 'start_slot': i, 'duration': duration})
                
        return windows

    def _can_schedule_session(self, window, num_batches, lab_subjects, year, division):
        """Check if resources (Rooms, Teachers) are available for N sub-batches."""
        day = window['day']
        start_slot = window['start_slot']
        duration = window.get('duration', 2)
        
        # 1. Check if slots are free for this division
        for offset in range(duration):
            if not self.state.is_slot_free(day, start_slot + offset, year, division): return False
        
        # 2. Check Lab Rooms (must be available for ALL slots in duration)
        # Intersection of availability across all slots
        common_labs = None
        for offset in range(duration):
            available = self._get_available_labs(day, start_slot + offset)
            if common_labs is None:
                common_labs = available
            else:
                # Intersection
                # Need to match by name or ID? They are dicts.
                # Assuming objects are consistent or we filter by name.
                # Better to filter by name.
                current_names = set(l['name'] for l in available)
                common_labs = [l for l in common_labs if l['name'] in current_names]
        
        if len(common_labs) < num_batches:
            return False
            
        # 3. Check Teachers
        common_teachers = None
        for offset in range(duration):
            available = self._get_available_teachers(day, start_slot + offset)
            if common_teachers is None:
                common_teachers = available
            else:
                current_names = set(t['name'] for t in available)
                common_teachers = [t for t in common_teachers if t['name'] in current_names]
        
        if len(common_teachers) < num_batches:
            return False
            
        return True

    def _assign_session(self, window, num_batches, lab_subjects, year, division, session_index):
        """Assign the session and lock resources."""
        day = window['day']
        start = window['start_slot']
        duration = window.get('duration', 2)
        
        # Get Resources again (Re-calculate intersection)
        common_labs = None
        for offset in range(duration):
            available = self._get_available_labs(day, start + offset)
            if common_labs is None: common_labs = available
            else:
                current_names = set(l['name'] for l in available)
                common_labs = [l for l in common_labs if l['name'] in current_names]
                
        common_teachers = None
        for offset in range(duration):
            available = self._get_available_teachers(day, start + offset)
            if common_teachers is None: common_teachers = available
            else:
                current_names = set(t['name'] for t in available)
                common_teachers = [t for t in common_teachers if t['name'] in current_names]
        
        # Safety
        if len(common_labs) < num_batches or len(common_teachers) < num_batches:
            return False
        
        # Determine specific subject for each batch using rotation
        # BATCHES: 0 to num_batches-1
        
        # To avoid index errors if num_batches > len(lab_subjects), use modulo
        
        for b in range(num_batches):
            # ROTATION: 
            sub_idx = (session_index + b) % len(lab_subjects)
            subject = lab_subjects[sub_idx]
            
            lab = common_labs[b]
            
            # Pick teacher
            teacher = self._pick_best_teacher(common_teachers, subject, b)
            if teacher in common_teachers:
                common_teachers.remove(teacher)
            
            # Create assignment for ALL slots in duration
            for slot_offset in range(duration):
                assignment = {
                    "day": day,
                    "slot": start + slot_offset,
                    "year": year,
                    "division": division,
                    "batch": f"B{b+1}",
                    "subject": subject['name'],
                    "teacher": teacher['name'],
                    "room": lab['name'],
                    "type": "LAB",
                    "isPractical": True,
                    "id": f"LAB_{year}_{division}_{day}_{start}_{b}_{slot_offset}"
                }
                self.state.assign_slot(assignment, lock=True)
                
        return True

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
