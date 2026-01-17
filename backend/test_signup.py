import requests
import json
import uuid

BASE_URL = "http://localhost:5000"

def test_signup():
    print("Testing Signup...")
    # Generate random email to avoid collision
    random_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": random_email,
        "name": "Test User",
        "username": random_email, # Frontend sends email as username
        "password": "password123",
        "role": "user"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("Signup Successful.")
            return True, random_email
        else:
            print("Signup Failed.")
            return False, None
    except Exception as e:
        print(f"Request Error: {e}")
        return False, None

def test_login_after_signup(email):
    print("\nTesting Login with New User...")
    payload = {
        "username": email,
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("Login with new user Successful.")
            return True
        else:
            print("Login with new user Failed.")
            return False
    except Exception as e:
        print(f"Request Error: {e}")
        return False

if __name__ == "__main__":
    success, email = test_signup()
    if success:
        test_login_after_signup(email)
