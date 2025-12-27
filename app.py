from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from datetime import datetime
import uuid

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Data directory setup
DATA_DIR = 'data'
BRANCHES_FILE = os.path.join(DATA_DIR, 'branches.json')

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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
