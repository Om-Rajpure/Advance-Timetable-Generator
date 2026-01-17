import requests
import json

BASE_URL = "http://localhost:5000"

def test_login():
    print("Testing Login...")
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token = response.json().get('token')
            print("Login Successful, Token received.")
            return token
        else:
            print("Login Failed.")
            return None
    except Exception as e:
        print(f"Request Error: {e}")
        return None

def test_verify(token):
    print("\nTesting Verify Token...")
    if not token:
        print("Skipping verify (no token)")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/verify", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    token = test_login()
    test_verify(token)
