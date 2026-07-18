"""
Timetable State Manager

Manages timetable state during generation, supports assign/rollback operations,
and handles partial/uploaded timetables.

FIX D: Added get_batches_for_division() to expose per-year batch names
        to gap_utils, theory_scheduler, and optimizer.
FIX D: Added get_total_slots() convenience accessor used by gap_utils.
"""

import copy

try:
    import utils.time_utils as time_utils
except ImportError:
    try:
        from backend.utils import time_utils
    except ImportError:
        time_utils = None



class TimetableState:
    """Manages the state of a timetable during generation"""
    
    def __init__(self, context, load_manager=None, logger=None):
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
        self.load_manager = load_manager
        self.logger = logger
        
        # Initialize slots
        self.slots = []
        self.slot_grid = {}  # (day, slot_index, year, division) -> assignment
        self.locked_slots = set()
        
        # Track assignments
        self.teacher_assignments = {}  # (teacher, day, slot) -> assignment
        self.room_assignments = {}  # (room, day, slot) -> assignment
        self.subject_counts = {}  # (subject, year, division) -> count
        
        # Room Balancing State (Global)
        from collections import Counter
        self.room_usage_counts = Counter() # Map room_name -> usage_count
        self.preferred_rooms = {} # Map class_id -> assigned_room (Sticky Room)
        
        # Load uploaded timetable if provided
        uploaded = context.get('uploadedTimetable', [])
        if uploaded:
            self._load_uploaded_timetable(uploaded)
        
        # Lock manually edited slots
        locked = context.get('lockedSlots', [])
        for slot_id in locked:
            self.locked_slots.add(slot_id)
            
        # Teacher Metadata (for fast lookup of login times)
        self.teacher_metadata = {}
        teachers = self.smart_input.get('teachers', [])
        for t in teachers:
            if t.get('name'):
                self.teacher_metadata[t['name']] = {
                    'loginTime': t.get('loginTime'), # e.g. "09:00"
                    'workingHours': t.get('workingHours', 8)
                }

        # GLOBAL CONSTANT: Recess Slot (Task: Enforce Global Recess)
        try:
             if time_utils:
                 time_config = time_utils.calculate_time_slots(self.branch_data)
                 self.recess_slot = time_config.get('recess_slot')
                 self.total_slots = time_config.get('total_slots', 8)
                 if self.recess_slot is not None:
                      print(f"STATE: Global Recess Fixed at Slot {self.recess_slot}")
             else:
                 raise ImportError("time_utils missing")
        except:
             self.recess_slot = 4 # Default Fallback
             self.total_slots = 8
             print("STATE: Recess Defaulting to 4 (Calc Failed)")

    
    # block_recess_for_class REMOVED - Recess is inferred from Branch Data only.
    
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
    
    def get_schedulable_slots(self):
        """
        Return a list of VALID, SCHEDULABLE slot indices.
        Strictly excludes Recess slot.
        """
        # Calculate if not already present
        if not hasattr(self, 'recess_slot'):
             from utils.time_utils import calculate_time_slots
             time_config = calculate_time_slots(self.branch_data)
             self.recess_slot = time_config.get('recess_slot')
             self.total_slots = time_config.get('total_slots', 8)
             
        valid_slots = []
        for i in range(getattr(self, 'total_slots', 8)):
            if self.recess_slot is not None and i == self.recess_slot:
                continue
            valid_slots.append(i)
        return valid_slots
    
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
            # If entry exists, convert to list if not already
            if isinstance(existing, list):
                existing.append(assignment)
                self.slot_grid[slot_key] = existing
            else:
                self.slot_grid[slot_key] = [existing, assignment]
            print(f"DEBUG: Slot Collision or Multi-Assign at {slot_key}! Exist: {type(existing)}", flush=True)
        else:
            # First assignment -> Store as single object
            self.slot_grid[slot_key] = assignment
            
        # DEBUG TRIGGER REMOVED

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

        # UPDATE LOAD MANAGER
        if self.load_manager:
            t = assignment.get('teacher')
            d = assignment.get('day')
            # Determine duration (Theory=1, Lab could be 2, but here we process per slot usually)
            # However, lab scheduler might call assign_slot multiple times for same session (duration times)
            # OR once? Let's check lab scheduler.
            # LabScheduler calls assign_slot for EACH duration offset. So here commit 1 is correct.
            if t and d:
                self.load_manager.commit_load(t, d, duration=1)
    
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

        # UPDATE LOAD MANAGER (ROLLBACK)
        if self.load_manager:
            t = assignment.get('teacher')
            d = assignment.get('day')
            if t and d:
                self.load_manager.rollback_load(t, d, duration=1)

    def remove_slot(self, year, division, day, slot_idx):
        """
        Convenience wrapper: look up the assignment at (year, division, day, slot_idx)
        and call rollback_slot() on it.

        This is the method previously called by _balance_theory_distribution() in
        theory_scheduler.py.  TimetableState never had it; this fixes the AttributeError:
            'TimetableState' object has no attribute 'remove_slot'

        Args:
            year:      e.g. "SE"
            division:  e.g. "A"
            day:       e.g. "Monday"
            slot_idx:  int slot index

        Returns:
            True  if an assignment was found and removed
            False if the slot was already empty (safe no-op)
        """
        slot_key = (day, slot_idx, year, division)
        existing = self.slot_grid.get(slot_key)

        if existing is None:
            return False   # nothing to remove — safe no-op

        if isinstance(existing, list):
            # Multi-batch slot: remove all assignments in the list
            for assignment in list(existing):
                self.rollback_slot(assignment)
        else:
            # Single assignment dict
            self.rollback_slot(existing)

        return True

    # Alias used in some older code paths
    def remove_assignment(self, year, division, day, slot_idx):
        """Alias for remove_slot() for backward compatibility."""
        return self.remove_slot(year, division, day, slot_idx)

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
        """Check if teacher is available at given time (not assigned AND within working hours)"""
        # 1. Assignment Check
        teacher_key = (teacher, day, slot_index)
        if teacher_key in self.teacher_assignments:
            return False
            
        # 2. Availability Window Check
        meta = self.teacher_metadata.get(teacher, {})
        if not meta:
            return True # No constraints
            
        login_time = meta.get('loginTime')
        if not login_time:
            return True # Default to available
            
        # Lazy Import to avoid cycle/path issues
        if not time_utils:
             print("CRITICAL IMPORT ERROR: Could not find time_utils")
             return True
        
        get_slot_time = time_utils.get_slot_time
        is_time_in_window = time_utils.is_time_in_window
        
        # Calculate real time of slot
        try:
            slot_time = get_slot_time(slot_index, self.branch_data)
        except Exception as e:
            # Fallback if time calculation breaks
            return True
        
        # Get lecture duration (default 60 mins)
        duration_mins = int(self.branch_data.get('lectureDuration', 60))
        
        # Check window
        working_hours = meta.get('workingHours', 8)
        is_available = is_time_in_window(slot_time, login_time, working_hours, duration_mins)
        
        if not is_available:
            # DEBUG LOG
            try:
                with open('backend_constraints_log.txt', 'a') as f:
                    f.write(f"REJECTED: Teacher {teacher} on Day {day} Slot {slot_index} ({slot_time}) due to Window [{login_time} for {working_hours} hrs] (Dur: {duration_mins})\n")
            except: 
                pass
            
        return is_available

    
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
                # Division check: current logic is loose on division property in subjects
                # Assuming subject def applies to all divisions unless specified
                (s.get('division') == division or not s.get('division'))):
                required = int(s.get('lecturesPerWeek', 0))
                break
        
        current = self.get_subject_count(subject, year, division)
        return max(0, required - current)

    def get_daily_load_for_class(self, year, division, day):
        """
        Returns number of lectures already scheduled for a given class on a given day.
        Used for load balancing.
        """
        load = 0
        
        # Iterate slots for this day/class
        # Since we don't store day-wise index efficiently, we scan slot_grid
        # Optimization: Pre-calculate or use heuristics? 
        # For now, scan total slots (e.g. 7).
        
        # Determine max slots
        total_slots = 8 # Safety upper bound
        
        for slot_idx in range(total_slots):
            key = (day, slot_idx, year, division)
            if key in self.slot_grid:
                 load += 1
                 
        return load

    def get_daily_load_for_teacher(self, teacher, day):
        """
        Returns number of lectures assigned to a teacher on a specific day.
        """
        load = 0
        total_slots = 8
        
        for slot_idx in range(total_slots):
            key = (teacher, day, slot_idx)
            if key in self.teacher_assignments:
                load += 1
        
        return load

    # ------------------------------------------------------------------
    # FIX D: Batch / slot-count accessors
    # ------------------------------------------------------------------

    def get_total_slots(self):
        """
        Return the total number of slots per day (including the recess slot).
        Used by gap_utils.build_batch_daily_schedule() to size the schedule list.
        """
        return getattr(self, 'total_slots', 8)

    def get_batches_for_division(self, year, division):
        """
        FIX D: Returns the list of batch names for a given year/division.

        e.g. ["B1", "B2", "B3"] for a division with 3 batches.

        Derives this from branchData.labBatchesPerYear stored at init:
            n = branchData['labBatchesPerYear'].get(year, 0)
            return [f"B{i+1}" for i in range(n)]

        If not defined, returns [] (no batches — treat as division-level only).

        Args:
            year:     e.g. "BE"
            division: e.g. "A"  (unused currently — all divisions share the
                                  same batch count per year; kept for API stability)
        """
        n = self.branch_data.get('labBatchesPerYear', {}).get(year, 0)
        return [f'B{i+1}' for i in range(n)]
