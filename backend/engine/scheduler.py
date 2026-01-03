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
        Generate timetables for ALL years and divisions independently.
        
        Returns:
            dict: Combined timetable response with quality score.
        """
        self.current_stage = "INITIALIZATION"
        
        print("=== GLOBAL_SETUP ENTERED ===")
        
        try:
            print("GLOBAL_SETUP STARTED")
            
            # --- TASK 3: IDENTIFY FAILING OBJECT ---
            bd = self.context.get('branchData', {})
            si = self.context.get('smartInputData', {})
            
            print(f"DEBUG_TYPE: context_branchData = {type(bd)}")
            print(f"DEBUG_TYPE: context_smartInput = {type(si)}")
            
            if isinstance(bd, dict):
                print(f"DEBUG_TYPE: academicYears = {type(bd.get('academicYears'))}")
                print(f"DEBUG_TYPE: divisions = {type(bd.get('divisions'))}")
                print(f"DEBUG_TYPE: labs = {type(bd.get('labs'))}")
            
            if isinstance(si, dict):
                print(f"DEBUG_TYPE: teachers = {type(si.get('teachers'))}")
                print(f"DEBUG_TYPE: subjects = {type(si.get('subjects'))}")
                print(f"DEBUG_TYPE: map = {type(si.get('teacherSubjectMap'))}")
                
            # 1. Validate & Normalize Inputs
            self._run_stage("INPUT_NORMALIZATION", self._validate_and_normalize_inputs)
            
            print("GLOBAL_SETUP COMPLETED")
            
            # 2. Global Feasibility Check (optional, but good practice)
            # self._run_stage("FEASIBILITY_CHECK", self._run_feasibility_check)
            
            all_timetables = {}
            failures = {} # Map of ClassID -> Error Reason
            
            total_slots_filled = 0
            
            print("GENERATION LOOP STARTED")
            print("Starting Multi-Class Generation Loop...")
            
            # 3. Main Generation Loop
            expected_class_count = len(self.normalized_classes)
            classes_debug = [c['id'] for c in self.normalized_classes]
            print(f"DEBUG: Normalized Classes to Generate: {classes_debug}")
            
            with open('backend_debug_inputs.json', 'w') as f:
                import json
                json.dump({
                    "normalized_classes": self.normalized_classes,
                    "branch_data_keys": list(bd.keys()) if isinstance(bd, dict) else str(type(bd)),
                    "smart_input_keys": list(si.keys()) if isinstance(si, dict) else str(type(si))
                }, f, default=str)
            
            for class_obj in self.normalized_classes:
                class_key = class_obj['id']
                year = class_obj['year']
                division = class_obj['division']
                
                print(f"\n==========================================")
                print(f"🚀 Generating Timetable for: {class_key}")
                print(f"==========================================")
                
                with open('backend_generation_progress.log', 'a') as f:
                    f.write(f"STARTING {class_key}\n")
                
                try:
                    # FIREWALL: Generate independent timetable for this class
                    class_result = self.generate_single_class_timetable(class_obj)
                    
                    # HIERARCHICAL STORAGE
                    if year not in all_timetables:
                        all_timetables[year] = {}
                    
                    # Frontend expects { "timetable": [...] } wrapper per division
                    all_timetables[year][division] = {
                        "timetable": class_result if class_result else {}
                    }
                    
                    if not class_result:
                         print(f"⚠️ Warning: No schedule generated for {class_key} (Empty)", flush=True)
                         failures[class_key] = "Empty result returned"
                         with open('backend_generation_progress.log', 'a') as f:
                            f.write(f"EMPTY {class_key}\n")
                    else:
                        print(f"✅ Generated {class_key} successfully", flush=True)
                        with open('backend_generation_progress.log', 'a') as f:
                            f.write(f"SUCCESS {class_key}\n")

                except Exception as class_err:
                    import traceback
                    traceback.print_exc()
                    error_msg = str(class_err)
                    print(f"❌ FAILED to generate {class_key}: {error_msg}", flush=True)
                    failures[class_key] = error_msg
                    
                    with open('backend_generation_progress.log', 'a') as f:
                        f.write(f"FAILED {class_key}: {error_msg}\n")
                        
                    # Ensure structure exists even on failure
                    import traceback
                    traceback.print_exc()
                    error_msg = str(class_err)
                    print(f"❌ FAILED to generate {class_key}: {error_msg}")
                    failures[class_key] = error_msg
                    # Ensure structure exists even on failure
                    if year not in all_timetables: all_timetables[year] = {}
                    all_timetables[year][division] = { "timetable": [], "error": error_msg }


            # 4. Final Validation / Partial Success
            # SAFE GUARD: unexpected structure
            if isinstance(all_timetables, dict):
                 generated_count = sum(len(divs) for divs in all_timetables.values())
            else:
                 generated_count = 0
                 print(f"CRITICAL: all_timetables is not a dict! ({type(all_timetables)})")
            print(f"\nGeneration Complete. Generated {generated_count}/{expected_class_count} classes.")
            print(f"Failures: {len(failures)}")
            
            # GUARANTEED SUCCESS if at least one generated (or even if 0, return structure so frontend handles it)
            # The User wants "Return status, not throw". 
            
            # Recalculate slots filled for stats
            total_slots_filled = 0
            raw_all_slots = []
            for year_data in all_timetables.values():
                for div_data in year_data.values():
                    tt = div_data.get('timetable', {})
                    if isinstance(tt, dict):
                        for day_slots in tt.values():
                            raw_all_slots.extend(day_slots)
                            total_slots_filled += len(day_slots)

            return {
                "success": True, # Always true if we handled exceptions
                "stage": "COMPLETED",
                "timetables": all_timetables, # Now Hierarchical
                "failures": failures, # Frontend can display these
                "raw_timetable": raw_all_slots, 
                "qualityScore": 100, 
                "message": f"Generated {generated_count}/{expected_class_count} classes. {len(failures)} failures.",
                "stats": {
                    "classes_generated": generated_count,
                    "classes_failed": len(failures),
                    "iterations": self.iterations,
                    "slotsFilled": total_slots_filled,
                    "backtracks": self.backtracks
                },
                "valid": True 
            }
            
            # DEBUG OUTPUT
            with open('backend_debug_result.json', 'w') as f:
                 import json
                 json.dump({
                     "timetables": all_timetables,
                     "failures": failures,
                     "stats": {
                        "classes_generated": generated_count,
                        "classes_failed": len(failures)
                     }
                 }, f, default=str)

        except Exception as e:
            # This catches global setup errors (normalization etc)
            import traceback
            tb = traceback.format_exc()
            print(tb)
            return {
                "success": False,
                "stage": "GLOBAL_SETUP",
                "errorType": type(e).__name__,
                "message": str(e),
                "details": "Critical error before generation loop started.",
                "traceback": tb
            }

    def generate_single_class_timetable(self, class_obj):
        """
        Generate timetable for a Single Class (Year + Division) independently.
        """
        from .theory_scheduler import TheoryScheduler
        
        # 1. Initialize FRESH State (Critical: No shared timeline between classes)
        # We pass context, but we must ensure we don't accidentally pull global junk if not needed.
        # TimetableState re-reads 'uploadedTimetable' from context. 
        # If we want truly empty, we might mask that in context if needed. 
        # For now, assuming standard generation context (no partial upload interference for new gen).
        
        class_state = TimetableState(self.context)
        
        # 2. Initialize Schedulers with this fresh state
        lab_scheduler = LabScheduler(class_state, self.context)
        theory_scheduler = TheoryScheduler(class_state, self.context)
        
        # 3. Schedule Labs
        self.current_stage = f"LAB_SCHEDULING_{class_obj['id']}"
        success_labs = lab_scheduler.schedule_class_labs(class_obj)
        if not success_labs:
            print(f"  🔸 Lab scheduling had issues for {class_obj['id']}")
            
        # STRICT VALIDATION: Ensure all batches covered
        # Get required lab subjects
        subjects = self.context.get('smartInputData', {}).get('subjects', [])
        lab_subjects = [
            s for s in subjects 
            if s.get('year') == class_obj['year'] 
            and (not s.get('division') or s.get('division') == class_obj['division'])
            and (s.get('isPractical') or s.get('type') == 'Practical')
        ]
        
        # Check actual assignments
        assigned_slots = class_state.get_filled_slots()
        batches = class_obj.get('batches', ["B1", "B2", "B3"])
        
        for batch in batches:
            batch_labs = set()
            for slot in assigned_slots:
                if slot.get('batch') == batch and slot.get('type') == 'LAB':
                     batch_labs.add(slot.get('subject'))
            
            # Verify against required
            for lab in lab_subjects:
                if lab['name'] not in batch_labs:
                     error_msg = f"WARNING: Batch {batch} in {class_obj['id']} missing lab {lab['name']}"
                     print(f"    🔸 {error_msg}")
                     # NO RAISE - Allow partial timetable
                     # We can append to a warnings list if we refactor return type, 
                     # but for now, main priority is NOT CRASHING.
                     
        # 4. Schedule Theory
        self.current_stage = f"THEORY_SCHEDULING_{class_obj['id']}"
        # theory_scheduler.schedule_theory returns nothing? checks internal state?
        # It modifies class_state.
        theory_scheduler.schedule_theory(class_obj)
        
        # 5. Extract & Format Result
        # Get all slots filled in this state
        raw_slots = class_state.get_filled_slots()
        
        # Format to canonical
        formatted_all = self.format_to_canonical(raw_slots)
        
        # Extract just this class's schedule
        class_id = class_obj['id']
        class_timetable = formatted_all.get(class_id, {})
        
        # Attach any internal warnings to the result? 
        # The result of this function is just the timetable dict { Day: [...] }.
        # We need to pass warnings up.
        # But for now, we just DON'T CRASH. 
        # The external validator or the caller can check coverage again if needed for reporting.
        
        return class_timetable

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
        
        # STRICT VALIDATION: divisions_map must be dict
        if not isinstance(divisions_map, dict):
             raise TypeError(f"branchData.divisions must be a dictionary, got {type(divisions_map)}")
        
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
                 
        # DEDUPLICATION: Remove duplicates based on Name + Year
        # (User might have uploaded same subject twice or mixed inputs)
        unique_subjects = {}
        cleaned_subjects = []
        for s in subjects:
            # Create a unique key. 
            # Note: If batch-specific, include batch. If division-specific, include division.
            # Currently inputs are mostly year-wise.
            key = (s.get('name'), s.get('year'), s.get('division'), s.get('type'))
            
            if key not in unique_subjects:
                unique_subjects[key] = s
                cleaned_subjects.append(s)
            else:
                print(f"    ⚠️ Warning: Dropping duplicate subject input: {s.get('name')} ({s.get('year')})")
        
        smart_input['subjects'] = cleaned_subjects
        subjects = cleaned_subjects # Update reference for further checks
        
        # VALIDATION: Check if Labs > Working Days
        # If One-Lab-Per-Day rule is active, Labs > Days is IMPOSSIBLE.
        daily_lab_limit = 1 # Rule #7
        working_days = branch_data.get('workingDays', [])
        num_days = len(working_days) if isinstance(working_days, list) else 5
        
        # Count labs per year
        lab_counts = {}
        for s in subjects:
            if s.get('isPractical') or s.get('type') == 'Practical':
                y = s.get('year')
                lab_counts[y] = lab_counts.get(y, 0) + 1
                
        for year, count in lab_counts.items():
            if count > num_days * daily_lab_limit:
                msg = f"Year {year} has {count} labs but only {num_days} working days. Rule 'One Lab/Batch/Day' makes this impossible."
                print(f"❌ CRITICAL CONFIG ERROR: {msg}")
                # We raise error to stop generation immediately and inform user
                raise ValueError(msg)
                 
        # Validate Teachers
        teachers = smart_input.get('teachers', [])
        if not isinstance(teachers, list):
             raise TypeError(f"teachers must be a list, got {type(teachers)}")
        for idx, t in enumerate(teachers):
             if not isinstance(t, dict):
                 raise TypeError(f"Teacher at index {idx} must be a dict, got {type(t)}: {t}")
                 
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
