from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from database import db
from models import User

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username') or data.get('email') # Support both
        password = data.get('password')
        role = data.get('role', 'user') # Default to user role

        if not username or not password:
            return jsonify({'error': 'Missing username/email or password'}), 400

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'User already exists'}), 409

        # Create new user
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT (Auto-login)
        token = jwt.encode({
            'user_id': new_user.id,
            'username': new_user.username,
            'role': new_user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'success': True, 
            'message': 'User created successfully',
            'token': token,
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Signup error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    print("🔹 Login Request Received")
    try:
        data = request.get_json()
        print(f"🔹 Payload: {data}")
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400

        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if check_password_hash(user.password_hash, password):
            # Generate JWT
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'token': token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/api/auth/verify', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'valid': False}), 401
    
    try:
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({
            'valid': True, 
            'user': {
                'id': data['user_id'],
                'username': data['username'], 
                'role': data['role']
            }
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

@auth_bp.route('/api/auth/debug', methods=['GET'])
def debug_status():
    return jsonify({
        'status': 'online',
        'database': 'sqlite',
        'timestamp': datetime.datetime.now().isoformat()
    })
