"""
Edit API Routes

Flask routes for timetable editing operations.
"""

from flask import Blueprint, request, jsonify
from edit.validate_edit import validate_slot_edit, validate_timetable_changes
from edit.suggest_fix import suggest_fix, find_alternate_teacher, find_alternate_room
from history.history_service import HistoryService

# Create blueprint
edit_bp = Blueprint('edit', __name__, url_prefix='/api/edit')

# Initialize history service
history_service = HistoryService()


@edit_bp.route('/validate', methods=['POST'])
def validate_edit():
    """
    Validate a slot edit.
    
    Request body:
    {
        "modifiedSlot": {...},
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "valid": bool,
        "conflicts": [...],
        "affectedSlots": [...],
        "severity": "HARD" | "SOFT" | "NONE"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        modified_slot = data.get('modifiedSlot')
        timetable = data.get('timetable')
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        
        if not all([modified_slot, timetable, branch_data, smart_input]):
            return jsonify({"error": "Missing required fields"}), 400
        
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        result = validate_slot_edit(modified_slot, timetable, context)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@edit_bp.route('/suggest-fix', methods=['POST'])
def suggest_fix_endpoint():
    """
    Get auto-fix suggestions for conflicts.
    
    Request body:
    {
        "slot": {...},
        "conflicts": [...],
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "fix": {...} or null,
        "explanation": str,
        "strategy": str
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        slot = data.get('slot')
        conflicts = data.get('conflicts', [])
        timetable = data.get('timetable')
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        
        if not all([slot, timetable, branch_data, smart_input]):
            return jsonify({"error": "Missing required fields"}), 400
        
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        result = suggest_fix(slot, conflicts, timetable, context)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@edit_bp.route('/alternatives', methods=['POST'])
def get_alternatives():
    """
    Get available alternatives for a slot (teachers and rooms).
    
    Request body:
    {
        "slot": {...},
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "teachers": [...],
        "rooms": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        slot = data.get('slot')
        timetable = data.get('timetable')
        branch_data = data.get('branchData')
        smart_input = data.get('smartInputData')
        
        if not all([slot, timetable, branch_data, smart_input]):
            return jsonify({"error": "Missing required fields"}), 400
        
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        # Get alternatives
        teachers = find_alternate_teacher(slot, timetable, context)
        rooms = find_alternate_room(slot, timetable, context)
        
        return jsonify({
            "teachers": teachers,
            "rooms": rooms
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@edit_bp.route('/save', methods=['POST'])
def save_timetable():
    """
    Save edited timetable (after final validation).
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "success": bool,
        "message": str,
        "validation": {...}
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
        
        # Final validation
        validation = validate_timetable_changes(timetable, context)
        
        if not validation['canSave']:
            return jsonify({
                "success": False,
                "message": "Cannot save timetable with hard constraint violations",
                "validation": validation
            }), 400
        
        # TODO: Actually save to database/file
        # For now, just return success
        
        # Create version in history
        try:
            version = history_service.auto_create_version(
                timetable=timetable,
                context=context,
                action="Manual Edit",
                description="Manual edits saved"
            )
            version_id = version['versionId']
        except Exception as e:
            print(f"Failed to create version: {e}")
            version_id = None
        
        return jsonify({
            "success": True,
            "message": "Timetable saved successfully",
            "validation": validation,
            "versionId": version_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
