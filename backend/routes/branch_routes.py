from flask import Blueprint, jsonify, request, current_app
from database import db
from models import Branch, User
import jwt
from functools import wraps
from datetime import datetime

branch_bp = Blueprint('branch_bp', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@branch_bp.route('/api/branch/setup', methods=['POST'])
@token_required
def create_branch(current_user):
    """Create a new branch configuration for the current user"""
    try:
        data = request.get_json()
        
        # Validation
        if 'branchName' not in data:
            return jsonify({'error': 'branchName is required'}), 400
            
        new_branch = Branch(
            user_id=current_user.id,
            name=data['branchName'],
            config=data
        )
        
        db.session.add(new_branch)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Branch created successfully',
            'branch': new_branch.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@branch_bp.route('/api/branch/all', methods=['GET'])
@token_required
def get_my_branches(current_user):
    """Get all branches created by the current user"""
    try:
        branches = Branch.query.filter_by(user_id=current_user.id).all()
        
        # Format explicitly to match frontend expectations if needed
        # Frontend expects: { branches: [ { id, branchName, ... } ] }
        
        simplified_branches = []
        for b in branches:
            # Reconstruct the expected object structure from the stored config
            # Ensure ID is the database ID, not the one in config
            branch_obj = b.config.copy()
            branch_obj['id'] = b.id # Override with DB ID
            branch_obj['createdAt'] = b.created_at.isoformat()
            
            # Simple list item
            simplified_branches.append({
                'id': b.id,
                'branchName': b.name,
                'academicYears': b.config.get('academicYears', []),
                'totalDivisions': sum(len(divs) for divs in b.config.get('divisions', {}).values()),
                'createdAt': b.created_at.isoformat()
            })
            
        return jsonify({'branches': simplified_branches}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@branch_bp.route('/api/branch/<int:branch_id>', methods=['GET'])
@token_required
def get_branch(current_user, branch_id):
    """Get a specific branch by ID, ensuring ownership"""
    try:
        branch = Branch.query.get(branch_id)
        
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404
            
        if branch.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Return full structure
        response_data = branch.config.copy()
        response_data['id'] = branch.id
        
        return jsonify({'branch': response_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@branch_bp.route('/api/branch/validate-name', methods=['POST'])
@token_required
def validate_branch_name(current_user):
    """Check if a branch name is available (per user)"""
    try:
        data = request.get_json()
        name = data.get('name', '')
        
        exists = Branch.query.filter_by(user_id=current_user.id, name=name).first()
        
        return jsonify({'available': not exists}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
