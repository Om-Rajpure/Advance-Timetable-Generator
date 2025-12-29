"""
History API Routes

Flask routes for timetable version history operations.
"""

from flask import Blueprint, request, jsonify
from history.version_store import VersionStore
from history.restore_manager import RestoreManager
from history.history_service import HistoryService

# Create blueprint
history_bp = Blueprint('history', __name__, url_prefix='/api/history')

# Initialize services
version_store = VersionStore()
restore_manager = RestoreManager(version_store)
history_service = HistoryService(version_store, restore_manager)


@history_bp.route('/versions', methods=['GET'])
def get_versions():
    """
    Get all versions for a branch.
    
    Query params:
        branchId: Branch ID (required)
        limit: Maximum number of versions (default: 50)
        action: Filter by action type (optional)
    
    Response:
    {
        "success": bool,
        "versions": [...],
        "stats": {...},
        "totalCount": int
    }
    """
    try:
        branch_id = request.args.get('branchId')
        
        if not branch_id:
            return jsonify({'error': 'branchId is required'}), 400
        
        limit = int(request.args.get('limit', 50))
        action_filter = request.args.get('action')
        
        timeline = history_service.get_version_timeline(
            branch_id=branch_id,
            limit=limit,
            action_filter=action_filter
        )
        
        return jsonify({
            'success': True,
            **timeline
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/version/<version_id>', methods=['GET'])
def get_version(version_id):
    """
    Get a specific version with full timetable snapshot.
    
    Query params:
        branchId: Branch ID (required)
    
    Response:
    {
        "success": bool,
        "version": {...}
    }
    """
    try:
        branch_id = request.args.get('branchId')
        
        if not branch_id:
            return jsonify({'error': 'branchId is required'}), 400
        
        version = version_store.get_version(branch_id, version_id)
        
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        return jsonify({
            'success': True,
            'version': version
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/restore', methods=['POST'])
def restore_version():
    """
    Restore a previous timetable version.
    
    Request body:
    {
        "branchId": "branch-123",
        "versionId": "v_abc123",
        "context": {
            "branchData": {...},
            "smartInputData": {...}
        }
    }
    
    Response:
    {
        "success": bool,
        "canRestore": bool,
        "timetable": [...] (if successful),
        "validation": {...},
        "version": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        branch_id = data.get('branchId')
        version_id = data.get('versionId')
        context = data.get('context', {})
        
        if not branch_id or not version_id:
            return jsonify({'error': 'branchId and versionId are required'}), 400
        
        if not context.get('branchData') or not context.get('smartInputData'):
            return jsonify({'error': 'context with branchData and smartInputData is required'}), 400
        
        result = restore_manager.restore_version(
            branch_id=branch_id,
            version_id=version_id,
            current_context=context
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/compare', methods=['POST'])
def compare_versions():
    """
    Compare two versions.
    
    Request body:
    {
        "branchId": "branch-123",
        "versionId1": "v_abc123",
        "versionId2": "v_def456"
    }
    
    Response:
    {
        "success": bool,
        "version1": {...},
        "version2": {...},
        "diff": {...},
        "summaryText": str,
        "qualityChange": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        branch_id = data.get('branchId')
        version_id_1 = data.get('versionId1')
        version_id_2 = data.get('versionId2')
        
        if not all([branch_id, version_id_1, version_id_2]):
            return jsonify({'error': 'branchId, versionId1, and versionId2 are required'}), 400
        
        result = history_service.generate_diff_summary(
            branch_id=branch_id,
            version_id_old=version_id_1,
            version_id_new=version_id_2
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/version/<version_id>', methods=['DELETE'])
def delete_version(version_id):
    """
    Delete a version (admin only).
    
    Query params:
        branchId: Branch ID (required)
    
    Response:
    {
        "success": bool,
        "message": str
    }
    """
    try:
        branch_id = request.args.get('branchId')
        
        if not branch_id:
            return jsonify({'error': 'branchId is required'}), 400
        
        # TODO: Add authentication check here
        # For now, allow all deletions
        
        success = version_store.delete_version(branch_id, version_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Version deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Version not found'
            }), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
