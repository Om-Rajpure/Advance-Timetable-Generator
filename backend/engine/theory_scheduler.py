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
        subjects = self._get_class_subjects(year, division)
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
            print(f"ALLOCATING THEORY: {subject_name} | {year}-{division} | Needed: {lectures_needed}")
            self.current_subject = subject_name
            
            teacher_name = self._get_teacher_for_subject(subject_name, division, year=year)
            
            assignments_count = 0
            
            # TRACKING DISTRIBUTION
            if not hasattr(self, 'theory_count'):
                self.theory_count = {d: 0 for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']}
            if not hasattr(self, 'subject_day_usage'):
                # Map: subject_name -> set(days)
                self.subject_day_usage = {}

            # Ensure subject entry exists
            if subject_name not in self.subject_day_usage:
                self.subject_day_usage[subject_name] = set()
            
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
                slot_assigned = self._assign_slot_on_day(year, division, best_day, subject_name, teacher_name, assignments_count)
                
                if slot_assigned:
                    assignments_count += 1
                    # UPDATE TRACKING
                    self.theory_count[best_day] += 1
                    self.subject_day_usage[subject_name].add(best_day)
                else: 
                    # If we couldn't fit on this day, we might loop and try another day
                    # But if we run out of days, we might fail or settle for uneven distribution
                    pass
            
            if assignments_count == 0:
                 # TASK 4: STOP SILENT FAILURES
                 # If we scheduled NOTHING for a subject, we must fail.
                 error_msg = f"CRITICAL: Could not schedule ANY lectures for {subject_name} (Teacher: {teacher_name}). Constraints too strict?"
                 print(f"    ❌ {error_msg}")
                 raise Exception(error_msg)
            
            if assignments_count < lectures_needed:
                print(f"    ! CAUTION: Only scheduled {assignments_count}/{lectures_needed} for {subject_name}")

                print(f"    ! CAUTION: Only scheduled {assignments_count}/{lectures_needed} for {subject_name}")

        # 4. POST-PROCESS BALANCING
        self._balance_theory_distribution(year, division)

        return True

    def _get_class_subjects(self, year: str, division: str = None) -> List[Dict]:
        all_subjects = self.context.get('smartInputData', {}).get('subjects', [])
        return [
            s for s in all_subjects 
            if s.get('year') == year 
            and (not s.get('division') or s.get('division') == division)
        ]

    def _get_teacher_for_subject(self, subject: str, division: str, year: str = None) -> str:
        # DELEGATE TO LOAD MANAGER
        if hasattr(self.state, 'load_manager') and self.state.load_manager:
            return self.state.load_manager.get_or_select_theory_teacher(subject, year, division)
        
        # Fallback (Legacy) if no manager
        mappings = self.context.get('smartInputData', {}).get('teacherSubjectMap', [])
        for m in mappings:
            if m.get('subjectName') == subject:
                return m.get('teacherName')
        return "TBA"

    def _pick_best_day(self, year, division, teacher, excluded_days) -> Optional[str]:
        # Get configured working days or default to full week
        cfg_days = self.context.get('branchData', {}).get('workingDays')
        if not cfg_days or not isinstance(cfg_days, list):
            cfg_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
        candidates = [d for d in cfg_days if d not in excluded_days]
        
        best_day = None
        min_score = float('inf')
        
        # Determine subject name from context? 
        # _pick_best_day signature in original didn't have subject.
        # But wait, I call it as: self._pick_best_day(year, division, teacher_name, days_tried)
        # I need 'subject_name' to check 'subject_day_usage'.
        # I MUST update the signature in a separate edit or rely on 'days_tried' which partly handles it?
        # NO, 'days_tried' is for retry loop. 
        # 'subject_day_usage' is for "don't put subject twice on same day".
        # Current logic: If I already put subject on Monday, Monday should be in 'subject_day_usage[sub]'.
        # The retry loop uses 'days_tried' to avoid re-picking the *same failed day*.
        # But for *allocation*, I should filter out days where subject is ALREADY assigned.
        
        # Wait, I cannot change signature easily without changing call site which I did not in previous chunk?
        # Actually I didn't change the call site signature in previous chunk. 
        # I should have.
        # Let's see if I can access subject from somewhere? No.
        # BUT: I can rely on `subject_day_usage` if I knew the subject.
        # FIX: I will get subject from `self.subject_day_usage` if I assume single-threaded subject processing loop?
        # No, that's risky.
        # Let's assume I missed updating the call site in previous chunk.
        # I will fix call site and signature here together? 
        # MultiReplace allows multiple chunks.
        # Let's fix the call site in Chunk 1 logic if possible? 
        # Chunk 1 was purely setup.
        # I will update `schedule_theory` again in a follow-up or try to do it right now?
        # I'll stick to modifying `_pick_best_day` to accept subject OR 
        # use a member variable `self.current_subject` which I set in the loop?
        # Setting `self.current_subject` in the loop is cleaner for minimal diff.
        
        # Let's use `current_subject` approach to avoid signature refactor hell.
        subject_name = getattr(self, 'current_subject', None)
        
        for day in candidates:
            # CONSTRAINT 1: Max 1 lecture per subject per day
            if subject_name and day in self.subject_day_usage.get(subject_name, set()):
                continue # Skip this day, subject already present
            
            # Base Load (Theory Only)
            theory_load = self.theory_count.get(day, 0)
            
            # Total Class Load (includes Labs)
            # We still want to respect total limits
            total_load = self.state.get_daily_load_for_class(year, division, day)
            if total_load >= self.max_daily_lectures: continue
            
            # Teacher Load
            teacher_load = self.state.get_daily_load_for_teacher(teacher, day)
            if teacher_load >= 4: continue
            
            # SCORING
            # 1. Balanced Theory Dist (Primary)
            score = theory_load * 10 
            
            # 2. Avoid Consecutive Days (Secondary)
            if subject_name:
                used_days = self.subject_day_usage.get(subject_name, set())
                # specific consecutive day check
                all_days = self.context.get('branchData', {}).get('workingDays', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
                if day in all_days:
                    idx = all_days.index(day)
                    if idx > 0 and all_days[idx-1] in used_days:
                        score += 50 # Dislike consecutive
                    if idx < len(all_days)-1 and all_days[idx+1] in used_days:
                        score += 50
                    
            # 3. Saturday Lighter (Tertiary)
            if day == 'Saturday':
                # We want Saturday to be chosen LAST if loads are equal
                score += 5
                
            if score < min_score:
                min_score = score
                best_day = day
                
        return best_day

    def _assign_slot_on_day(self, year, division, day, subject, teacher, assignment_idx=0):
        # Determine available slots
        # Validate Recess
        try:
            from utils.time_utils import calculate_time_slots
            time_config = calculate_time_slots(self.context.get('branchData', {}))
            recess_slot = time_config.get('recess_slot')
            total_slots = time_config.get('total_slots', 8)
        except:
            total_slots = int(self.context.get('branchData', {}).get('slotsPerDay', 8))
            recess_slot = None

        # Randomize start order to minimize collisions
        # FIX: Use 0-based indexing to match StateManager and TimeUtils
        slots = list(range(total_slots)) 
        
        for slot_idx in slots:
            # SKIP RECESS (Task 2)
            if recess_slot is not None and slot_idx == recess_slot:
                continue

            # Check Global State (Class Free)
            if self.state.is_slot_free(day, slot_idx, year, division):
                
                # Check Teacher Availability
                is_avail = self.state.is_teacher_available(teacher, day, slot_idx)
                
                # TASK 6: TEMPORARY DEBUG LO (Log strictly for one subject/teacher to avoid spam)
                if assignment_idx == 0 and "Mrs. S. R. Katke" in teacher: 
                     # Re-verify why it failed
                     meta = self.state.teacher_metadata.get(teacher, {})
                     print(f"    DEBUG: {teacher} @ {day} Slot {slot_idx}")
                     print(f"      Login: {meta.get('loginTime')}, Window: {meta.get('workingHours')}h")
                     print(f"      Available? {is_avail}")

                # TASK 3: Relax Constraint for First Assignment
                if not is_avail and assignment_idx == 0:
                     # Check if it's a hard conflict (assigned elsewhere) or just Window
                     # If teacher is assigned elsewhere, we CANNOT override (hard conflict).
                     assigned_elsewhere = False
                     if (teacher, day, slot_idx) in self.state.teacher_assignments:
                         assigned_elsewhere = True
                     
                     if not assigned_elsewhere:
                         print(f"    DEBUG OVERRIDE: Forcing Slot {slot_idx} for {subject} despite Window constraint (First Placement).")
                         is_avail = True # Force Allow
                
                if not is_avail:
                     # print(f"DEBUG: {teacher} unavailable at {day} slot {slot_idx}")
                     pass
                     
                if is_avail:
                    
                    # DYNAMIC ROOM ALLOCATION
                    assigned_room = self._find_available_room(year, division, day, slot_idx)
                    
                    if not assigned_room:
                         # No room available! Cannot schedule here.
                         pass
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
        Find an available room from the Global Branch Pool.
        """
        branch_data = self.context.get('branchData', {})
        all_classrooms = branch_data.get('classrooms', [])
        
        # Normalize to list if strict dict (legacy) was somehow passed
        if isinstance(all_classrooms, dict):
            # Fallback for Mixed/Legacy Data: Flatten values
            temp_list = []
            for r_list in all_classrooms.values():
                if isinstance(r_list, list): temp_list.extend(r_list)
            all_classrooms = list(set(temp_list)) # dedupe
            
        if not all_classrooms:
            # Fallback to 'rooms' key if 'classrooms' is empty/missing
            all_classrooms = branch_data.get('rooms', [])
            
        if not all_classrooms:
             # CRITICAL FALLBACK: If no rooms defined, create virtual pool to allow generation
             print(f"DEBUG: No classrooms defined. Using Virtual Room Pool 1-20.")
             all_classrooms = [f"Virtual-Room-{i}" for i in range(1, 21)]
            
        # Iterate and Find First Free
        # DEBUG: Print room count check once per class generation (to avoid spam, maybe logic needed?)
        # For now, just print if empty
        if not all_classrooms:
             print(f"DEBUG: No classrooms found in branchData for {year}-{division}!")
             
        for room in all_classrooms:
            room_name = room.get('name') if isinstance(room, dict) else room
            
            if self.state.is_room_available(room_name, day, slot_index):
                return room_name
            # else:
            #     # DEBUG: Room occupied
            #     pass
                
    def _balance_theory_distribution(self, year, division):
        """
        Post-Process: Attempts to move theory slots from Heavy Days to Light Days.
        Constraints:
        1. Target day load < Heavy day load - 1
        2. Target day must not already have this subject
        3. Teacher must be free on target day/slot
        4. Room must be free on target day/slot
        """
        print(f"  > Balancing Theory Load for {year}-{division}...")
        
        # Calculate load per day (Theory Only)
        # Re-scan state because self.theory_count might be slightly off if we did other things?
        # Better to rely on self.theory_count if we trust it, or scan grid.
        # Let's scan simple grid for accuracy.
        branch_data = self.context.get('branchData', {})
        days = branch_data.get('workingDays')
        if not days or not isinstance(days, list):
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
        # Try balancing Max 5 times
        for pass_idx in range(5):
            # Recalculate loads
            loads = {day: 0 for day in days}
            theory_slots_map = {day: [] for day in days} # store (slot_idx, assignment)
            
            # Scan current assignments
            # Note: We don't have direct access to 'grid' here easily without scanning state.slots
            # But state.slot_grid uses canonical keys? No, keys are (year, div, day, slot) in dict?
            # StateManager uses 'slot_grid' keyed by unique string or tuple?
            # Let's check state_manager.py... assign_slot uses keys like f"{year}_{div}_{day}_{slot}"
            # It's expensive to reverse scan.
            # Use `valide_slots` from `self.theory_count`? No, that's just counts.
            
            # Let's assume `self.theory_count` is accurate enough OR reconstruct it?
            # We need actual slot objects to move them.
            # We can use `self.state.get_day_assignments(year, division, day)` if it exists.
            # It doesn't.
            
            # FAST SCAN: Iterate all slots for this class
            # Assuming max 8 slots * 6 days = 48 checks. Very fast.
            # We need finding Theory Slots.
            
            import utils.time_utils
            # We need max slots
            total_slots = 8 # Default
            try:
                tc = utils.time_utils.calculate_time_slots(branch_data)
                total_slots = tc.get('total_slots', 8)
                recess_slot = tc.get('recess_slot', -1)
            except:
                pass
                
            for d in days:
                for s in range(total_slots):
                     cell = self.state.get_slot_assignment(year, division, d, s)
                     if cell and isinstance(cell, dict) and cell.get('type') == 'THEORY':
                         loads[d] += 1
                         theory_slots_map[d].append(cell)
                     elif isinstance(cell, list):
                         # Should not prevent list of theory? Usually Lab list.
                         # If multiple theory?? No, theory is single.
                         pass

            # Find Max and Min Load (excluding Saturday if desired, or treat Saturday as lighter target?)
            # Prompt says "Saturday should be lighter".
            # So we treat Saturday as 'Normal' for being a SOURCE of moves? 
            # Or receiving?
            # Let's exclude Saturday from being a "Min" target if it's already > 2?
            # Simple Logic: Max Load Day -> Min Load Day.
            
            sorted_days = sorted(days, key=lambda d: loads[d])
            min_day = sorted_days[0]
            max_day = sorted_days[-1]
            
            diff = loads[max_day] - loads[min_day]
            if diff <= 1:
                print("    > Load Balanced. Stopping.")
                return # Balanced enough
            
            print(f"    Pass {pass_idx+1}: Attempting move from {max_day}({loads[max_day]}) to {min_day}({loads[min_day]})")
            
            moved = False
            # Try to find a moveable slot from max_day
            # Shuffle slots to avoid deterministic stuck
            candidates = theory_slots_map[max_day]
            random.shuffle(candidates)
            
            for slot_data in candidates:
                subj = slot_data['subject']
                teacher = slot_data['teacher']
                current_slot_idx = slot_data['slot']
                
                # Validation Target Day:
                # 1. Subject constraint: Min Day must NOT have this subject
                # We can check existing slots in min_day
                existing_subjects_in_min = set(s['subject'] for s in theory_slots_map[min_day])
                if subj in existing_subjects_in_min:
                    continue # Subject already exists on target day
                
                # 2. Find FREE slot in Min Day
                target_slot = -1
                for ts in range(total_slots):
                    # Skip recess
                    # if ts == recess_slot: continue 
                    # State check handles validation usually?
                    
                    if self.state.is_slot_free(min_day, ts, year, division):
                        if self.state.is_teacher_available(teacher, min_day, ts):
                            target_slot = ts
                            break
                
                if target_slot != -1:
                    # EXECUTE SWAP (Move)
                    # 1. Remove from old
                    self.state.remove_slot(year, division, max_day, current_slot_idx)
                    # 2. Add to new
                    new_assign = slot_data.copy()
                    new_assign['day'] = min_day
                    new_assign['slot'] = target_slot
                    # Room? Re-find dynamic room or keep old?
                    # Old room might be occupied on new day.
                    # Best to re-find room.
                    new_room = self._find_available_room(year, division, min_day, target_slot)
                    if new_room:
                         new_assign['room'] = new_room
                    else:
                         # No room, revert?
                         # Or keep old room name and hope? 
                         # Verify old room avail?
                         if self.state.is_room_available(slot_data['room'], min_day, target_slot):
                             pass # Keep old
                         else:
                             # Abort this move
                             self.state.assign_slot(slot_data) # Put back old
                             continue
                    
                    self.state.assign_slot(new_assign)
                    print(f"      Moved {subj} from {max_day} to {min_day}")
                    moved = True
                    break # One move per pass to re-evaluate loads
            
            if not moved:
                print("      No valid moves found this pass.")
                break
