import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/auth"

def test_login():
    print("Testing Login...")
    
    # 1. Try to Login as Admin (should exist)
    payload = {
        "username": "Om",
        "password": "Om@123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login Successful")
        else:
            print("❌ Login Failed")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_login()
