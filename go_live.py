import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:5000"
DATA_FILE = os.path.join("test_data", "go_live_data.json")

def wait_for_server():
    print("⏳ Waiting for backend server to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{BASE_URL}/api/health")
            if response.status_code == 200:
                print("✅ Backend server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    print("\n❌ Timed out waiting for backend server.")
    return False

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Data file not found: {DATA_FILE}")
        return None
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def setup_branch(data):
    print("\n🚀 Setting up Branch...")
    url = f"{BASE_URL}/api/branch/setup"
    payload = data['branchData']
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201 or response.status_code == 200:
            print("✅ Branch setup successful!")
            return True
        else:
            print(f"❌ Branch setup failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during branch setup: {e}")
        return False

def save_smart_input(data):
    print("\n🧠 Saving Smart Input...")
    url = f"{BASE_URL}/api/smart-input/save"
    # Combine everything into the payload as the endpoint seems to expect a flat structure or specific keys
    # Looking at app.py: save_smart_input expects 'teachers' and 'subjects' in the body
    # The payload structure in app.py logic roughly takes the whole body.
    
    payload = data['smartInputData']
    # Add branch info if needed, though app.py separates them.
    # Actually app.py:229 uses data.get('branchName').
    payload['branchName'] = data['branchData']['branchName']
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201 or response.status_code == 200:
            print("✅ Smart input saved successfully!")
            return True
        else:
            print(f"❌ Smart input save failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during smart input save: {e}")
        return False

def generate_timetable(data):
    print("\n⚡ Generating Timetable...")
    url = f"{BASE_URL}/api/generate/full"
    
    # payload for generate/full expects { branchData: ..., smartInputData: ... }
    payload = {
        "branchData": data['branchData'],
        "smartInputData": data['smartInputData']
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ Timetable generation successful! (Took {end_time - start_time:.2f}s)")
            result = response.json()
            if result.get('success'):
                print(f"🎉 SUCCESS! {len(result.get('timetables', {}))} divisions generated.")
                if result.get('validationErrors'):
                    print(f"⚠️ Validation warnings: {len(result['validationErrors'])}")
            else:
                 print(f"⚠️ Generated with issues: {result.get('message')}")
            return True
        else:
            print(f"❌ Timetable generation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return False

def main():
    if not wait_for_server():
        sys.exit(1)
        
    data = load_data()
    if not data:
        sys.exit(1)
        
    if not setup_branch(data):
        sys.exit(1)
        
    if not save_smart_input(data):
        sys.exit(1)
        
    generate_timetable(data)

if __name__ == "__main__":
    main()
