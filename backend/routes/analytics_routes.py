"""
Analytics API Routes

Flask routes for analytics and insights operations.
"""

from flask import Blueprint, request, jsonify
from analytics.analytics_engine import generate_full_analytics
from analytics.workload_analysis import compute_teacher_workload, generate_workload_insights
from analytics.lab_usage import compute_lab_heatmap, analyze_lab_efficiency
from analytics.free_slots import find_free_slots, analyze_free_capacity
from analytics.bottleneck_detector import detect_bottlenecks, prioritize_bottlenecks

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/full-report', methods=['POST'])
def get_full_report():
    """
    Get complete analytics report for a timetable.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "workload": {...},
        "labUsage": {...},
        "freeSlots": {...},
        "bottlenecks": {...},
        "summary": {...}
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
            return jsonify({"error": "Missing required fields: timetable, branchData, or smartInputData"}), 400
        
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        # Generate full analytics
        analytics = generate_full_analytics(timetable, context)
        
        return jsonify(analytics), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/teacher-workload', methods=['POST'])
def get_teacher_workload():
    """
    Get teacher workload metrics and insights.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "metrics": {...},
        "insights": [...]
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
        
        metrics = compute_teacher_workload(timetable, context)
        insights = generate_workload_insights(metrics)
        
        return jsonify({
            "metrics": metrics,
            "insights": insights
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/lab-usage', methods=['POST'])
def get_lab_usage():
    """
    Get lab usage heatmap and insights.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "metrics": {...},
        "insights": [...]
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
        
        metrics = compute_lab_heatmap(timetable, context)
        insights = analyze_lab_efficiency(metrics)
        
        return jsonify({
            "metrics": metrics,
            "insights": insights
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/free-slots', methods=['POST'])
def get_free_slots():
    """
    Get free slot analysis and capacity insights.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "metrics": {...},
        "insights": [...]
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
        
        metrics = find_free_slots(timetable, context)
        insights = analyze_free_capacity(metrics)
        
        return jsonify({
            "metrics": metrics,
            "insights": insights
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/bottlenecks', methods=['POST'])
def get_bottlenecks():
    """
    Get bottleneck detection and structural issues.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "issues": [...],
        "counts": {...}
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
        
        bottlenecks = detect_bottlenecks(timetable, context)
        prioritized = prioritize_bottlenecks(bottlenecks)
        
        return jsonify({
            "issues": prioritized,
            "counts": {
                "critical": bottlenecks.get('criticalCount', 0),
                "warning": bottlenecks.get('warningCount', 0),
                "info": bottlenecks.get('infoCount', 0)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route('/summary', methods=['POST'])
def get_summary():
    """
    Get quality score and top insights summary.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "qualityScore": int,
        "grade": str,
        "stars": int,
        "topIssues": [...],
        "topStrengths": [...]
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
        
        # Generate full analytics to get summary
        analytics = generate_full_analytics(timetable, context)
        
        return jsonify(analytics.get('summary', {})), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
