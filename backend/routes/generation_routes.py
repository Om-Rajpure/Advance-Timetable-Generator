"""
Timetable Generation API Routes

Flask routes for timetable generation operations.
"""

from flask import Blueprint, request, jsonify
import json
from engine.scheduler import TimetableScheduler
from engine.optimizer import TimetableOptimizer
from history.history_service import HistoryService

# Create blueprint
generation_bp = Blueprint('generation', __name__, url_prefix='/api/generate')

# Initialize history service
history_service = HistoryService()


@generation_bp.route('/full', methods=['POST'])
def generate_full_timetable():
    """
    Generate a complete timetable from scratch.
    Safe execution wrapper ensures no crashes.
    """
    print("GENERATION STARTED") # Trace marker
    
    try:
        # 1. Safe Payload Extraction
        try:
            data = request.get_json(force=True)
        except Exception as e:
            err = {"success": False, "reason": "INVALID_JSON", "details": str(e)}
            with open('backend_last_error.json', 'w') as f: json.dump(err, f)
            print(f"❌ JSON Parse Error: {e}")
            return jsonify(err), 400

        if not data or 'branchData' not in data or 'smartInputData' not in data:
            err = {"success": False, "reason": "INVALID_PAYLOAD", "details": "Missing required data fields (branchData or smartInputData)"}
            with open('backend_last_error.json', 'w') as f: json.dump(err, f)
            print("❌ Missing branchData or smartInputData")
            return jsonify(err), 400
            
        # STRICT Deep Validation
        bd = data['branchData']
        si = data['smartInputData']
        
        if not bd.get('academicYears') or not isinstance(bd['academicYears'], list):
             err = {"success": False, "reason": "INVALID_CONFIG", "details": f"academicYears must be a non-empty list. Got: {type(bd.get('academicYears'))} - {bd.get('academicYears')}"}
             with open('backend_last_error.json', 'w') as f: json.dump(err, f)
             return jsonify(err), 400
             
        if not si.get('subjects') or not si.get('teachers'):
             err = {"success": False, "reason": "NO_DATA", "details": "Subjects and Teachers lists cannot be empty"}
             with open('backend_last_error.json', 'w') as f: json.dump(err, f)
             return jsonify(err), 400

        print(f"RAW PAYLOAD KEYS: {list(data.keys())}")
        print(f"Deep Validation: {len(bd.get('academicYears', []))} Years, {len(si.get('subjects', []))} Subjects")
        
        # 3. Execution
        context = {
            "branchData": data['branchData'],
            "smartInputData": data['smartInputData']
        }
        
        # Initialize Scheduler (Fresh Instance)
        scheduler = TimetableScheduler(context, max_iterations=data.get('maxIterations', 10000))
        
        # Run Generation
        result = scheduler.generate()
        
        # 4. Strict Response Contract
        
        # 4. Response Guarantee
        # Even if success=False from global setup, we might want to return that as 400.
        # But partial success (success=True with failures) is 200.
        
        if not result.get('success'):
            print(f"❌ Generation Global Failure: {result.get('message')}")
            with open('backend_last_error.json', 'w') as f: json.dump(result, f, default=str)
            return jsonify(result), 400 
            
        all_timetables = result.get('timetables', {})
        failures = result.get('failures', {})
        
        # Verify if we have ANYTHING to show
        if not all_timetables and not failures:
             err = {"success": False, "reason": "NO_DATA_GENERATED", "details": "Scheduler returned success but no data."}
             with open('backend_last_error.json', 'w') as f: json.dump(err, f)
             print("❌ No timetables AND no failures recorded?")
             return jsonify(err), 400
             
        # 5. Soft Post-Gen Validation
        from engine.validator import TimetableValidator, ValidationError
        validator = TimetableValidator(context)
        validation_errors = []
        
        # Validate PER DIVISION that succeeded
        for div_key, timetable in all_timetables.items():
            try:
                validator._validate_division(div_key, timetable)
            except ValidationError as ve:
                print(f"⚠️ Validation Warning for {div_key}: {ve.reason}")
                # SOFT FAIL: Add to errors but keep timetable
                validation_errors.append({
                    "division": div_key,
                    "reason": ve.reason,
                    "details": ve.details
                })
                # We do NOT remove the timetable. User wants to see what was generated.
        
        # Add global validation errors to result
        result['validationErrors'] = validation_errors
        
        if validation_errors:
            print(f"⚠️ Completing with {len(validation_errors)} validation warnings.")
        else:
            print("✅ Generation & Validation Clean.")
            
        # ALWAYS RETURN 200 for partial/full success
        return jsonify(result), 200

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("❌ CRITICAL SERVER CRASH TRACEBACK:")
        print(tb)
        print(f"❌ CRITICAL SERVER CRASH MESSAGE: {str(e)}")
        
        crash_info = {
            "success": False,
            "stage": "SERVER_CRASH",
            "reason": "INTERNAL_SERVER_ERROR",
            "details": str(e),
            "traceback": tb
        }
        try:
            with open('backend_last_crash.json', 'w') as f: json.dump(crash_info, f, default=str)
        except:
            pass 
            
        return jsonify(crash_info), 500


@generation_bp.route('/partial', methods=['POST'])
def generate_partial_timetable():
    """
    Regenerate a specific year/division.
    
    Request body:
    {
        "existingTimetable": [...],
        "branchData": {...},
        "smartInputData": {...},
        "year": "SE",
        "division": "A"
    }
    
    Response:
    {
        "success": bool,
        "timetable": [...],
        "message": str
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        existing_timetable = data.get('existingTimetable', [])
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        year = data.get('year')
        division = data.get('division')
        
        if not all([branch_data, smart_input, year, division]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Filter out slots for the specified division
        other_slots = [
            slot for slot in existing_timetable
            if not (slot.get('year') == year and slot.get('division') == division)
        ]
        
        # Create context with locked slots
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input,
            "uploadedTimetable": other_slots,
            "lockedSlots": [slot.get('id') for slot in other_slots]
        }
        
        # Generate for this division only
        scheduler = TimetableScheduler(context)
        result = scheduler.generate()
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@generation_bp.route('/optimize', methods=['POST'])
def optimize_timetable():
    """
    Optimize an existing valid timetable.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...},
        "maxIterations": 100 (optional)
    }
    
    Response:
    {
        "success": bool,
        "timetable": [...],
        "qualityScore": float,
        "improvement": float
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        timetable = data.get('timetable')
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        
        if not all([timetable, branch_data, smart_input]):
            return jsonify({"error": "Missing required fields"}), 400
        
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        # Compute initial score
        from constraints.constraint_engine import ConstraintEngine
        engine = ConstraintEngine()
        initial_score = engine.compute_quality_score(timetable, context)
        
        # Optimize
        optimizer = TimetableOptimizer(context)
        max_iterations = data.get('maxIterations', 100)
        optimized = optimizer.optimize(timetable, max_iterations=max_iterations)
        
        # Compute final score
        final_score = engine.compute_quality_score(optimized, context)
        
        # Create version in history
        try:
            version = history_service.auto_create_version(
                timetable=optimized,
                context=context,
                action="Optimization",
                description=f"Timetable optimized - quality improved by {round(final_score - initial_score, 2)} points"
            )
            version_id = version['versionId']
        except Exception as e:
            print(f"Failed to create version: {e}")
            version_id = None
        
        return jsonify({
            "success": True,
            "timetable": optimized,
            "qualityScore": final_score,
            "improvement": final_score - initial_score,
            "initialScore": initial_score,
            "versionId": version_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@generation_bp.route('/status', methods=['GET'])
def generation_status():
    """Get generation engine status and capabilities"""
    return jsonify({
        "available": True,
        "algorithms": ["CSP with Backtracking", "Hill Climbing Optimization"],
        "maxIterations": 10000,
        "features": [
            "Full timetable generation",
            "Partial regeneration",
            "Post-generation optimization",
            "Failure explanation"
        ]
    }), 200
