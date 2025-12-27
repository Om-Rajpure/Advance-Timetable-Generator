"""
Validation API Routes

Flask routes for timetable validation and optimization operations.
"""

from flask import Blueprint, request, jsonify
from validation.validation_report import ValidationReport

# Create blueprint
validation_bp = Blueprint('validation', __name__, url_prefix='/api/validate')


@validation_bp.route('/full', methods=['POST'])
def validate_full():
    """
    Complete validation without optimization.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "valid": bool,
        "canProceed": bool,
        "qualityScore": {...},
        "resourceAnalysis": {...},
        "explanation": {...}
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
        
        # Generate report without optimization
        report_gen = ValidationReport(context)
        report = report_gen.generate_full_report(timetable, optimize=False)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@validation_bp.route('/optimize', methods=['POST'])
def validate_and_optimize():
    """
    Complete validation WITH optimization.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...},
        "maxIterations": 50 (optional)
    }
    
    Response:
    {
        "timetable": [...],  // Optimized version
        "validation": {...},
        "qualityScore": {...},
        "resourceAnalysis": {...},
        "optimization": {...},
        "explanation": {...},
        "canProceed": bool
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
        
        # Generate report with optimization
        report_gen = ValidationReport(context)
        report = report_gen.generate_full_report(timetable, optimize=True)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@validation_bp.route('/quick', methods=['POST'])
def validate_quick():
    """
    Quick validation check (score + pass/fail only).
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "valid": bool,
        "canProceed": bool,
        "score": float,
        "grade": str,
        "message": str
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
        
        #Generate quick report
        report_gen = ValidationReport(context)
        result = report_gen.generate_quick_report(timetable)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@validation_bp.route('/metrics', methods=['POST'])
def get_metrics_only():
    """
    Get resource utilization metrics only.
    
    Request body:
    {
        "timetable": [...],
        "branchData": {...},
        "smartInputData": {...}
    }
    
    Response:
    {
        "teacherUtilization": {...},
        "labUtilization": float,
        "roomUtilization": float,
        "loadDistribution": {...}
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
        
        # Compute metrics only
        from validation.resource_analysis import ResourceAnalyzer
        analyzer = ResourceAnalyzer(context)
        metrics = analyzer.analyze(timetable)
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
