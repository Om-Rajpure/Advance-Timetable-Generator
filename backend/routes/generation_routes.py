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
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        
        if not branch_data or not smart_input:
            return jsonify({"error": "branchData and smartInputData are required"}), 400
        
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
        
        # Optimize if successful
        if result['success'] and result['valid']:
            optimizer = TimetableOptimizer(context)
            optimized = optimizer.optimize(result['timetable'], max_iterations=100)
            result['timetable'] = optimized
            
            # Recalculate quality score
            from constraints.constraint_engine import ConstraintEngine
            engine = ConstraintEngine()
            result['qualityScore'] = engine.compute_quality_score(optimized, context)
            
            # Create version in history
            try:
                version = history_service.auto_create_version(
                    timetable=optimized,
                    context=context,
                    action="Generation",
                    description=f"Full timetable generated with {len(optimized)} slots"
                )
                result['versionId'] = version['versionId']
            except Exception as e:
                print(f"Failed to create version: {e}")
                # Continue even if version creation fails
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
