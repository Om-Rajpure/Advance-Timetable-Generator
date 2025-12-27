"""
Constraint API Routes

Flask routes for constraint validation and management.
"""

from flask import Blueprint, request, jsonify
from constraints.constraint_engine import ConstraintEngine

# Create blueprint
constraint_bp = Blueprint('constraints', __name__, url_prefix='/api/constraints')

# Initialize constraint engine (singleton)
engine = ConstraintEngine()


@constraint_bp.route('/validate', methods=['POST'])
def validate_timetable():
    """
    Validate a complete timetable against all constraints.
    
    Request body:
    {
        "timetable": [...],  // Array of slot objects
        "context": {
            "branchData": {...},
            "smartInputData": {...}
        }
    }
    
    Response:
    {
        "valid": bool,
        "hardViolations": [...],
        "softViolations": [...],
        "qualityScore": float,
        "summary": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        timetable = data.get('timetable', [])
        context = data.get('context', {})
        
        if not timetable:
            return jsonify({"error": "Timetable is required"}), 400
        
        # Run validation
        result = engine.validate_timetable(timetable, context)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@constraint_bp.route('/check-slot', methods=['POST'])
def check_slot():
    """
    Validate adding a single slot to existing timetable.
    
    Request body:
    {
        "slot": {...},  // Single slot object
        "existingTimetable": [...],
        "context": {...}
    }
    
    Response:
    {
        "valid": bool,
        "violations": [...],
        "conflicts": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        new_slot = data.get('slot')
        existing_timetable = data.get('existingTimetable', [])
        context = data.get('context', {})
        
        if not new_slot:
            return jsonify({"error": "Slot is required"}), 400
        
        # Run slot validation
        result = engine.validate_slot(new_slot, existing_timetable, context)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@constraint_bp.route('/list', methods=['GET'])
def list_constraints():
    """
    Get list of all registered constraints.
    
    Response:
    {
        "hard": [
            {
                "name": "...",
                "description": "...",
                "severity": "HARD",
                "enabled": true
            },
            ...
        ],
        "soft": [...]
    }
    """
    try:
        constraints = engine.list_constraints()
        return jsonify(constraints), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@constraint_bp.route('/enable/<constraint_name>', methods=['POST'])
def enable_constraint(constraint_name):
    """Enable a specific constraint"""
    try:
        success = engine.enable_constraint(constraint_name)
        
        if success:
            return jsonify({
                "message": f"Constraint {constraint_name} enabled",
                "enabled": True
            }), 200
        else:
            return jsonify({
                "error": f"Constraint {constraint_name} not found"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@constraint_bp.route('/disable/<constraint_name>', methods=['POST'])
def disable_constraint(constraint_name):
    """Disable a specific constraint"""
    try:
        success = engine.disable_constraint(constraint_name)
        
        if success:
            return jsonify({
                "message": f"Constraint {constraint_name} disabled",
                "enabled": False
            }), 200
        else:
            return jsonify({
                "error": f"Constraint {constraint_name} not found"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@constraint_bp.route('/quality-score', methods=['POST'])
def compute_quality_score():
    """
    Compute only the quality score for a timetable.
    
    Request body:
    {
        "timetable": [...],
        "context": {...}
    }
    
    Response:
    {
        "qualityScore": float
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        timetable = data.get('timetable', [])
        context = data.get('context', {})
        
        # Compute score
        score = engine.compute_quality_score(timetable, context)
        
        return jsonify({"qualityScore": round(score, 2)}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
