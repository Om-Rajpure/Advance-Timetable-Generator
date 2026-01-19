import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_admin_users():
    print("Testing Admin API...")
    
    # 1. Login as Admin
    login_payload = {
        "username": "Om",
        "password": "Om@123"
    }
    
    try:
        # A. Login
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        if login_resp.status_code != 200:
            print(f"❌ Login Failed: {login_resp.text}")
            return
            
        token = login_resp.json().get('token')
        print("✅ Admin Login Successful")
        
        # B. Get Users
        headers = {'Authorization': f'Bearer {token}'}
        users_resp = session.get(f"{BASE_URL}/admin/users", headers=headers)
        
        print(f"Users API Status: {users_resp.status_code}")
        
        if users_resp.status_code == 200:
            users = users_resp.json()
            print(f"✅ Found {len(users)} users:")
            for u in users:
                print(f" - {u['username']} ({u['role']}) (ID: {u['id']})")
                
                # Auto-Test: Promote 'test' user to 'admin' if exists
                if u['username'] == 'test' and u['role'] != 'admin':
                    print(f"   🔄 Promoting 'test' (ID: {u['id']}) to admin...")
                    update_payload = {'role': 'admin'}
                    update_resp = session.put(f"{BASE_URL}/admin/users/{u['id']}", json=update_payload, headers=headers)
                    if update_resp.status_code == 200:
                         print("   ✅ Promotion Successful!")
                    else:
                         print(f"   ❌ Promotion Failed: {update_resp.text}")

        else:
            print(f"❌ Failed to fetch users: {users_resp.text}")

        # C. Get Timetables
        timetables_resp = session.get(f"{BASE_URL}/admin/timetables", headers=headers)
        if timetables_resp.status_code == 200:
             print(f"✅ Found {len(timetables_resp.json())} timetables")
        else:
             print(f"❌ Failed to fetch timetables: {timetables_resp.text}")

            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_admin_users()
