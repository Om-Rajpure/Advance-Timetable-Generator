"""
Timetable State Manager

Manages timetable state during generation, supports assign/rollback operations,
and handles partial/uploaded timetables.
"""

import copy


class TimetableState:
    """Manages the state of a timetable during generation"""
    
    def __init__(self, context):
        """
        Initialize timetable state.
        
        Args:
            context: Dictionary containing:
                {
                    "branchData": {...},
                    "smartInputData": {...},
                    "uploadedTimetable": [...] (optional),
                    "lockedSlots": [...] (optional)
                }
        """
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
        
        # Initialize slots
        self.slots = []
        self.slot_grid = {}  # (day, slot_index, year, division) -> assignment
        self.locked_slots = set()
        
        # Track assignments
        self.teacher_assignments = {}  # (teacher, day, slot) -> assignment
        self.room_assignments = {}  # (room, day, slot) -> assignment
        self.subject_counts = {}  # (subject, year, division) -> count
        
        # Load uploaded timetable if provided
        uploaded = context.get('uploadedTimetable', [])
        if uploaded:
            self._load_uploaded_timetable(uploaded)
        
        # Lock manually edited slots
        locked = context.get('lockedSlots', [])
        for slot_id in locked:
            self.locked_slots.add(slot_id)
    
    def _load_uploaded_timetable(self, uploaded_timetable):
        """Load an uploaded timetable and mark valid slots as locked"""
        for slot in uploaded_timetable:
            if slot.get('valid', True):  # Only load valid slots
                self.assign_slot(slot, lock=True)
    
    def generate_slot_grid(self):
        """Generate all possible slots based on branch data"""
        slots = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # Calculate slot configuration
        from utils.time_utils import calculate_time_slots
        time_config = calculate_time_slots(self.branch_data)
        slots_per_day = time_config['total_slots']
        recess_slot = time_config['recess_slot']
        
        self.recess_slot = recess_slot # Store for access by other components
        
        # Get all years and divisions
        years = self.branch_data.get('academicYears', [])
        divisions_map = self.branch_data.get('divisions', {})
        
        for year in years:
            divisions = divisions_map.get(year, [])
            for division in divisions:
                for day in days:
                    for slot_index in range(slots_per_day):
                        # Skip recess slot
                        if recess_slot is not None and slot_index == recess_slot:
                            continue
                            
                        slot_key = (day, slot_index, year, division)
                        
                        # Check if already filled
                        if slot_key not in self.slot_grid:
                            slots.append({
                                'day': day,
                                'slot': slot_index,
                                'year': year,
                                'division': division,
                                'filled': False
                            })
        
        return slots
    
    def assign_slot(self, assignment, lock=False):
        """
        Assign a value to a slot.
        
        Args:
            assignment: Dictionary with day, slot, year, division, subject, teacher, room, etc.
            lock: Whether to lock this slot (prevent modification)
        """
        slot_key = (
            assignment['day'],
            assignment['slot'],
            assignment['year'],
            assignment['division']
        )
        
        # Store in grid
        # Store in grid
        # Handle collision/multi-batch:
        # If key exists, convert to list? Or fail?
        # For labs, we might assign multiple batches.
        # Let's verify usage. LabScheduler calls assign_slot for EACH batch.
        # So we simply append to a list or support list values?
        
        existing = self.slot_grid.get(slot_key)
        if existing:
            if isinstance(existing, list):
                existing.append(assignment)
                self.slot_grid[slot_key] = existing
            else:
                self.slot_grid[slot_key] = [existing, assignment]
        else:
            self.slot_grid[slot_key] = assignment

        self.slots.append(assignment)
        
        # Track teacher assignment
        teacher_key = (
            assignment.get('teacher'),
            assignment['day'],
            assignment['slot']
        )
        if teacher_key[0]:
            if teacher_key not in self.teacher_assignments:
                self.teacher_assignments[teacher_key] = []
            self.teacher_assignments[teacher_key].append(assignment)
        
        # Track room assignment
        room_key = (
            assignment.get('room'),
            assignment['day'],
            assignment['slot']
        )
        if room_key[0]:
            if room_key not in self.room_assignments:
                self.room_assignments[room_key] = []
            self.room_assignments[room_key].append(assignment)
        
        # Track subject count
        subject_key = (
            assignment.get('subject'),
            assignment['year'],
            assignment['division']
        )
        if subject_key[0]:
            self.subject_counts[subject_key] = self.subject_counts.get(subject_key, 0) + 1
        
        # Lock if requested
        if lock:
            slot_id = assignment.get('id', f"{slot_key[0]}_{slot_key[1]}_{slot_key[2]}_{slot_key[3]}")
            self.locked_slots.add(slot_id)
    
    def rollback_slot(self, assignment):
        """
        Rollback a slot assignment.
        
        Args:
            assignment: The assignment to remove
        """
        slot_key = (
            assignment['day'],
            assignment['slot'],
            assignment['year'],
            assignment['division']
        )
        
        # Remove from grid
        if slot_key in self.slot_grid:
            del self.slot_grid[slot_key]
        
        # Remove from slots list
        if assignment in self.slots:
            self.slots.remove(assignment)
        
        # Remove teacher assignment
        teacher_key = (
            assignment.get('teacher'),
            assignment['day'],
            assignment['slot']
        )
        if teacher_key in self.teacher_assignments:
            if assignment in self.teacher_assignments[teacher_key]:
                self.teacher_assignments[teacher_key].remove(assignment)
            if not self.teacher_assignments[teacher_key]:
                del self.teacher_assignments[teacher_key]
        
        # Remove room assignment
        room_key = (
            assignment.get('room'),
            assignment['day'],
            assignment['slot']
        )
        if room_key in self.room_assignments:
            if assignment in self.room_assignments[room_key]:
                self.room_assignments[room_key].remove(assignment)
            if not self.room_assignments[room_key]:
                del self.room_assignments[room_key]
        
        # Decrement subject count
        subject_key = (
            assignment.get('subject'),
            assignment['year'],
            assignment['division']
        )
        if subject_key in self.subject_counts:
            self.subject_counts[subject_key] -= 1
            if self.subject_counts[subject_key] <= 0:
                del self.subject_counts[subject_key]
    
    def is_slot_locked(self, slot_key):
        """Check if a slot is locked"""
        slot_id = f"{slot_key[0]}_{slot_key[1]}_{slot_key[2]}_{slot_key[3]}"
        return slot_id in self.locked_slots
    
    def get_filled_slots(self):
        """Get all filled slots"""
        return copy.deepcopy(self.slots)
    
    def get_slot_assignment(self, day, slot_index, year, division):
        """Get assignment for specific slot"""
        return self.slot_grid.get((day, slot_index, year, division))

    def is_slot_free(self, day, slot_index, year, division):
        """Check if a slot is completely free for a division (no lectures, no labs)."""
        # Division level check
        if (day, slot_index, year, division) in self.slot_grid:
            return False
            
        # Batch level safety check (if we implement hybrid)
        # For now, if the division slot is empty, it's free.
        # But wait, labs assign to (year, division) but with 'batch' key.
        # So slot_grid might imply full division occupancy?
        
        # Our assign_slot puts it in slot_grid. 
        # If we assign multiple batches to the same (day, slot, year, div), 
        # we need to handle list of assignments or distinct keys.
        
        # Current implementation: slot_grid[(d,s,y,div)] = assignment
        # If we overwrite, we lose data.
        # LAB CHANGE: slot_grid should store a LIST if it's a lab/multi-batch slot.
        # Or we check 'batches' occupancy.
        
        # FAST FIX: simple dict keys don't support parallel batches.
        # We need to refine assign_slot to handle lists or check batch conflicts.
        
        val = self.slot_grid.get((day, slot_index, year, division))
        if val:
            # If there is something here, is it a parallel batch or a full lecture?
            # If full lecture (type!=LAB), it's occupied.
            if val.get('type') != 'LAB':
                return False
            # If it is LAB, it is occupied for THIS context (we usually want empty for new placement)
            return False
            
        return True
    
    def is_teacher_available(self, teacher, day, slot_index):
        """Check if teacher is available at given time"""
        teacher_key = (teacher, day, slot_index)
        return teacher_key not in self.teacher_assignments
    
    def is_room_available(self, room, day, slot_index):
        """Check if room is available at given time"""
        room_key = (room, day, slot_index)
        return room_key not in self.room_assignments
    
    def get_subject_count(self, subject, year, division):
        """Get current count of lectures for a subject"""
        subject_key = (subject, year, division)
        return self.subject_counts.get(subject_key, 0)
    
    def get_remaining_lectures(self, subject, year, division):
        """Get remaining lectures needed for a subject"""
        # Find required count from smart input
        subjects = self.smart_input.get('subjects', [])
        required = 0
        
        for s in subjects:
            if (s.get('name') == subject and 
                s.get('year') == year and 
                s.get('division') == division):
                required = s.get('lecturesPerWeek', 0)
                break
        
        current = self.get_subject_count(subject, year, division)
        return max(0, required - current)
