from flask import Blueprint, jsonify, request
from database import db
from models import User, Timetable, TimetableEntry
from functools import wraps
import jwt
import os
from flask import current_app

admin_bp = Blueprint('admin_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(data['user_id'])
            if not user or user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@admin_bp.route('/api/admin/timetables', methods=['GET'])
@admin_required
def get_all_timetables():
    timetables = Timetable.query.all()
    # Eager load isn't strictly necessary for a list view but good for details
    return jsonify([t.to_dict() for t in timetables]), 200

@admin_bp.route('/api/admin/timetable/<int:id>/entries', methods=['GET'])
@admin_required
def get_timetable_entries(id):
    entries = TimetableEntry.query.filter_by(timetable_id=id).all()
    return jsonify([e.to_dict() for e in entries]), 200

@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_db_stats():
    user_cnt = User.query.count()
    timetable_cnt = Timetable.query.count()
    return jsonify({
        'users': user_cnt,
        'timetables': timetable_cnt
    }), 200

@admin_bp.route('/api/admin/users/<int:id>', methods=['PUT'])
@admin_required
def update_user(id):
    try:
        data = request.get_json()
        user = User.query.get(id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Prevent self-demotion/deletion logic (optional but recommended)
        # current_user_id = ... (needs extraction if strict safety needed)
        
        if 'role' in data:
            if data['role'] not in ['admin', 'user', 'faculty']:
                 return jsonify({'error': 'Invalid role'}), 400
            user.role = data['role']
            
        if 'username' in data:
            # Check unique
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != id:
                return jsonify({'error': 'Username already taken'}), 409
            user.username = data['username']

        db.session.commit()
        return jsonify(user.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    try:
        user = User.query.get(id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Optional: Prevent deleting the last admin or self
        # if user.role == 'admin': ...

        # Cascade delete is handled by database relationships if configured, 
        # but let's be explicit or rely on models.py cascade.
        # Models.py has: timetables = db.relationship(..., cascade="all, delete-orphan") ✅
        
        # We also need to delete Branches and SmartInputs manually if not cascaded
        # defined in models.py? 
        # Branch/SmartInput dont have relationship() in User model explicitly with cascade, 
        # let's quick check models.py or just do it manual.
        # User model: timetables = db.relationship...
        # Branch model: user_id = ForeignKey... (no backref in User)
        # So we should manually clean up to be safe.
        
        from models import Branch, SmartInput
        Branch.query.filter_by(user_id=id).delete()
        SmartInput.query.filter_by(user_id=id).delete()
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
