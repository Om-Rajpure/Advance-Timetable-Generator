from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import json
from datetime import datetime
import uuid

# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pdf_parser
from routes.constraint_routes import constraint_bp
from routes.generation_routes import generation_bp
from routes.validation_routes import validation_bp
from routes.edit_routes import edit_bp

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Register blueprints
app.register_blueprint(constraint_bp)
app.register_blueprint(generation_bp)
app.register_blueprint(validation_bp)
app.register_blueprint(edit_bp)

# Data directory setup
DATA_DIR = 'data'
BRANCHES_FILE = os.path.join(DATA_DIR, 'branches.json')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')

# Ensure data directories exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize branches file if it doesn't exist
if not os.path.exists(BRANCHES_FILE):
    with open(BRANCHES_FILE, 'w') as f:
        json.dump({'branches': []}, f)

# Helper functions
def load_branches():
    """Load branches from JSON file"""
    try:
        with open(BRANCHES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'branches': []}

def save_branches(data):
    """Save branches to JSON file"""
    with open(BRANCHES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# API Routes (placeholders for authentication)
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Handle user login"""
    # TODO: Implement actual authentication logic
    return jsonify({'message': 'Login endpoint - to be implemented'}), 200

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Handle user signup"""
    # TODO: Implement actual authentication logic
    return jsonify({'message': 'Signup endpoint - to be implemented'}), 200

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Flask server is running'}), 200

# Branch Setup API Endpoints
@app.route('/api/branch/setup', methods=['POST'])
def create_branch():
    """Create a new branch configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['branchName', 'academicYears', 'divisions', 'workingDays']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Load existing branches
        branches_data = load_branches()
        
        # Check for duplicate branch name
        for branch in branches_data['branches']:
            if branch['branchName'].lower() == data['branchName'].lower():
                return jsonify({'error': 'Branch name already exists'}), 409
        
        # Create new branch with ID and timestamp
        new_branch = {
            'id': str(uuid.uuid4()),
            'createdAt': datetime.now().isoformat(),
            **data
        }
        
        # Add to branches list
        branches_data['branches'].append(new_branch)
        
        # Save to file
        save_branches(branches_data)
        
        return jsonify({
            'success': True,
            'message': 'Branch created successfully',
            'branch': new_branch
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/branch/all', methods=['GET'])
def get_all_branches():
    """Get all branch configurations"""
    try:
        branches_data = load_branches()
        
        # Return simplified branch info
        simplified_branches = []
        for branch in branches_data['branches']:
            simplified_branches.append({
                'id': branch['id'],
                'branchName': branch['branchName'],
                'academicYears': branch['academicYears'],
                'totalDivisions': sum(len(divs) for divs in branch['divisions'].values()),
                'createdAt': branch['createdAt']
            })
        
        return jsonify({'branches': simplified_branches}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/branch/<branch_id>', methods=['GET'])
def get_branch(branch_id):
    """Get a specific branch by ID"""
    try:
        branches_data = load_branches()
        
        # Find branch by ID
        for branch in branches_data['branches']:
            if branch['id'] == branch_id:
                return jsonify({'branch': branch}), 200
        
        return jsonify({'error': 'Branch not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/branch/validate-name', methods=['POST'])
def validate_branch_name():
    """Check if a branch name is available"""
    try:
        data = request.get_json()
        branch_name = data.get('name', '')
        
        if not branch_name:
            return jsonify({'error': 'Branch name is required'}), 400
        
        branches_data = load_branches()
        
        # Check if name exists
        for branch in branches_data['branches']:
            if branch['branchName'].lower() == branch_name.lower():
                return jsonify({'available': False}), 200
        
        return jsonify({'available': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Smart Input API Endpoints
SMART_INPUT_FILE = os.path.join(DATA_DIR, 'smart_input_history.json')

# Initialize smart input history file
if not os.path.exists(SMART_INPUT_FILE):
    with open(SMART_INPUT_FILE, 'w') as f:
        json.dump({'history': []}, f)

def load_smart_input_history():
    """Load smart input history from JSON file"""
    try:
        with open(SMART_INPUT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'history': []}

def save_smart_input_history(data):
    """Save smart input history to JSON file"""
    with open(SMART_INPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/api/smart-input/save', methods=['POST'])
def save_smart_input():
    """Save smart input data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'teachers' not in data or 'subjects' not in data:
            return jsonify({'error': 'Missing required fields: teachers or subjects'}), 400
        
        # Load history
        history_data = load_smart_input_history()
        
        # Create new entry
        new_entry = {
            'id': str(uuid.uuid4()),
            'branchName': data.get('branchName', 'Unknown Branch'),
            'createdAt': datetime.now().isoformat(),
            'teacherCount': len(data.get('teachers', [])),
            'subjectCount': len(data.get('subjects', [])),
            'data': data
        }
        
        # Add to history
        history_data['history'].append(new_entry)
        
        # Keep only last 20 entries
        if len(history_data['history']) > 20:
            history_data['history'] = history_data['history'][-20:]
        
        # Save
        save_smart_input_history(history_data)
        
        return jsonify({
            'success': True,
            'message': 'Smart input data saved successfully',
            'id': new_entry['id']
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/smart-input/history', methods=['GET'])
def get_smart_input_history():
    """Get smart input history"""
    try:
        history_data = load_smart_input_history()
        return jsonify(history_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/smart-input/validate', methods=['POST'])
def validate_smart_input():
    """Validate smart input data"""
    try:
        data = request.get_json()
        
        errors = []
        warnings = []
        
        # Basic validation
        if not data.get('teachers') or len(data.get('teachers', [])) == 0:
            errors.append({'message': 'At least one teacher is required'})
        
        if not data.get('subjects') or len(data.get('subjects', [])) == 0:
            errors.append({'message': 'At least one subject is required'})
        
        # Check for unmapped subjects
        teacher_subject_map = data.get('teacherSubjectMap', [])
        subjects = data.get('subjects', [])
        
        mapped_subject_ids = set(m['subjectId'] for m in teacher_subject_map)
        for subject in subjects:
            if subject['id'] not in mapped_subject_ids:
                errors.append({
                    'message': f'Subject "{subject["name"]}" has no teacher assigned'
                })
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# What-If Simulation API Endpoints
from simulation.scenarios import (
    simulate_teacher_unavailable,
    simulate_lab_unavailable,
    simulate_days_reduced
)
from simulation.simulation_report import generate_simulation_report

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
        
        return jsonify({
            'success': True,
            'message': 'Simulation applied successfully',
            'timetableSlots': len(simulated_timetable)
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

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React static files"""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
