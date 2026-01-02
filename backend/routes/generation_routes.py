"""
Timetable Generation API Routes

Flask routes for timetable generation operations.
"""

from flask import Blueprint, request, jsonify
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
    
    Request body:
    {
        "branchData": {...},
        "smartInputData": {...},
        "maxIterations": 10000 (optional)
    }
    
    Response:
    {
        "success": bool,
        "timetable": [...],
        "valid": bool,
        "qualityScore": float,
        "message": str,
        "stats": {...}
    }
    """
    try:
        # Strict Request Parsing
        try:
            data = request.get_json(force=True)
        except Exception as parse_err:
             print(f"❌ [Generation] JSON Parse Error: {str(parse_err)}")
             return jsonify({
                 "success": False,
                 "stage": "REQUEST_PROCESSING",
                 "reason": "Invalid JSON payload",
                 "details": str(parse_err)
             }), 400

        if not isinstance(data, dict):
            print(f"❌ [Generation] Invalid Payload Type: {type(data)}")
            return jsonify({
                "success": False,
                "stage": "REQUEST_PROCESSING",
                "reason": "Invalid JSON payload structure",
                "details": f"Expected dict, got {type(data).__name__}"
            }), 400
            
        # PROACTIVE LOGGING
        print("Payload received:", data)
        print("BranchData:", data.get("branchData"))
        print("SmartInputData:", data.get("smartInputData"))
        print(f"📥 [Generation] Received Payload Keys: {list(data.keys())}")
        
        # Extract and Validate Components
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        
        print(f"DEBUG branchData type: {type(branch_data)}")
        print(f"DEBUG smartInputData type: {type(smart_input)}")
        
        if not isinstance(branch_data, dict):
             return jsonify({
                 "success": False,
                 "stage": "VALIDATION",
                 "reason": "Invalid branchData",
                 "details": f"Expected dict, got {type(branch_data).__name__}"
             }), 400
             
        if not isinstance(smart_input, dict):
             return jsonify({
                 "success": False,
                 "stage": "VALIDATION",
                 "reason": "Invalid smartInputData",
                 "details": f"Expected dict, got {type(smart_input).__name__}"
             }), 400
        
        # Create context
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        # Initialize scheduler
        max_iterations = data.get('maxIterations', 10000)
        scheduler = TimetableScheduler(context, max_iterations=max_iterations)
        
        # Generate timetable
        result = scheduler.generate()
        
        if result['success'] and result['valid']:
            raw_timetable = result.get('raw_timetable', [])
            print(f"✅ [Generation] Generated timetable size: {len(raw_timetable)}")

            try:
                optimizer = TimetableOptimizer(context)
                # Optimize using raw list
                optimized_raw = optimizer.optimize(raw_timetable, max_iterations=100)
                
                # Re-format to canonical structure
                result['timetable'] = scheduler.format_to_canonical(optimized_raw)
                
                # Recalculate quality score
                from constraints.constraint_engine import ConstraintEngine
                engine = ConstraintEngine()
                result['qualityScore'] = engine.compute_quality_score(optimized_raw, context)
                
                # Update stats with Theory/Lab counts
                theory_count = sum(1 for s in optimized_raw if s.get('type') == 'THEORY')
                lab_count = sum(1 for s in optimized_raw if s.get('type') == 'LAB')
                
                result['stats'].update({
                    "theoryCount": theory_count,
                    "labCount": lab_count,
                    "totalClasses": len(result['timetable'])
                })

                # Create version in history
                version = history_service.auto_create_version(
                    timetable=optimized_raw, # Saving RAW list to history for now (consistency)
                    context=context,
                    action="Generation",
                    description=f"Full timetable generated with {len(optimized_raw)} slots"
                )
                result['versionId'] = version['versionId']
            except Exception as opt_err:
                import traceback
                traceback.print_exc()
                print(f"⚠️ [Generation] Optimization/History error: {opt_err}")
                # Don't fail the whole request
        
        # Step 2: GUARANTEE TIMETABLE EXISTS
        if not result.get('timetable') or not isinstance(result['timetable'], dict):
            return jsonify({
                "success": False,
                "stage": "POST_GENERATION_VALIDATION",
                "reason": "Timetable generation returned empty or invalid structure"
            }), 500

        # Cleanup raw timetable from response to keep it clean (optional)
        if 'raw_timetable' in result:
             del result['raw_timetable']

        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("BACKEND ERROR:", str(e)) # IMPORTANT for debugging
        return jsonify({
            "success": False,
            "stage": "BACKEND_EXCEPTION",
            "reason": str(e),
            "type": type(e).__name__,
            "details": "Unexpected error in generation route."
        }), 500

    # Fallback for ANY execution path that escapes (should not happen with catch-all)
    return jsonify({
        "success": False,
        "reason": "Unhandled execution path reached"
    }), 500


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
