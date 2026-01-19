from flask import Blueprint, jsonify, request, current_app
from database import db
from models import SmartInput, User
import jwt
from functools import wraps

smart_input_bp = Blueprint('smart_input_bp', __name__)

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

@smart_input_bp.route('/api/smart-input/save', methods=['POST'])
@token_required
def save_smart_input(current_user):
    try:
        data = request.get_json()
        
        new_entry = SmartInput(
            user_id=current_user.id,
            data=data
        )
        
        db.session.add(new_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Smart input saved',
            'id': new_entry.id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@smart_input_bp.route('/api/smart-input/history', methods=['GET'])
@token_required
def get_smart_input_history(current_user):
    try:
        # Get last 20 entries for this user
        entries = SmartInput.query.filter_by(user_id=current_user.id)\
            .order_by(SmartInput.created_at.desc())\
            .limit(20).all()
            
        history_list = []
        for e in entries:
            # Reconstruct history object format
            history_list.append({
                'id': e.id,
                'branchName': e.data.get('branchName', 'Unknown'),
                'createdAt': e.created_at.isoformat(),
                'teacherCount': len(e.data.get('teachers', [])),
                'subjectCount': len(e.data.get('subjects', [])),
                'data': e.data
            })
            
        return jsonify({'history': history_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@smart_input_bp.route('/api/smart-input/validate', methods=['POST'])
# Validation might not strictly need auth, but good to have
def validate_smart_input():
    try:
        data = request.get_json()
        errors = []
        
        if not data.get('teachers'):
            errors.append({'message': 'At least one teacher is required'})
            
        return jsonify({'valid': len(errors) == 0, 'errors': errors}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
