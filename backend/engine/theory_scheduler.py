"""
Theory Scheduler Component

Handles scheduling of theory lectures with load balancing and constraint checking.
"""

from typing import List, Dict, Optional
import random

class TheoryScheduler:
    def __init__(self, state_manager, context):
        self.state = state_manager
        self.context = context
        self.max_daily_lectures = 7  # Configurable?
        
    def schedule_theory(self, class_info) -> bool:
        """
        Schedule theory lectures for a specific class (Year-Div).
        """
        if not isinstance(class_info, dict):
            raise TypeError(f"Expected class_info dict, got {type(class_info)}")
            
        year = class_info.get('year')
        division = class_info.get('division')
        
        print(f"  > Scheduling Theory for {year}-{division}...")
        
        # 1. Get Theory Subjects for this class
        subjects = self._get_class_subjects(year)
        theory_subjects = [s for s in subjects if not s.get('isPractical', False) and s.get('type') != 'Practical']
        
        print(f"    found {len(subjects)} subjects for year '{year}', {len(theory_subjects)} are Theory.")
        if not theory_subjects:
            print(f"    ⚠️ No Theory subjects found for {year}-{division}. Check 'year' field in subjects CSV.")

        # 2. Sort subjects by difficulty (more lectures/constraints -> first)
        theory_subjects.sort(key=lambda s: int(s.get('weeklyLectures', 3)), reverse=True)
        
        # 3. Schedule each subject
        for subject in theory_subjects:
            lectures_needed = int(subject.get('weeklyLectures', 3))
            subject_name = subject.get('name')
            teacher_name = self._get_teacher_for_subject(subject_name, division)
            
            assignments_count = 0
            
            # Try to spread across different days first
            days_tried = set()
            
            while assignments_count < lectures_needed:
                # Pick best day (lowest load for class & teacher)
                best_day = self._pick_best_day(year, division, teacher_name, days_tried)
                
                if not best_day:
                    print(f"    ! Could not find valid day for {subject_name} ({assignments_count}/{lectures_needed})")
                    break # Cannot schedule more for this subject efficiently
                
                days_tried.add(best_day)
                
                # Try to find a slot on this day
                slot_assigned = self._assign_slot_on_day(year, division, best_day, subject_name, teacher_name)
                
                if slot_assigned:
                    assignments_count += 1
                else:
                    # If we couldn't fit on this day, we might loop and try another day
                    # But if we run out of days, we might fail or settle for uneven distribution
                    pass
            
            if assignments_count < lectures_needed:
                print(f"    ! CAUTION: Only scheduled {assignments_count}/{lectures_needed} for {subject_name}")

        return True

    def _get_class_subjects(self, year: str) -> List[Dict]:
        all_subjects = self.context.get('smartInputData', {}).get('subjects', [])
        return [s for s in all_subjects if s.get('year') == year]

    def _get_teacher_for_subject(self, subject: str, division: str) -> str:
        # Check mapping
        mappings = self.context.get('smartInputData', {}).get('teacherSubjectMap', [])
        # Strict mapping logic: Subject + Division specific? 
        # Typically mapping is Subject -> Teacher. For now assuming simple mapping.
        # Ideally we'd pass Division to mapping if data supported it.
        for m in mappings:
            if m.get('subjectName') == subject:
                return m.get('teacherName')
        return "TBA"

    def _pick_best_day(self, year, division, teacher, excluded_days):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        candidates = [d for d in days if d not in excluded_days]
        
        # Score days: Lower score = Better
        # Score = (Class Load) + (Teacher Load)
        best_day = None
        min_score = float('inf')
        
        for day in candidates:
            class_load = self.state.get_daily_load_for_class(year, division, day)
            teacher_load = self.state.get_daily_load_for_teacher(teacher, day)
            
            # Constraints
            if class_load >= self.max_daily_lectures: continue
            if teacher_load >= 4: continue # Max 4 lectures per day per teacher
            
            score = class_load + teacher_load
            if score < min_score:
                min_score = score
                best_day = day
                
        return best_day

    def _assign_slot_on_day(self, year, division, day, subject, teacher):
        # Determine available slots
        total_slots = int(self.context.get('branchData', {}).get('slotsPerDay', 8))
        
        # Randomize start order to minimize collisions
        slots = list(range(1, total_slots + 1)) 
        
        for slot_idx in slots:
            # Check Global State (Class Free)
            if self.state.is_slot_free(day, slot_idx, year, division):
                # Check Teacher Availability
                if self.state.is_teacher_available(teacher, day, slot_idx):
                    
                    # DYNAMIC ROOM ALLOCATION
                    assigned_room = self._find_available_room(year, division, day, slot_idx)
                    
                    if not assigned_room:
                         # No room available! Cannot schedule here.
                         continue

                    # ASSIGN
                    assignment = {
                        'year': year,
                        'division': division,
                        'day': day,
                        'slot': slot_idx,
                        'subject': subject,
                        'teacher': teacher,
                        'type': 'THEORY',
                        'room': assigned_room # Assigned dynamically!
                    }
                    
                    self.state.assign_slot(assignment)
                    return True
                    
        return False

    def _find_available_room(self, year, division, day, slot_index):
        """
        Find an available room with fallback strategy:
        1. Home Room (Preferred)
        2. Global Pool (Fallback)
        """
        branch_data = self.context.get('branchData', {})
        all_classrooms = branch_data.get('classrooms', {})
        
        # 1. Identify Home Room (Replicating scheduler.py logic)
        home_room = None
        
        rooms_for_year = []
        if isinstance(all_classrooms, dict):
            rooms_for_year = all_classrooms.get(year, [])
        elif isinstance(all_classrooms, list):
            # Legacy/Dummy
            rooms_for_year = [r.get('name') for r in all_classrooms if isinstance(r, dict)]
            
        if isinstance(rooms_for_year, list) and len(rooms_for_year) > 0:
            div_idx = 0
            if len(division) == 1 and 'A' <= division <= 'Z':
                div_idx = ord(division) - ord('A')
            room_idx = div_idx % len(rooms_for_year)
            home_room = rooms_for_year[room_idx]
            
        # 2. Check Home Room
        if home_room and self.state.is_room_available(home_room, day, slot_index):
            return home_room
            
        # 3. Fallback: Search ALL rooms
        # Flatten all rooms
        all_rooms_list = []
        if isinstance(all_classrooms, dict):
            for y_rooms in all_classrooms.values():
                if isinstance(y_rooms, list):
                    for r in y_rooms:
                        if isinstance(r, dict): all_rooms_list.append(r.get('name'))
                        elif isinstance(r, str): all_rooms_list.append(r)
        elif isinstance(all_classrooms, list):
             for r in all_classrooms:
                 if isinstance(r, dict): all_rooms_list.append(r.get('name'))
                 elif isinstance(r, str): all_rooms_list.append(r)
             
        if not all_rooms_list:
             pass 
             # print("DEBUG: Room Search - No rooms found in branchData['classrooms']!", flush=True)

        # Scramble for fairness? Or just First Fit? First Fit is fine for "emergency"
        for room in all_rooms_list:
            if not room: continue 
            available = self.state.is_room_available(room, day, slot_index)
            if available:
                return room
                
        # 4. Fail
        return None
