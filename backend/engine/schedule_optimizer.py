"""
Schedule Optimizer Module

Responsible for post-processing the generated timetable to enforce critical
constraints like "Daily Compaction" (No Gaps).
"""
import copy

class ScheduleOptimizer:
    def __init__(self, state):
        self.state = state
        self.context = state.context
        
    def compact_daily_schedule(self, year, division, day):
        """
        Re-organizes the day's schedule to eliminate gaps using GRAVITY ALGORITHM.
        
        Strategy: Fill-First (Gravity)
        1. Collect all valid assignments for the day.
        2. CLEAR the day's slots in the state.
        3. Sort assignments by priority (Practical blocks > Theory).
        4. Re-insert them starting from Slot 0 (skipping Recess).
        """
        try:
            from utils.time_utils import calculate_time_slots
            time_config = calculate_time_slots(self.context.get('branchData', {}))
            recess_slot = time_config.get('recess_slot')
        except:
             recess_slot = getattr(self.state, 'recess_slot', None)
        
        # 1. EXTRACT: Collect all Assignments
        #    We grouping them into "Blocks" that must stay together (e.g. Lab sessions)
        raw_assignments = []
        
        # USE CENTRALIZED SCHEDULABLE SLOTS
        schedulable_indices = self.state.get_schedulable_slots()
        
        for i in schedulable_indices: 
            ass = self.state.get_slot_assignment(day, i, year, division)
            if ass:
                # Normalize to list
                is_multi = isinstance(ass, list)
                data_list = ass if is_multi else [ass]
                
                # Check what type
                first = data_list[0]
                
                # Double check we didn't pick up RECESS object
                if first.get('type') in ['RECESS', 'BREAK']:
                    continue

                raw_assignments.append({
                    'original_slot': i,
                    'data': data_list,
                    'type': first.get('type', 'THEORY'),
                    'subject': first.get('subject'),
                    'is_practical': first.get('type') == 'Practical' or first.get('isPractical')
                })
        
        if not raw_assignments:
            return # Nothing to compact

        # 2. GROUPING (Reconstruct blocks)
        #    If we have consecutive slots of same Subject+Type, treat as one BLOCK.
        #    This is critical for Labs (2-3 hrs) to move as a unit.
        blocks = []
        if raw_assignments:
            # Sort by original slot to ensure correct grouping order
            raw_assignments.sort(key=lambda x: x['original_slot'])
            
            current_block = [raw_assignments[0]]
            
            for k in range(1, len(raw_assignments)):
                prev = raw_assignments[k-1]
                curr = raw_assignments[k]
                
                # Check continuity
                is_consecutive = (curr['original_slot'] - prev['original_slot']) == 1
                # If there's a recess gap, they might still be consecutive logically?
                # For now, strict slot continuity is required for a BLOCK.
                
                same_subject = (curr['subject'] == prev['subject'])
                same_type = (curr['type'] == prev['type'])
                
                if is_consecutive and same_subject and same_type:
                    current_block.append(curr)
                else:
                    blocks.append(current_block)
                    current_block = [curr]
            blocks.append(current_block)

        # 3. CLEAR THE BOARD (The scariest part!)
        #    We must remove these from the state so we can re-place them without self-collision.
        for block in blocks:
            for item in block:
                for a in item['data']:
                    self.state.rollback_slot(a)
                    
        # 4. SORT BLOCKS
        #    Priority: Practicals (Hard constraints) > Theory
        #    Within same type: maintain original relative order (Stable sort)
        #    Actually, to maintain relative order of lectures, we should JUST rely on original order.
        #    BUT, if we want to fill gaps, we just push everything LEFT.
        #    So, simpler is better: Keep original order of blocks.
        #    Exception: If we couldn't place a block, we might try to swap? No, that breaks teacher flow.
        
        # 5. RE-INSERT WITH GRAVITY
        current_slot_ptr = 0
        total_slots = getattr(self.state, 'total_slots', 8)

        # Track failures to re-insert
        failed_blocks = []

        for block in blocks:
            duration = len(block)
            subj = block[0]['subject']

            with open('backend_compaction_trace.log', 'a', encoding='utf-8') as f:
                 f.write(f"COMPACTION: {year}-{division} | Block {subj} | Size: {duration} | OrigSlot: {block[0]['original_slot']}\n")

            placed = False

            # Search for FIRST valid slot starting from slot 0 (gravity / slide-left).
            # FIX 3b: We must never slide a block INTO the recess slot.
            # Build the candidate start list from schedulable_indices, skipping any
            # start position whose window overlaps the recess slot.

            for start_s in schedulable_indices:
                # Bounds check
                if start_s + duration > total_slots:
                    continue

                # FIX 3b: Explicit recess-slot skip -- reject ANY window whose
                # range [start_s, start_s + duration) includes the recess slot.
                if recess_slot is not None:
                    hit_recess = any(
                        (start_s + i) == recess_slot for i in range(duration)
                    )
                    if hit_recess:
                        continue

                # Check Constraints
                if self._can_place_block(block, day, start_s, duration):
                    self._place_block(block, day, start_s)
                    placed = True
                    break
            
            if not placed:
                print(f"[WARNING] Compaction Warning: Could not re-place block {block[0]['subject']} ({block[0]['type']}) in {year}-{division}. Restoring to original.")
                # RESTORE to original slots
                # We need to ensure original slots are still free?
                # We cleared them, and if we followed specific order (sorted by time), 
                # earlier blocks might have moved into our original slots?
                # This is tricky. 
                # Better strategy: Try to place at original_slot specifically.
                
                start_original = block[0]['original_slot']
                if self._can_place_block(block, day, start_original, duration):
                    self._place_block(block, day, start_original)
                else:
                    print(f"[FAIL] CRITICAL: Could not even restore {block[0]['subject']} to original slot {start_original}!")
                    failed_blocks.append(block)

    def _can_place_block(self, block, day, start_slot, duration):
        """Check if block can be placed starting at start_slot."""
        
        # 1. Slot Vacancy Check (Is slot empty in current state?)
        for i in range(duration):
            s = start_slot + i
            # Check global conflict (other divisions)
            # Since we only control OUR schedule, we check if WE have something there.
            # But we cleared our slots? Yes, rollback_slot was called.
            # So get_slot_assignment should return None, UNLESS we re-filled it in this loop.
            
            existing = self.state.get_slot_assignment(day, s, block[0]['data'][0]['year'], block[0]['data'][0]['division'])
            if existing: 
                return False 

        # 2. Teacher Availability Check
        for i in range(duration):
            s = start_slot + i
            valid_item = block[i]
            sessions = valid_item['data']
            for sess in sessions:
                teacher = sess.get('teacher')
                # Check teacher busy elsewhere
                if teacher and not self.state.is_teacher_available(teacher, day, s):
                    return False
        
        # 3. Room Check
        # Try to use original room if possible, else find any room.
        first_item = block[0]
        # Labs usually have fixed rooms. Theory is flexible.
        is_theory = (first_item['type'] == 'THEORY')
        orig_sessions = first_item['data']
        orig_room = orig_sessions[0].get('room')
        
        room_valid = True
        for i in range(duration):
            s = start_slot + i
            # For each sub-session (batch)
            # Actually, just check if the proposed room is free.
            if orig_room and not self.state.is_room_available(orig_room, day, s):
                room_valid = False
                break
        
        if room_valid:
            block[0]['_temp_target_room'] = orig_room
            return True
            
        # If original room blocked, try to find NEW room (Only for Theory)
        if is_theory:
             candidate_room = self._find_free_global_room_multi(day, start_slot, duration)
             if candidate_room:
                 block[0]['_temp_target_room'] = candidate_room
                 return True
                 
        return False
        
    def _find_free_global_room_multi(self, day, start_slot, duration):
        """Find room available for multiple consecutive slots."""
        branch_data = self.context.get('branchData', {})
        all_classrooms = branch_data.get('classrooms', [])
        
        # Normalize
        if isinstance(all_classrooms, dict):
             temp = []
             for v in all_classrooms.values():
                 if isinstance(v, list): temp.extend(v)
             all_classrooms = list(set(temp))
        if not isinstance(all_classrooms, list) or not all_classrooms:
             all_classrooms = branch_data.get('rooms', [])

        for r in all_classrooms:
            r_name = r.get('name') if isinstance(r, dict) else r
            
            is_free = True
            for i in range(duration):
                if not self.state.is_room_available(r_name, day, start_slot + i):
                    is_free = False
                    break
            
            if is_free:
                return r_name
        return None

    def _place_block(self, block, day, start_slot):
        """Commit the block to the state at new position."""
        target_room = block[0].get('_temp_target_room')
        
        for i, item in enumerate(block):
            current_s = start_slot + i
            sessions = item['data']
            
            for sess in sessions:
                sess['day'] = day
                sess['slot'] = current_s
                
                # Update room if we found a better one / forced one
                # Note: For Labs (multi-batch), usually we don't swap rooms easily 
                # because implies multiple different rooms. 
                # But here we treat Lab as single block. 
                # If target_room is set, it overrides.
                # BUT wait, Labs have different rooms per batch usually?
                # If 'target_room' reflects the first batch's room, we shouldn't apply it to all batches bluntly if they were different.
                
                # Safer: Only override room for Theory.
                if sess.get('type') == 'THEORY' and target_room:
                     sess['room'] = target_room
                # For labs, keep original room unless specific logic added.
                # But we checked original room availability above.
                    
                self.state.assign_slot(sess)
