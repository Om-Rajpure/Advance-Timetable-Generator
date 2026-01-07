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
        Re-organizes the day's schedule to eliminate gaps.
        Strategy: Left-Shift Blocks.
        """
        recess_slot = getattr(self.state, 'recess_slot', None)
        
        # 1. Identify and COLLECT Assignments
        temp_assignments = [] 
        for i in range(12):
            if recess_slot is not None and i == recess_slot:
                continue
                
            ass = self.state.get_slot_assignment(day, i, year, division)
            if ass:
                # Handle list (multi-batch)
                is_multi = isinstance(ass, list)
                data_list = ass if is_multi else [ass]
                first = data_list[0]
                
                temp_assignments.append({
                    'slot': i,
                    'data': data_list,
                    'is_multi': is_multi,
                    'type': first.get('type', 'THEORY'),
                    'subject': first.get('subject')
                })
        
        if not temp_assignments:
            return

        # 2. Group into BLOCKS (Contiguous assignments of same subject)
        blocks = []
        if temp_assignments:
            current_block = [temp_assignments[0]]
            
            for k in range(1, len(temp_assignments)):
                prev = temp_assignments[k-1]
                curr = temp_assignments[k]
                
                slots_diff = curr['slot'] - prev['slot']
                same_subject = (curr['subject'] == prev['subject'])
                same_type = (curr['type'] == prev['type'])
                
                # Logic: If same subject+type and relatively close (<=2 slots difference), group.
                # Actually, strictly contiguous (or jumped over recess) is best.
                # But since we just want to move them together, grouping by subject is safe.
                
                if same_subject and same_type and slots_diff <= 2:
                    current_block.append(curr)
                else:
                    blocks.append(current_block)
                    current_block = [curr]
            blocks.append(current_block)
            
        # 3. ROLLBACK all slots (Clear the board)
        for block in blocks:
            for item in block:
                for a in item['data']:
                    self.state.rollback_slot(a)
                    
        # 4. RE-ASSIGN Blocks Contiguously
        current_slot_ptr = 0
        items_to_place = blocks[:]
        
        # Safety limit for iterations
        max_scan = 12 
        
        while items_to_place:
            
            # Skip Recess Slot
            if recess_slot is not None and current_slot_ptr == recess_slot:
                current_slot_ptr += 1
                continue
                
            if current_slot_ptr >= max_scan:
                # Run out of day!
                # This implies we couldn't fit everything back in.
                # This can happen if shifting accidentally caused a conflict that wasn't there (rare)
                # or if we are just failing to find a spot.
                print(f"Compact Fail: Run out of slots for {year}-{division} on {day}.")
                break
                
            placed = False
            
            for i, block in enumerate(items_to_place):
                block_len = len(block)
                # Can we place this block at current_slot_ptr?
                if self._can_place_block(block, day, current_slot_ptr, block_len):
                    self._place_block(block, day, current_slot_ptr)
                    items_to_place.pop(i)
                    placed = True
                    current_slot_ptr += block_len
                    break
            
            if not placed:
                # Gap forced. Move pointer.
                current_slot_ptr += 1

    def _can_place_block(self, block, day, start_slot, duration):
        """Check if block can be placed starting at start_slot."""
        recess_slot = getattr(self.state, 'recess_slot', None)
        
        # 1. Bounds & Recess Check
        for i in range(duration):
            s = start_slot + i
            if s >= 8: return False # Max slots per day assumption
            if recess_slot is not None and s == recess_slot: return False
            
        # 2. Teacher Availability Check
        for i in range(duration):
            s = start_slot + i
            # Block item i corresponds to offset i
            if i < len(block):
                valid_item = block[i]
                sessions = valid_item['data']
                for sess in sessions:
                    teacher = sess.get('teacher')
                    if teacher and not self.state.is_teacher_available(teacher, day, s):
                        return False
        
        # 3. Room Check (Flexible)
        # Check first item room for simplicity
        first_item = block[0]
        orig_sessions = first_item['data']
        orig_room = orig_sessions[0].get('room')
        
        room_valid = True
        for i in range(duration):
            s = start_slot + i
            if orig_room and not self.state.is_room_available(orig_room, day, s):
                room_valid = False
                break
        
        if room_valid:
            block[0]['_temp_assigned_room'] = orig_room
            return True
            
        # If blocked, try Global Pool (only for THEORY)
        if first_item['type'] == 'THEORY':
             candidate_room = self._find_free_global_room_multi(day, start_slot, duration)
             if candidate_room:
                 block[0]['_temp_assigned_room'] = candidate_room
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
        if not isinstance(all_classrooms, list):
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
        """Commit the block to the state."""
        assigned_room = block[0].get('_temp_assigned_room')
        
        for i, item in enumerate(block):
            current_s = start_slot + i
            sessions = item['data']
            
            for sess in sessions:
                sess['day'] = day
                sess['slot'] = current_s
                
                # Apply new room if applicable
                if assigned_room and sess.get('type') == 'THEORY':
                    sess['room'] = assigned_room
                    
                self.state.assign_slot(sess)
