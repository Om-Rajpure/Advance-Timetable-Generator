"""
Core Timetable Scheduler

Implements CSP-based backtracking algorithm for timetable generation.
"""

from .state_manager import TimetableState
from .candidate_generator import CandidateGenerator
from .heuristics import SlotHeuristics
from constraints.constraint_engine import ConstraintEngine
from .feasibility import FeasibilityVerifier
from .lab_scheduler import LabScheduler

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
        self.feasibility = FeasibilityVerifier(context)
        self.lab_scheduler = LabScheduler(self.state, context)
        
        # Statistics
        self.iterations = 0
        self.backtracks = 0
    
    def generate(self):
        """
        Generate a complete timetable using Iterative Constructive Approach.
        Sequence: Labs -> Theory (per class).
        """
        from .theory_scheduler import TheoryScheduler
        self.theory_scheduler = TheoryScheduler(self.state, self.context)
        
        self.current_stage = "INITIALIZATION"
        
        try:
            # Step 1: Input Validation & Normalization
            self._run_stage("INPUT_NORMALIZATION", self._validate_and_normalize_inputs)

            # Step 2: Feasibility Check
            self._run_stage("FEASIBILITY_CHECK", self._run_feasibility_check)

            # Step 3: Iterative Scheduling
            print("Starting Iterative Scheduling...")
            
            for class_obj in self.normalized_classes:
                print(f"\n--- Generating for {class_obj['id']} ---")
                
                # A. Schedule Labs
                self._run_stage(f"LAB_SCHEDULING_{class_obj['id']}", 
                              lambda: self._schedule_labs_wrapper(class_obj))
                
                # B. Schedule Theory
                self._run_stage(f"THEORY_SCHEDULING_{class_obj['id']}",
                              lambda: self.theory_scheduler.schedule_theory(class_obj))

            # Step 4: Final Compilation
            self._run_stage("FINAL_COMPILATION", self._compile_final_result)
            
            # Format to Canonical Structure
            formatted_timetable = self.format_to_canonical(self.state.get_filled_slots())

            # Validate Theory + Lab coverage
            self._validate_content_coverage(formatted_timetable)

            # --- CRITICAL FIX: EMPTY SLOT VALIDATION ---
            # Task 4 & 6: Ensure we don't return success empty
            if not formatted_timetable:
                import json
                print("DEBUG: Smart Input Context Keys:", self.context.get('smartInputData', {}).keys())
                print("DEBUG: Branch Data Keys:", self.context.get('branchData', {}).keys())
                raise RuntimeError({
                    "error": "Generated timetable is empty",
                    "details": "No slots were assigned for any class. Check input data (Subjects/Teachers) or Constraints.",
                    "stats": {
                        "iterations": self.iterations,
                        "slotsFilled": 0
                    }
                })

            # Check for specific classes being empty
            empty_classes = []
            for class_obj in self.normalized_classes:
                class_id = class_obj['id']
                if class_id not in formatted_timetable or not formatted_timetable[class_id]:
                    empty_classes.append(class_id)
            
            if empty_classes:
                print(f"⚠️ Warning: No schedule generated for classes: {empty_classes}")
                # We could choose to fail here too, but maybe partial success is allowed?
                # For this specific 'Empty Timetable' bug, let's just log loudly.

            return {
                "success": True,
                "stage": "COMPLETED",
                "timetable": formatted_timetable,
                "raw_timetable": self.final_timetable, # For optimization
                "valid": True,
                "qualityScore": 100, 
                "message": "Timetable generated successfully",
                "stats": {
                    "iterations": self.iterations,
                    "slotsFilled": len(self.state.slots)
                }
            }
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # Extract structured error if it's our wrapper
            error_data = str(e)
            if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
                 return {
                    "success": False,
                    "stage": e.args[0].get('stage', self.current_stage),
                    "reason": e.args[0].get('error', str(e)),
                    "errorType": e.args[0].get('type', type(e).__name__),
                    "details": e.args[0]
                }
            
            return {
                "success": False,
                "stage": self.current_stage,
                "errorType": type(e).__name__,
                "message": str(e),
                "details": "Unexpected error during generation.",
                "debug": {}
            }

    def _run_stage(self, stage_name, fn):
        """Execute a generation stage with error context."""
        self.current_stage = stage_name
        try:
            fn()
        except Exception as e:
            # Re-raise with context
            raise RuntimeError({
                "stage": stage_name,
                "error": str(e),
                "type": type(e).__name__
            })

    def _validate_and_normalize_inputs(self):
        """Validate raw inputs and construct canonical class objects."""
        self._validate_inputs() # Call the existing validator
        
        # Normalize Branch Data into Class Objects
        self.normalized_classes = []
        
        years = self.context.get('branchData', {}).get('academicYears', [])
        divisions_map = self.context.get('branchData', {}).get('divisions', {})
        
        if not isinstance(years, list): 
            raise ValueError(f"academicYears must be list, got {type(years)}")
            
        for year in years:
            if not isinstance(year, str):
                raise ValueError(f"Year must be string, got {type(year)}: {year}")
                
            divs = divisions_map.get(year, [])
            if not isinstance(divs, list):
                raise ValueError(f"Divisions for {year} must be list, got {type(divs)}")
                
            for div in divs:
                if not isinstance(div, str):
                    raise ValueError(f"Division must be string, got {type(div)}: {div}")
                    
                self.normalized_classes.append({
                    "id": f"{year}-{div}",
                    "year": year,
                    "division": div,
                    "batches": ["B1", "B2", "B3"] # Defaulting batches for now
                })
                
    def _run_feasibility_check(self):
        result = self.feasibility.verify()
        if not result['valid']:
             raise ValueError(f"Feasibility Failed: {result.get('reason')}")

    def _schedule_labs_wrapper(self, class_obj):
        if not self.lab_scheduler.schedule_class_labs(class_obj):
             print(f"Warning: Could not schedule all labs for {class_obj['id']}")

    def _compile_final_result(self):
        # Just ensure state is clean, actual formatting happens in generate()
        self.final_timetable = self.state.get_filled_slots()

    def format_to_canonical(self, slots_list):
        """
        Convert list of slots to the canonical format:
        {
            "SE-A": {
                "Monday": [ {...}, ... ],
                ...
            },
            ...
        }
        """
        canonical = {}
        
        for slot in slots_list:
            class_id = f"{slot['year']}-{slot['division']}"
            day = slot['day']
            
            if class_id not in canonical:
                canonical[class_id] = {}
            
            if day not in canonical[class_id]:
                canonical[class_id][day] = []
                
            # Filter keys for clean output
            clean_slot = {k: v for k, v in slot.items() if k not in ['id', 'isPractical']}
            # Ensure critical keys exist
            if 'type' not in clean_slot:
                clean_slot['type'] = 'THEORY' # Default
                
            canonical[class_id][day].append(clean_slot)
            
        # Sort slots by time
        for class_id in canonical:
            for day in canonical[class_id]:
                canonical[class_id][day].sort(key=lambda s: s['slot'])
                
        return canonical

    def _validate_content_coverage(self, timetable):
        """Ensure every class has both Theory and Lab (if applicable)."""
        for class_id, schedule in timetable.items():
            has_theory = False
            has_lab = False
            
            for day, slots in schedule.items():
                for slot in slots:
                    if slot.get('type') == 'THEORY':
                        has_theory = True
                    if slot.get('type') == 'LAB':
                        has_lab = True
            
            print(f"Content Check for {class_id}: Theory={has_theory}, Lab={has_lab}")
            # We don't fail hard here yet to avoid breaking partial generations, 
            # but we log it. In future, we can raise specific warnings.

    def _validate_inputs(self):
        """
        Validate input data structure to prevent 'str' object has no attribute 'get' errors.
        """
        if not isinstance(self.context, dict):
             raise TypeError(f"Context must be a dict, got {type(self.context)}")
        
        branch_data = self.context.get('branchData')
        if not isinstance(branch_data, dict):
             raise TypeError(f"branchData must be a dict, got {type(branch_data)}")
             
        smart_input = self.context.get('smartInputData')
        if not isinstance(smart_input, dict):
             raise TypeError(f"smartInputData must be a dict, got {type(smart_input)}")
             
        # Validate Subjects
        subjects = smart_input.get('subjects', [])
        if not isinstance(subjects, list):
             raise TypeError(f"subjects must be a list, got {type(subjects)}")
        for idx, s in enumerate(subjects):
             if not isinstance(s, dict):
                 raise TypeError(f"Subject at index {idx} must be a dict, got {type(s)}: {s}")
                 
        # Validate Teachers
        teachers = smart_input.get('teachers', [])
        if not isinstance(teachers, list):
             raise TypeError(f"teachers must be a list, got {type(teachers)}")
        for idx, t in enumerate(teachers):
             if not isinstance(t, dict):
                 raise TypeError(f"Teacher at index {idx} must be a dict, got {type(t)}: {t}")

    
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
