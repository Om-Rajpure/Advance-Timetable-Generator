from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import json
from datetime import datetime
import uuid


import pdf_parser
from routes.constraint_routes import constraint_bp
from routes.generation_routes import generation_bp
from routes.validation_routes import validation_bp
from routes.edit_routes import edit_bp
from routes.analytics_routes import analytics_bp
from routes.history_routes import history_bp

# Database imports
from database import db
from models import User
from werkzeug.security import generate_password_hash

# Static folder setup - REMOVED for API-only backend
app = Flask(__name__)

# Allow CORS for all domains for development and Vercel deployment
CORS(app, resources={r"/*": {"origins": "*"}})

print(f"Server running on http://localhost:5000. API Only Mode.")

# Register blueprints
# Config
# Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)

# Register blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.timetable_routes import timetable_bp
from routes.branch_routes import branch_bp
from routes.smart_input_routes import smart_input_bp

app.register_blueprint(constraint_bp)
app.register_blueprint(generation_bp)
app.register_blueprint(validation_bp)
app.register_blueprint(edit_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(history_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(timetable_bp)
app.register_blueprint(branch_bp)
app.register_blueprint(smart_input_bp)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Flask server is running'}), 200

# Initialize Database and Seed Admin
with app.app_context():
    db.create_all()
    # Check for Admin
    admin = User.query.filter_by(username='Om').first()
    if not admin:
        print("Creating default admin user...")
        hashed_pw = generate_password_hash('Om@123')
        new_admin = User(username='Om', password_hash=hashed_pw, role='admin')
        db.session.add(new_admin)
        db.session.commit()
        print("Admin created.")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# What-If Simulation API Endpoints
from simulation.scenarios import (
    simulate_teacher_unavailable,
    simulate_lab_unavailable,
    simulate_days_reduced
)
from simulation.simulation_report import generate_simulation_report
from history.history_service import HistoryService

# Initialize history service for simulation
history_service_sim = HistoryService()

@app.route('/api/simulation/scenarios', methods=['GET'])
def get_available_scenarios():
    """Get list of supported simulation scenarios"""
    try:
        scenarios = [
            {
                "type": "TEACHER_UNAVAILABLE",
                "name": "Teacher Unavailable",
                "description": "Simulate what happens when a teacher is unavailable for specific days or the entire week",
                "parameters": ["teacherName", "unavailableSpec"],
                "icon": "👨‍🏫"
            },
            {
                "type": "LAB_UNAVAILABLE",
                "name": "Lab Removed / Unavailable",
                "description": "Simulate lab removal or unavailability, reassigning practicals to remaining labs",
                "parameters": ["labName"],
                "icon": "🔬"
            },
            {
                "type": "DAYS_REDUCED",
                "name": "Working Days Reduced",
                "description": "Simulate reducing working days (e.g., removing Saturday)",
                "parameters": ["newWorkingDays", "newSlotsConfig"],
                "icon": "📅"
            }
        ]
        
        return jsonify({"scenarios": scenarios}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulation/run', methods=['POST'])
def run_simulation():
    """
    Run a what-if simulation.
    
    Request body:
    {
        "branchId": "branch-123",
        "currentTimetable": [...],
        "scenarioType": "TEACHER_UNAVAILABLE" | "LAB_UNAVAILABLE" | "DAYS_REDUCED",
        "parameters": { scenario-specific parameters }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        scenario_type = data.get('scenarioType')
        current_timetable = data.get('currentTimetable', [])
        parameters = data.get('parameters', {})
        
        if not scenario_type:
            return jsonify({'error': 'scenarioType is required'}), 400
        
        if not current_timetable:
            return jsonify({'error': 'currentTimetable is required'}), 400
        
        # Load branch context
        branch_id = data.get('branchId')
        context = {}
        
        if branch_id:
            branches_data = load_branches()
            for branch in branches_data['branches']:
                if branch['id'] == branch_id:
                    context['branchData'] = branch
                    break
        
        # Load smart input data if available
        smart_input_id = data.get('smartInputId')
        if smart_input_id:
            history_data = load_smart_input_history()
            for entry in history_data['history']:
                if entry['id'] == smart_input_id:
                    context['smartInputData'] = entry['data']
                    break
        
        # If no context provided, try to extract from request
        if not context.get('branchData'):
            context['branchData'] = data.get('branchData', {})
        if not context.get('smartInputData'):
            context['smartInputData'] = data.get('smartInputData', {})
        
        # Run simulation based on scenario type
        simulation_result = None
        
        if scenario_type == 'TEACHER_UNAVAILABLE':
            teacher_name = parameters.get('teacherName')
            unavailable_spec = parameters.get('unavailableSpec', {})
            
            if not teacher_name:
                return jsonify({'error': 'teacherName is required for this scenario'}), 400
            
            simulation_result = simulate_teacher_unavailable(
                current_timetable,
                context,
                teacher_name,
                unavailable_spec
            )
        
        elif scenario_type == 'LAB_UNAVAILABLE':
            lab_name = parameters.get('labName')
            
            if not lab_name:
                return jsonify({'error': 'labName is required for this scenario'}), 400
            
            simulation_result = simulate_lab_unavailable(
                current_timetable,
                context,
                lab_name
            )
        
        elif scenario_type == 'DAYS_REDUCED':
            new_working_days = parameters.get('newWorkingDays')
            new_slots_config = parameters.get('newSlotsConfig')
            
            if not new_working_days:
                return jsonify({'error': 'newWorkingDays is required for this scenario'}), 400
            
            simulation_result = simulate_days_reduced(
                current_timetable,
                context,
                new_working_days,
                new_slots_config
            )
        
        else:
            return jsonify({'error': f'Unknown scenario type: {scenario_type}'}), 400
        
        # Generate detailed report
        report = generate_simulation_report(
            current_timetable,
            simulation_result['simulatedTimetable'],
            context,
            simulation_result
        )
        
        return jsonify({
            'success': True,
            'simulation': simulation_result,
            'report': report
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulation/apply', methods=['POST'])
def apply_simulation():
    """
    Apply a simulated timetable as the new active timetable.
    
    Request body:
    {
        "branchId": "branch-123",
        "smartInputId": "smart-input-123",
        "simulatedTimetable": [...]
    }
    """
    try:
        data = request.get_json()
        
        branch_id = data.get('branchId')
        simulated_timetable = data.get('simulatedTimetable', [])
        
        if not branch_id:
            return jsonify({'error': 'branchId is required'}), 400
        
        if not simulated_timetable:
            return jsonify({'error': 'simulatedTimetable is required'}), 400
        
        # In a real implementation, you would save this to a database or file
        # For now, we'll just return a success message
        # You can extend this to integrate with your existing timetable storage
        
        # Create version in history
        try:
            # Get branch and smart input data from request
            branch_data = data.get('branchData')
            smart_input_data = data.get('smartInputData')
            
            if branch_data and smart_input_data:
                context = {
                    'branchData': branch_data,
                    'smartInputData': smart_input_data
                }
                
                version = history_service_sim.auto_create_version(
                    timetable=simulated_timetable,
                    context=context,
                    action="Simulation Applied",
                    description="What-If simulation applied to active timetable"
                )
                version_id = version['versionId']
            else:
                version_id = None
        except Exception as e:
            print(f"Failed to create version: {e}")
            version_id = None
        
        return jsonify({
            'success': True,
            'message': 'Simulation applied successfully',
            'timetableSlots': len(simulated_timetable),
            'versionId': version_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Timetable Upload API Endpoints
@app.route('/api/upload/timetable/pdf', methods=['POST'])
def upload_pdf_timetable():
    """Handle PDF timetable uploads"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save the file
        file.save(filepath)
        
        try:
            # Parse the PDF
            result = pdf_parser.parse_pdf_file(filepath)
            
            # Clean up the file after processing
            if os.path.exists(filepath):
                os.remove(filepath)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'type': result['type'],
                    'pages': result['pages'],
                    'extractionMethod': result['extraction_method'],
                    'rowCount': result['row_count'],
                    'data': result['rows']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 400
        
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Restart Trigger
    app.run(debug=True, host='0.0.0.0', port=5000)
