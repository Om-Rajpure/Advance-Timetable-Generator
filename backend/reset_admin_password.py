import json
import os
from werkzeug.security import generate_password_hash

DATA_DIR = 'data'
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

def reset_admin():
    users = load_users()
    admin_found = False
    
    for user in users:
        if user['username'] == 'admin':
            print("Found admin user. Updating password...")
            user['password'] = generate_password_hash('admin123')
            admin_found = True
            break
            
    if not admin_found:
        print("Admin user not found. Creating one...")
        users.append({
            'id': 'admin-user',
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'createdAt': '2024-01-01T00:00:00.000000'
        })
        print("Created admin user.")
        
    if save_users(users):
        print("Successfully updated admin password.")
    else:
        print("Failed to save users.json")

if __name__ == "__main__":
    reset_admin()
