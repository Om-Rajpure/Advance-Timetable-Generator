"""
Core Timetable Scheduler

Implements CSP-based backtracking algorithm for timetable generation.
"""

from .state_manager import TimetableState
from .candidate_generator import CandidateGenerator
from .heuristics import SlotHeuristics
from constraints.constraint_engine import ConstraintEngine
from .feasibility import FeasibilityVerifier
from .feasibility import FeasibilityVerifier
from .lab_scheduler import LabScheduler
from .data_normalizer import DataNormalizer, NormalizationError

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__)) 
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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
        from .load_manager import TeacherLoadManager
        self.load_manager = TeacherLoadManager(context)
        
        self.state = TimetableState(context, self.load_manager) # Pass manager to state
        self.candidate_gen = CandidateGenerator(self.state, context)
        self.heuristics = SlotHeuristics(self.state, context)
        self.constraint_engine = ConstraintEngine()
        self.feasibility = FeasibilityVerifier(context)
        self.lab_scheduler = LabScheduler(self.state, context)
        
        # Room Balancing State
        from collections import Counter
        self.room_assignments = {} # Map class_id -> assigned_room
        self.room_counts = Counter() # Map room_name -> usage_count
        
        # Statistics
        self.iterations = 0
        self.backtracks = 0
    
    def generate(self):
        """
        Generate timetables for ALL years and divisions independently.
        
        Returns:
            dict: Combined timetable response with quality score.
        """
        # Path setup moved to module level
        
        try:
             from utils.constraint_logger import ConstraintLogger
        except ImportError:
             from backend.utils.constraint_logger import ConstraintLogger

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
            # NEW: Strict Data Normalization Layer
            # from .data_normalizer import DataNormalizer, NormalizationError (Moved to top)
            
            print("Running Data Normalization Layer...")
            try:
                normalizer = DataNormalizer(self.context)
                self.context = normalizer.normalize()
            except NormalizationError as ne:
                print(f"CRITICAL NORMALIZATION ERROR: {ne}")
                return {
                    "success": False,
                    "stage": "GENERATION_FAILED",
                    "errorType": "NormalizationError",
                    "message": str(ne),
                    "details": "Data contains inconsistencies that prevent safe generation."
                }
                
            self._run_stage("INPUT_NORMALIZATION", self._validate_and_normalize_inputs)
            
            print("GLOBAL_SETUP COMPLETED")
            
            # 2. Global Feasibility Check (optional, but good practice)
            # self._run_stage("FEASIBILITY_CHECK", self._run_feasibility_check)
            
            all_timetables = {}
            failures = {} # Map of ClassID -> Error Reason
            
            total_slots_filled = 0
            
            print("GENERATION LOOP STARTED")
            print("Starting Multi-Class Generation Loop...")
            
            # --- GLOBAL STATE (Shared across classes) ---
            self.constraint_logger = ConstraintLogger()
            global_state = TimetableState(self.context, self.load_manager, logger=self.constraint_logger)
            
            # 3. Main Generation Loop
            expected_class_count = len(self.normalized_classes)
            # ... debug prints ...
            
            # We want to iterate AND use the same state
            total_slots_filled = 0
            
            with open('backend_debug_inputs.json', 'w') as f:
                 import json
                 subjects_debug = self.context.get('smartInputData', {}).get('subjects', [])
                 json.dump({ 
                     "normalized_classes": self.normalized_classes,
                     "subjects_sample": subjects_debug[:20], # First 20 to check parsing
                     "se_subjects": [s for s in subjects_debug if s.get('year') in ['SE', 'Second Year', 'II']]
                 }, f, default=str)
            
            # STRICT GENERATION LOOP
            expected_ids = set(c['id'] for c in self.normalized_classes)
            generated_ids = set()
            
            for class_obj in self.normalized_classes:
                class_key = class_obj['id']
                year = class_obj['year']
                division = class_obj['division']
                
                print(f"\n==========================================")
                print(f"Generating Timetable for: {class_key}")
                print(f"==========================================")

                try:
                    # TASK: ENFORCE GLOBAL RECESS
                    # Recess is now implicitly handled by schedulable_slots
                    # global_state.block_recess_for_class(year, division) -> REMOVED


                    # TASK 3: VERIFY DATA EXISTS BEFORE TRYING
                    subjects = self.context.get('smartInputData', {}).get('subjects', [])
                    class_subjects = [
                        s for s in subjects 
                        if s.get('year') == year 
                        and (not s.get('division') or s.get('division') == division)
                    ]
                    
                    print(f"DATA CHECK: {class_key} has {len(class_subjects)} subjects.")
                    if not class_subjects:
                        # TASK 4: REMOVE SILENT SKIPS - FAIL LOUDLY
                        raise RuntimeError(f"CRITICAL DATA ERROR: No subjects found for {class_key}. Cannot generate.")

                    # FIREWALL: Pass global_state
                    class_result = self.generate_single_class_timetable(class_obj, global_state)
                    
                    # TASK 4: CHECK RESULT
                    # generate_single_class_timetable now returns True (labs-only phase signal).
                    # Full timetable dict (labs + theory) is built in the CP-SAT phase below.
                    if not class_result:
                         raise RuntimeError(f"SCHEDULING FAILURE: Engine returned empty result for {class_key} despite valid data. Constraints might be impossible.")

                    # Register class as successfully processed (labs done).
                    # all_timetables is rebuilt after CP-SAT fills theory slots.
                    if year not in all_timetables:
                        all_timetables[year] = {}
                    all_timetables[year][division] = {"timetable": {}}  # placeholder
                    
                    generated_ids.add(class_key)
                    print(f"LABS DONE: {class_key} (theory scheduled globally via CP-SAT)")
                    
                    with open('backend_generation_progress.log', 'a') as f:
                        f.write(f"SUCCESS {class_key}\n")

                except Exception as class_err:
                    import traceback
                    traceback.print_exc()
                    error_msg = f"FAILED to generate {class_key}: {str(class_err)}"
                    print(error_msg, flush=True)
                    # TASK 4: DO NOT CONTINUE IF DIVISION FAILS
                    # The user prompt says "Generation FAILS loudly if any division is skipped"
                    # raising here ensures the whole process stops and returns 500.
                    raise RuntimeError(error_msg)
            
            # TASK 5: POST-GENERATION VALIDATION
            missing_divisions = expected_ids - generated_ids
            if missing_divisions:
                raise RuntimeError(f"CRITICAL: The following divisions were SKIPPED: {missing_divisions}")

            # --- PHASE 3: GLOBAL THEORY SCHEDULING (CP-SAT) ---
            # All labs are placed. Now run the CP-SAT model once across all divisions.
            print("\n--- Starting CP-SAT Theory Scheduling (all divisions) ---")
            self.current_stage = "CPSAT_THEORY_SCHEDULING"
            try:
                from .theory_scheduler import TheoryScheduler

                # Link load_manager to global_state so pick_teacher() can check availability
                self.load_manager._state = global_state

                theory_sched = TheoryScheduler(
                    global_state,
                    self.load_manager,
                    self.context
                )
                cpsat_result = theory_sched.schedule()

                print(
                    f"[Scheduler] CP-SAT: {cpsat_result['status']} | "
                    f"{cpsat_result['time_ms']:.0f}ms | "
                    f"gaps={cpsat_result['gaps']} | "
                    f"incomplete={len(cpsat_result['incomplete'])}"
                )
                if cpsat_result["incomplete"]:
                    for div, subj, placed, needed in cpsat_result["incomplete"]:
                        print(f"  WARNING: {div} {subj}: {placed}/{needed} lectures placed")
            except Exception as cpsat_err:
                import traceback
                print(f"[Scheduler] CP-SAT theory scheduling failed: {cpsat_err}")
                traceback.print_exc()
                # Non-fatal — labs are still in state; generation continues

            # --- Rebuild all_timetables from global_state (now includes theory) ---
            all_timetables = {}
            for class_obj in self.normalized_classes:
                year = class_obj['year']
                division = class_obj['division']
                all_raw_slots_class = [
                    s for s in global_state.get_filled_slots()
                    if isinstance(s, dict)
                    and s.get('year') == year
                    and s.get('division') == division
                ]
                if year not in all_timetables:
                    all_timetables[year] = {}
                all_timetables[year][division] = {
                    "timetable": self.format_to_canonical(all_raw_slots_class)
                }


            print("\n--- Starting Daily Compaction (No Gaps) ---")
            with open('backend_compaction_trace.log', 'w', encoding='utf-8') as f:
                 f.write("COMPACTION PHASE STARTED\n")
            try:
                from engine.schedule_optimizer import ScheduleOptimizer
                optimizer = ScheduleOptimizer(global_state)
                
                years = self.context.get('branchData', {}).get('academicYears', [])
                divisions_map = self.context.get('branchData', {}).get('divisions', {})
                # Safely get working days
                bd_days = self.context.get('branchData', {}).get('workingDays', [])
                days = bd_days if isinstance(bd_days, list) and bd_days else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                
                for year in years:
                    divisions = divisions_map.get(year, [])
                    for division in divisions:
                        for day in days:
                            try:
                                optimizer.compact_daily_schedule(year, division, day)
                            except Exception as e:
                                print(f"Error compacting {year}-{division} on {day}: {str(e).encode('ascii', errors='ignore').decode('ascii')}")
                                # Don't crash global gen
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Warning: Compaction failed or module missing: {e}")

            # 4. Final Validation / Partial Success
            # SAFE GUARD: unexpected structure
            if isinstance(all_timetables, dict):
                 generated_count = sum(len(divs) for divs in all_timetables.values())
            else:
                 generated_count = 0
                 print(f"CRITICAL: all_timetables is not a dict! ({type(all_timetables)})")
            print(f"\nGeneration Complete. Generated {generated_count}/{expected_class_count} classes.")
            print(f"Failures: {len(failures)}")
            
            # 5. Populate Statistics & Raw Data
            total_slots_filled = 0
            raw_all_slots = []
            for year_data in all_timetables.values():
                for div_data in year_data.values():
                    tt = div_data.get('timetable', {})
                    if isinstance(tt, dict):
                        for day_slots in tt.values():
                            raw_all_slots.extend(day_slots)
                            total_slots_filled += len(day_slots)

            # TASK 5: STRICT GLOBAL FAILURE & TASK 1 LOGGING
            print(f"ALLOCATED SESSIONS COUNT: {total_slots_filled}")
            
            # AGGREGATE INTERNAL RAW SLOTS (For Validation)
            all_internal_slots = []
            if global_state:
                 all_internal_slots = global_state.get_filled_slots()
            
            if raw_all_slots:
                 print(f"SAMPLE SESSION: {raw_all_slots[0]}")
            else:
                 print("SAMPLE SESSION: None")

            if total_slots_filled == 0:
                  print("WARNING: No lectures placed during initialization. Constraint logic might be too strict.")
                  # Instead of crashing, return a failure report with analysis
                  return self._generate_failure_report()
                 
            # GENERATE TIME-BASED LAYOUT
            day_layout = []
            try:
                # RELIABLE IMPORT: Path already setup at top of function
                # RELIABLE IMPORT: Path already setup at top of function
                from utils.time_utils import generate_day_structure 
                from utils.constraint_logger import ConstraintLogger
                
                # Fetch Structure
                topo = generate_day_structure(self.context.get('branchData', {}))
                raw_layout = topo['layout']
                
                for item in raw_layout:
                    if item['is_recess']:
                         day_layout.append({
                             "type": "recess",
                             "index": -1,
                             "label": "Recess" # or item['label']
                         })
                    else:
                         idx = item.get('slot_index', 0)
                         day_layout.append({
                             "type": "lecture",
                             "index": idx + 1, # Visual Index 1-based
                             "label": item['label']
                         })
                    # current_visual_idx not needed

            except Exception as e:
                # LOG ERROR
                with open('backend_time_layout_error.log', 'w') as f:
                    import traceback
                    f.write(f"ERROR: {str(e)}\n\n{traceback.format_exc()}")
                day_layout = []
            
            print(f"DEBUG: Generated Day Layout: {day_layout}")

            # DEBUG: DUMP FINAL STRUCTURE
            try:
                import json
                # Use a custom encoder for datetime/sets if necessary
                class SetEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, set): return list(obj)
                        if isinstance(obj, datetime): return str(obj)
                        return super().default(obj)

                with open('backend_final_structure.json', 'w') as f:
                    json.dump(all_timetables, f, indent=2, cls=SetEncoder)
            except Exception as e:
                print(f"Failed to dump structure: {e}")

            # STEP 1: HARD INSTRUMENTATION
            print("==== FINAL ALLOCATION DEBUG ====")
            print("Total divisions:", len(all_timetables))
            total_slots_filled = 0 # RESET for final count
            for year, divs in all_timetables.items():
                for div, wrapper in divs.items():
                    table = wrapper.get('timetable', {})
                    non_empty_count = 0
                    for d in table:
                        # table[d] is now a DICT of slots (canonical) or LIST?
                        # format_to_canonical returns { Day: { Slot: [List of entries] } }
                        # So table[d] is a dict of slots.
                        # We count entries.
                        slots_map = table[d]
                        if isinstance(slots_map, dict):
                            for s_key, entries in slots_map.items():
                                if entries:
                                    # Filter out BREAK and RECESS
                                    real_entries = [e for e in entries if e.get('type') not in ['BREAK', 'RECESS']]
                                    if real_entries: 
                                        non_empty_count += 1
                                        total_slots_filled += 1
                        elif isinstance(slots_map, list): # Legacy check
                            real_entries = [e for e in slots_map if e.get('type') not in ['BREAK', 'RECESS']]
                            non_empty_count += len(real_entries)
                            total_slots_filled += len(real_entries)
                            
                    print(f"Division: {year}-{div} | Non-empty slots: {non_empty_count}")

            # STEP 7: FINAL HARD ASSERTION
            if total_slots_filled == 0:
                 error_msg = ("FATAL: Allocation failed. Grid initialized but no sessions placed. "
                              "Constraint Logic might have rejected everything.")
                 print(f"ERROR: {error_msg}")
                 if hasattr(self, 'constraint_logger'):
                     print(self.constraint_logger.get_report())
                 raise RuntimeError(error_msg)

            # FIX 6: build gap report from raw (pre-visual-index) slots
            gap_report = {}
            try:
                gap_report = self.build_gap_report(raw_all_slots)
                print(f"[GapReport] {gap_report['summary']}")
            except Exception as _gr_err:
                print(f"Warning: build_gap_report failed: {_gr_err}")

            # --- TEACHER TIMETABLE GENERATION ---
            teacher_timetables = {}
            try:
                from .teacher_timetable import TeacherTimetableGenerator
                tt_gen = TeacherTimetableGenerator(global_state, self.context)
                teacher_timetables = tt_gen.generate()
                print(f"[TeacherTT] Generated schedules for {len(teacher_timetables)} teachers.")
            except Exception as _tt_err:
                import traceback
                print(f"Warning: teacher_timetable generation failed: {_tt_err}")
                traceback.print_exc()

            return {
                "success": True,  
                "stage": "COMPLETED",
                "timetables": all_timetables,
                "teacher_timetables": teacher_timetables,
                "failures": failures,
                "raw_timetable": raw_all_slots, 
                "internal_slots": all_internal_slots, # NEW for Validation
                "qualityScore": 100, 
                "config": {
                    "recess_slot": self.state.recess_slot,
                    "total_slots": self.state.total_slots
                },
                "dayLayout": day_layout,
                "message": f"Generated {generated_count}/{expected_class_count} classes. {len(failures)} failures.",
                "constraintReport": self.constraint_logger.get_report(),
                # FIX 6: gap report surfaced in API response
                "gapReport": gap_report,
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
            
            # LOG TRACEBACK TO FILE
            try:
                with open('backend_startup_error.log', 'w') as f:
                    f.write(f"TIMESTAMP: {str(datetime.now())}\n")
                    f.write(f"ERROR: {str(e)}\n")
                    f.write("TRACEBACK:\n")
                    f.write(tb)
            except:
                pass

            # Check if it's a structured RuntimeError
            if isinstance(e, RuntimeError) and e.args and isinstance(e.args[0], dict):
                 err_dict = e.args[0]
                 return {
                     "success": False,
                     "stage": err_dict.get('stage', 'GENERATION_FAILED'),
                     "errorType": err_dict.get('type', 'RuntimeError'),
                     "message": err_dict.get('error', str(e)),
                     "details": str(err_dict),
                     "traceback": tb
                 }

            return {
                "success": False,
                "stage": "GENERATION_FAILED",
                "errorType": type(e).__name__,
                "message": str(e),
                "details": "Critical error before generation loop started.",
                "traceback": tb
            }

    def generate_single_class_timetable(self, class_obj, global_state=None):
        """
        Generate timetable for a Single Class (Year + Division).
        Accepts optional global_state for shared constraints.

        NOTE: Theory scheduling is NO LONGER done here.  CP-SAT schedules
        all divisions simultaneously after all labs are placed.  This method
        now handles LABS ONLY.  The caller (generate()) runs theory globally.
        """
        # 1. Initialize State (Shared or Fresh)
        if global_state:
            class_state = global_state
        else:
            # Fallback for individual testing
            class_state = TimetableState(self.context, self.load_manager)
        
        # 2. Initialize Lab Scheduler only
        lab_scheduler = LabScheduler(class_state, self.context)
        
        # 3. Schedule Labs
        self.current_stage = f"LAB_SCHEDULING_{class_obj['id']}"
        try:
            success_labs = lab_scheduler.schedule_class_labs(class_obj)
            if not success_labs:
                print(f"  Lab scheduling returned False for {class_obj['id']}")
        except Exception as e:
            print(f"  Lab scheduling CRASHED for {class_obj['id']}: {e}")
            print(f"  Proceeding with Theory only (Partial Generation).")
            success_labs = False
            
        # STRICT VALIDATION: Ensure all batches covered
        subjects = self.context.get('smartInputData', {}).get('subjects', [])
        lab_subjects = [
            s for s in subjects 
            if s.get('year') == class_obj['year'] 
            and (not s.get('division') or s.get('division') == class_obj['division'])
            and (s.get('isPractical') or s.get('type') == 'Practical')
        ]
        
        assigned_slots = class_state.get_filled_slots()
        batches = class_obj.get('batches', ["B1", "B2", "B3"])
        
        for batch in batches:
            batch_labs = set()
            for slot in assigned_slots:
                if slot.get('batch') == batch and slot.get('type') == 'LAB':
                     batch_labs.add(slot.get('subject'))
            for lab in lab_subjects:
                if lab['name'] not in batch_labs:
                     error_msg = f"WARNING: Batch {batch} in {class_obj['id']} missing lab {lab['name']}"
                     print(f"    {error_msg}")

        # Theory scheduling is deferred to the global CP-SAT call in generate().
        # Return labs-only snapshot (theory slots will be added to global_state later).
        # We return the full global state view filtered to this class; after theory
        # runs globally, format_to_canonical() will include both lab and theory slots.
        all_raw_slots = class_state.get_filled_slots()
        print(f"DEBUG: {class_obj['id']} LAB slots after lab phase: {len([s for s in all_raw_slots if s.get('year') == class_obj['year'] and s.get('division') == class_obj['division']])}")

        # Return placeholder — final timetable built in generate() after CP-SAT runs
        return True  # Signal success; actual formatting happens in generate()

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
            
            clean_year = year.strip() 
                
            divs = divisions_map.get(year, [])
            if not isinstance(divs, list):
                raise ValueError(f"Divisions for {year} must be list, got {type(divs)}")
                
            for div in divs:
                if not isinstance(div, str):
                    raise ValueError(f"Division must be string, got {type(div)}: {div}")
                
                clean_div = div.strip()
                    
                self.normalized_classes.append({
                    "id": f"{clean_year}-{clean_div}",
                    "year": clean_year,
                    "division": clean_div,
                    "batches": ["B1", "B2", "B3"] # Defaulting batches for now
                })
                
    def _run_feasibility_check(self):
        result = self.feasibility.verify()
        if not result['valid']:
             raise ValueError(f"Feasibility Failed: {result.get('reason')}")

    def _get_balanced_room(self, class_id, available_rooms):
        """
        Assign a room to a class using a 'Least Used' strategy.
        Once assigned, the class keeps the room for consistency.
        """
        # 1. Check if already assigned
        if class_id in self.room_assignments:
            return self.room_assignments[class_id]
            
        if not available_rooms:
            return None
            
        # 2. Find least used room
        # We start with random shuffle to break ties randomly, avoiding "Room A" always winning ties
        import random
        # Create a copy to shuffle
        candidates = list(available_rooms)
        random.shuffle(candidates)
        
        # Find room with minimum current usage
        best_room = min(candidates, key=lambda r: self.room_counts[r])
        
        # 3. Assign and Update
        self.room_assignments[class_id] = best_room
        self.room_counts[best_room] += 1
        
        return best_room

    def format_to_canonical(self, slots_list):
        """
        Convert list of slots to the canonical format:
        {
            "Monday": [ {...}, ... ],  # List of slots
            "Tuesday": [ ... ]
        }
        
        FIX: Returns LIST per day (not dict) to match Frontend 'transformToGrid' 
        and Backend 'history' expectations.
        Also maps internal 0-based indices to 1-based Visual Indices.
        """
        canonical_days = {}
        
        # Calculate recess configuration for mapping
        try:
            from utils.time_utils import calculate_time_slots
            time_config = calculate_time_slots(self.context.get('branchData', {}))
            recess_slot = time_config.get('recess_slot')
        except:
            recess_slot = None
            
        for slot in slots_list:
            day = slot['day']
            raw_slot_idx = int(slot['slot'])
            
            # --- SLOT MAPPING LOGIC (0-based -> 1-based Visual) ---
            # Strictly use 1-based indexing to match Day Layout
            visual_idx = raw_slot_idx + 1
                
            # Filter keys for clean output
            clean_slot = {k: v for k, v in slot.items() if k not in ['id', 'isPractical']}
            
            # OVERWRITE SLOT WITH VISUAL INDEX
            clean_slot['slot'] = visual_idx
            if 'id' in slot: clean_slot['id'] = slot['id']
            if 'isPractical' in slot: clean_slot['isPractical'] = slot['isPractical']
            
            # DEFAULT ROOM ASSIGNMENT (THEORY)
            if 'room' not in clean_slot or not clean_slot['room']:
                assigned_room = None
                try:
                    branch_data = self.context.get('branchData', {})
                    all_classrooms = branch_data.get('classrooms', [])
                    if isinstance(all_classrooms, dict):
                         temp = []
                         for v in all_classrooms.values():
                             if isinstance(v, list): temp.extend(v)
                         all_classrooms = list(set(temp))
                    if not all_classrooms:
                        all_classrooms = branch_data.get('rooms', [])
                        
                    if not all_classrooms:
                        all_classrooms = branch_data.get('rooms', [])
                        
                    class_id = f"{slot['year']}-{slot['division']}"
                    
                    # SMART BALANCING: Use least-used room strategy
                    if isinstance(all_classrooms, list) and len(all_classrooms) > 0:
                        rooms_list = [r.get('name') if isinstance(r, dict) else r for r in all_classrooms]
                        assigned_room = self._get_balanced_room(class_id, rooms_list)
                    else:
                        assigned_room = f"Classroom-{class_id}"

                except Exception as e:
                    print(f"Room Assignment Error: {e}")
                    pass
                
                clean_slot['room'] = assigned_room if assigned_room else f"Classroom-{slot['year']}-{slot['division']}"

            if 'type' not in clean_slot:
                clean_slot['type'] = 'THEORY'
                
            # Append to Day List
            if day not in canonical_days:
                canonical_days[day] = []
            canonical_days[day].append(clean_slot)
            
        return canonical_days


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
             
             # CLEAN STRINGS
             if isinstance(s.get('year'), str): s['year'] = s['year'].strip()
             if isinstance(s.get('division'), str): s['division'] = s['division'].strip()
             if isinstance(s.get('name'), str): s['name'] = s['name'].strip()
             if isinstance(s.get('type'), str): s['type'] = s['type'].strip()
                 
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
                print(f"    Warning: Dropping duplicate subject input: {s.get('name')} ({s.get('year')})")
        
        smart_input['subjects'] = cleaned_subjects
        subjects = cleaned_subjects # Update reference for further checks
        
        # VALIDATION: Check if Labs > Working Days
        # If One-Lab-Per-Day rule is active, Labs > Days is IMPOSSIBLE.
        daily_lab_limit = 1 # Rule #7
        working_days = branch_data.get('workingDays', [])
        num_days = len(working_days) if isinstance(working_days, list) else 5
        
        # Count labs per year
        # Count labs per (Year, Division)
        lab_counts = {}
        for s in subjects:
            if s.get('isPractical') or s.get('type') == 'Practical':
                y = s.get('year')
                d = s.get('division')
                key = (y, d)
                lab_counts[key] = lab_counts.get(key, 0) + 1
                
        for (year, div), count in lab_counts.items():
            if count > num_days * daily_lab_limit:
                msg = f"Class {year}-{div} has {count} labs but only {num_days} working days. Rule 'One Lab/Batch/Day' makes this impossible."
                print(f"CRITICAL CONFIG ERROR: {msg}")
                # We raise error to stop generation immediately and inform user
                raise ValueError(msg)
                 
        # Validate Teachers
        teachers = smart_input.get('teachers', [])
        if not isinstance(teachers, list):
             raise TypeError(f"teachers must be a list, got {type(teachers)}")
        for idx, t in enumerate(teachers):
             if not isinstance(t, dict):
                 raise TypeError(f"Teacher at index {idx} must be a dict, got {type(t)}: {t}")
                 
             if isinstance(t.get('name'), str): t['name'] = t['name'].strip()
             
             # Validate Login Time format if present
             if t.get('loginTime'):
                 lt = t.get('loginTime')
                 import re
                 if not re.match(r'^\d{1,2}:\d{2}(?:\s?[AaPp][Mm])?$', str(lt)):
                     print(f"    Warning: Invalid loginTime format '{lt}' for teacher {t.get('name')}. Expected HH:MM or HH:MM AM/PM.")
                 
    def _generate_slot_id(self, slot):
        """Generate unique ID for a slot"""
        return f"{slot['day']}_{slot['slot']}_{slot['year']}_{slot['division']}_{slot.get('batch', '')}"

    
    def build_gap_report(self, raw_slots):
        """
        FIX 6: Compute a structured gap analysis over the completed timetable.

        Produces two sections:
          - perDivision: for each (year, division, day) how many internal
                         gap slots exist between the first and last lecture.
          - perTeacher:  for each (teacher, day) how many idle slots fall
                         between their first and last teaching slot.

        Returns:
            dict with keys:
              'totalStudentGaps'   : int   – sum of all division-day gaps
              'totalTeacherGaps'   : int   – sum of all teacher-day idle slots
              'perDivision'        : list of dicts {year, division, day, gaps}
              'perTeacher'         : list of dicts {teacher, day, idleSlots}
              'summary'            : human-readable string
        """
        try:
            from utils.gap_utils import count_gaps_in_day, count_teacher_gaps_in_day
        except ImportError:
            try:
                from backend.utils.gap_utils import count_gaps_in_day, count_teacher_gaps_in_day
            except ImportError:
                # Inline fallback so this method never hard-crashes
                def count_gaps_in_day(lst):
                    occ = [i for i, v in enumerate(lst) if v is not None]
                    if len(occ) < 2: return 0
                    return sum(1 for i in range(occ[0] + 1, occ[-1]) if lst[i] is None)
                count_teacher_gaps_in_day = count_gaps_in_day

        from collections import defaultdict

        # ---- Build per-division-day and per-teacher-day grids ----
        div_grid     = defaultdict(dict)     # {(year, div, day): {slot_idx: slot}}
        teacher_grid = defaultdict(dict)     # {(teacher, day):   {slot_idx: slot}}

        for slot in raw_slots:
            year    = slot.get('year')
            div     = slot.get('division')
            day     = slot.get('day')
            teacher = slot.get('teacher')
            # Use raw 0-based index (internal_slots list); visual index is already +1 in
            # format_to_canonical but raw_all_slots has the pre-conversion values.
            idx = int(slot.get('slot', 0))

            if year and div and day:
                div_grid[(year, div, day)][idx] = slot

            if teacher and teacher != 'TBA' and day:
                teacher_grid[(teacher, day)][idx] = slot

        # ---- Division gaps ----
        per_division = []
        total_student_gaps = 0

        for (year, div, day), slot_map in sorted(div_grid.items()):
            if not slot_map:
                continue
            max_idx  = max(slot_map.keys()) + 1
            day_list = [slot_map.get(i) for i in range(max_idx)]
            gaps = count_gaps_in_day(day_list)
            total_student_gaps += gaps
            if gaps > 0:
                per_division.append({
                    "year": year, "division": div, "day": day, "gaps": gaps
                })

        # ---- Teacher gaps ----
        per_teacher = []
        total_teacher_gaps = 0

        for (teacher, day), slot_map in sorted(teacher_grid.items()):
            if not slot_map:
                continue
            max_idx  = max(slot_map.keys()) + 1
            day_list = [slot_map.get(i) for i in range(max_idx)]
            idle = count_teacher_gaps_in_day(day_list)
            total_teacher_gaps += idle
            if idle > 0:
                per_teacher.append({
                    "teacher": teacher, "day": day, "idleSlots": idle
                })

        summary = (
            f"{total_student_gaps} student gap-slot(s) across "
            f"{len(per_division)} division-day(s); "
            f"{total_teacher_gaps} teacher idle-slot(s) across "
            f"{len(per_teacher)} teacher-day(s)."
        )

        return {
            "totalStudentGaps": total_student_gaps,
            "totalTeacherGaps": total_teacher_gaps,
            "perDivision": per_division,
            "perTeacher":  per_teacher,
            "summary":     summary
        }

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
            "stage": "GENERATION_FAILED",
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
                "slotsFilled": len(self.state.slots)
            }
        }
