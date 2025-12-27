"""
Core Timetable Scheduler

Implements CSP-based backtracking algorithm for timetable generation.
"""

from .state_manager import TimetableState
from .candidate_generator import CandidateGenerator
from .heuristics import SlotHeuristics
from constraints.constraint_engine import ConstraintEngine


class TimetableScheduler:
    """Main CSP scheduler for timetable generation"""
    
    def __init__(self, context, max_iterations=10000):
        """
        Initialize scheduler.
        
        Args:
            context: Dictionary with branchData, smartInputData, etc.
            max_iterations: Maximum backtracking iterations
        """
        self.context = context
        self.max_iterations = max_iterations
        
        # Initialize components
        self.state = TimetableState(context)
        self.candidate_gen = CandidateGenerator(self.state, context)
        self.heuristics = SlotHeuristics(self.state, context)
        self.constraint_engine = ConstraintEngine()
        
        # Statistics
        self.iterations = 0
        self.backtracks = 0
    
    def generate(self):
        """
        Generate a complete timetable.
        
        Returns:
            {
                "success": bool,
                "timetable": [...],
                "valid": bool,
                "qualityScore": float,
                "violations": [...],
                "message": str,
                "stats": {...}
            }
        """
        # Generate all possible slots
        all_slots = self.state.generate_slot_grid()
        
        # Order slots by difficulty
        ordered_slots = self.heuristics.order_slots(all_slots)
        
        # Run backtracking
        result = self._backtrack(ordered_slots, 0)
        
        if result:
            # Validate final timetable
            validation = self.constraint_engine.validate_timetable(
                self.state.get_filled_slots(),
                self.context
            )
            
            return {
                "success": True,
                "timetable": self.state.get_filled_slots(),
                "valid": validation['valid'],
                "qualityScore": validation['qualityScore'],
                "violations": validation['hardViolations'] + validation['softViolations'],
                "message": "Timetable generated successfully",
                "stats": {
                    "iterations": self.iterations,
                    "backtracks": self.backtracks,
                    "totalSlots": len(self.state.slots)
                }
            }
        else:
            # Failed to generate
            return self._generate_failure_report()
    
    def _backtrack(self, remaining_slots, depth):
        """
        Recursive backtracking algorithm.
        
        Args:
            remaining_slots: List of unfilled slots
            depth: Current recursion depth
        
        Returns:
            True if solution found, False otherwise
        """
        self.iterations += 1
        
        # Check iteration limit
        if self.iterations >= self.max_iterations:
            return False
        
        # Base case: all slots filled
        if not remaining_slots:
            return True
        
        # Select next slot using heuristic
        current_slot = self.heuristics.select_next_slot(remaining_slots)
        if not current_slot:
            return True  # No more slots to fill
        
        # Generate candidates for this slot
        candidates = self.candidate_gen.generate_candidates(current_slot)
        
        # Try each candidate
        for candidate in candidates:
            # Handle practical group (multiple slots)
            if candidate.get('practical_group'):
                assignments = candidate['assignments']
                
                # Assign all batches
                for assignment in assignments:
                    assignment['id'] = self._generate_slot_id(assignment)
                    self.state.assign_slot(assignment)
                
                # Validate
                if self._is_valid_state():
                    # Remove current slot from remaining
                    new_remaining = [s for s in remaining_slots if s != current_slot]
                    
                    # Recurse
                    if self._backtrack(new_remaining, depth + 1):
                        return True
                
                # Rollback all batches
                self.backtracks += 1
                for assignment in assignments:
                    self.state.rollback_slot(assignment)
            
            else:
                # Regular lecture
                candidate['id'] = self._generate_slot_id(candidate)
                self.state.assign_slot(candidate)
                
                # Validate
                if self._is_valid_state():
                    # Remove current slot from remaining
                    new_remaining = [s for s in remaining_slots if s != current_slot]
                    
                    # Recurse
                    if self._backtrack(new_remaining, depth + 1):
                        return True
                
                # Rollback
                self.backtracks += 1
                self.state.rollback_slot(candidate)
        
        # No valid assignment found
        return False
    
    def _is_valid_state(self):
        """
        Check if current state is valid using constraint engine.
        
        Only checks hard constraints for efficiency.
        """
        current_timetable = self.state.get_filled_slots()
        
        # Quick validation: check only incremental constraints
        # For full generation, we check teacher/room overlaps
        
        # Get last few assignments
        if not current_timetable:
            return True
        
        recent_slots = current_timetable[-5:] if len(current_timetable) > 5 else current_timetable
        
        # Check hard constraints on recent slots
        for slot in recent_slots:
            day = slot['day']
            slot_index = slot['slot']
            teacher = slot.get('teacher')
            room = slot.get('room')
            
            # Teacher overlap check
            if teacher and teacher != 'TBA':
                teacher_key = (teacher, day, slot_index)
                if len(self.state.teacher_assignments.get(teacher_key, [])) > 1:
                    return False
            
            # Room overlap check
            if room and room != 'TBA':
                room_key = (room, day, slot_index)
                if len(self.state.room_assignments.get(room_key, [])) > 1:
                    return False
        
        return True
    
    def _generate_slot_id(self, slot):
        """Generate unique ID for a slot"""
        return f"{slot['day']}_{slot['slot']}_{slot['year']}_{slot['division']}_{slot.get('batch', '')}"
    
    def _generate_failure_report(self):
        """Generate detailed failure report when no solution found"""
        # Analyze what went wrong
        blockers = []
        suggestions = []
        
        # Check if enough labs
        smart_input = self.context.get('smartInputData', {})
        subjects = smart_input.get('subjects', [])
        branch_data = self.context.get('branchData', {})
        labs = branch_data.get('labs', [])
        
        # Find practical subjects needing most batches
        max_batches_needed = 0
        for subject in subjects:
            if subject.get('type') == 'Practical':
                batches = subject.get('batches', 3)
                if batches > max_batches_needed:
                    max_batches_needed = batches
        
        if max_batches_needed > len(labs):
            blockers.append({
                "issue": "Insufficient labs",
                "details": f"Need {max_batches_needed} labs but only {len(labs)} available"
            })
            suggestions.append(f"Add {max_batches_needed - len(labs)} more lab(s)")
        
        # Check teacher workload
        teachers = smart_input.get('teachers', [])
        if len(teachers) < 3:
            blockers.append({
                "issue": "Too few teachers",
                "details": f"Only {len(teachers)} teachers available"
            })
            suggestions.append("Add more teachers to distribute workload")
        
        # Check if iteration limit reached
        if self.iterations >= self.max_iterations:
            blockers.append({
                "issue": "Iteration limit reached",
                "details": f"Exhausted {self.max_iterations} iterations without finding solution"
            })
            suggestions.append("Try increasing max_iterations or simplifying constraints")
        
        return {
            "success": False,
            "timetable": self.state.get_filled_slots(),
            "valid": False,
            "qualityScore": 0,
            "violations": [],
            "message": "Failed to generate valid timetable",
            "blockers": blockers,
            "suggestions": suggestions,
            "stats": {
                "iterations": self.iterations,
                "backtracks": self.backtracks,
                "slotsF illed": len(self.state.slots)
            }
        }
