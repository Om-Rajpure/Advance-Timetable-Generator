import sys
import os
import json
from backend.app import app, db
from backend.models import User

def run_verification():
    print("🚀 Starting Database Verification...")
    
    # 1. Initialize DB
    print("\n1️⃣  Initializing Database...")
    with app.app_context():
        db.create_all()
        print("   ✅ Tables created (or existed).")
        
        # 2. Verify Admin User
        print("\n2️⃣  Verifying Admin User Seed...")
        admin = User.query.filter_by(username='Om').first()
        if admin:
            print(f"   ✅ Admin user found: {admin.username}, Role: {admin.role}")
        else:
            print("   ❌ Admin user NOT found! Seeding failed.")
            return

    # 3. Test Auth Endpoint (Login)
    print("\n3️⃣  Testing Admin Login...")
    client = app.test_client()
    login_payload = {
        "username": "Om",
        "password": "Om@123"
    }
    
    response = client.post('/api/auth/login', json=login_payload)
    if response.status_code == 200:
        print("   ✅ Login Successful.")
        data = response.get_json()
        token = data.get('token')
        print(f"   🔑 Token received: {token[:20]}...")
    else:
        print(f"   ❌ Login Failed: {response.status_code} - {response.get_json()}")
        return

    # 4. Test Admin Route (Get Users)
    print("\n4️⃣  Testing Protected Admin Route (/api/admin/users)...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = client.get('/api/admin/users', headers=headers)
    if response.status_code == 200:
        users = response.get_json()
        print(f"   ✅ Admin Access Granted. Found {len(users)} users.")
        print(f"   📋 Users: {[u['username'] for u in users]}")
    else:
        print(f"   ❌ Admin Access Failed: {response.status_code} - {response.get_json()}")
        return

    print("\n✨ ALL CHECKS PASSED SUCCESSFULLY! ✨")

if __name__ == "__main__":
    # Fix path so we can import backend modules AND backend internal modules match
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, 'backend')
    sys.path.append(root_dir)
    sys.path.append(backend_dir)
    
    try:
        run_verification()
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   ⚠️  Did you install the dependencies? Run: pip install Flask-SQLAlchemy")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
