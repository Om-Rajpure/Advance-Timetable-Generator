from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
import json
import os
import uuid

auth_bp = Blueprint('auth_bp', __name__)


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', [])
    except:
        return []

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump({'users': users}, f, indent=2)
        return True
    except:
        return False

@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username') or data.get('email') # Support both
        password = data.get('password')
        role = data.get('role', 'user') # Default to user role

        if not username or not password:
            return jsonify({'error': 'Missing username/email or password'}), 400

        users = load_users()
        
        # Check if user already exists
        if any(u['username'] == username for u in users):
            return jsonify({'error': 'User already exists'}), 409

        # Create new user
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': generate_password_hash(password),
            'role': role,
            'createdAt': datetime.datetime.now().isoformat()
        }
        
        users.append(new_user)
        
        if save_users(users):
            # Generate JWT (Auto-login)
            token = jwt.encode({
                'user_id': new_user['id'],
                'username': new_user['username'],
                'role': new_user['role'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'success': True, 
                'message': 'User created successfully',
                'token': token,
                'user': {
                    'id': new_user['id'],
                    'username': new_user['username'],
                    'role': new_user['role']
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to save user'}), 500

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # DEBUG LOGGING
        with open('debug_auth.txt', 'a') as f:
            f.write(f"\n[{datetime.datetime.now()}] Login attempt:\n")
            f.write(f"Received data: {json.dumps(data)}\n")
            f.write(f"Username: {username}\n")
            
            if not username or not password:
                f.write("Missing username or password\n")
                return jsonify({'error': 'Missing username or password'}), 400

            users = load_users()
            f.write(f"Loaded {len(users)} users\n")
            
            user = next((u for u in users if u['username'] == username), None)

            if not user:
                f.write(f"User {username} not found\n")
                return jsonify({'error': 'Invalid credentials'}), 401

            f.write(f"Found user: {user['username']}\n")
            is_valid = check_password_hash(user['password'], password)
            f.write(f"Password valid: {is_valid}\n")

            if is_valid:
                # Generate JWT
                token = jwt.encode({
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, current_app.config['SECRET_KEY'], algorithm='HS256')

                return jsonify({
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role']
                    }
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
