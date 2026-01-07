from werkzeug.security import generate_password_hash
import json
import os

DATA_DIR = 'backend/data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

def reset_admin_password():
    password = "admin123"
    print(f"Generating hash for password: {password}")
    
    # Generate new hash
    password_hash = generate_password_hash(password)
    print(f"New Hash: {password_hash}")
    
    # Update users.json
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            
        users = data.get('users', [])
        admin_user = next((u for u in users if u['username'] == 'admin'), None)
        
        if admin_user:
            admin_user['password'] = password_hash
            print("Updated admin password hash.")
            
            with open(USERS_FILE, 'w') as f:
                json.dump({'users': users}, f, indent=2)
            print("Saved users.json.")
        else:
            print("Admin user not found!")
    else:
        print(f"File not found: {USERS_FILE}")

if __name__ == "__main__":
    reset_admin_password()
