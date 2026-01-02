import requests
import json
import sys

BASE_URL = "http://localhost:5000/api/generate/full"

def print_result(test_name, success, message=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}: {message}")

def test_invalid_json_content_type():
    try:
        response = requests.post(BASE_URL, data="not json", headers={"Content-Type": "text/plain"})
        
        # Should fail but return JSON 400
        is_json = False
        try:
            data = response.json()
            is_json = True
        except:
            is_json = False
            
        print_result("Invalid Content Type Handled", 
                     response.status_code == 400 and is_json, 
                     f"Status: {response.status_code}, Is JSON: {is_json}, Body: {response.text[:100]}")
    except Exception as e:
        print_result("Invalid Content Type Handled", False, str(e))

def test_invalid_json_structure():
    try:
        # Send a list instead of dict
        response = requests.post(BASE_URL, json=[], headers={"Content-Type": "application/json"})
        
        data = response.json()
        success = response.status_code == 400 and data.get("success") == False and "Invalid JSON payload structure" in data.get("reason", "")
        
        print_result("Invalid JSON Structure Handled", success, f"Reason: {data.get('reason')}")
    except Exception as e:
        print_result("Invalid JSON Structure Handled", False, str(e))

def test_missing_fields():
    try:
        # Send dict but missing required fields
        response = requests.post(BASE_URL, json={"some": "data"}, headers={"Content-Type": "application/json"})
        
        data = response.json()
        # logic checks for branchData and smartInputData
        # type(None) will result in Validiation Stage error
        
        success = response.status_code == 400 and data.get("success") == False and data.get("stage") == "VALIDATION"
        
        print_result("Missing Fields Handled", success, f"Stage: {data.get('stage')}, Reason: {data.get('reason')}")
    except Exception as e:
        print_result("Missing Fields Handled", False, str(e))

def run_tests():
    print("🧪 Starting API Robustness Tests...")
    test_invalid_json_content_type()
    test_invalid_json_structure()
    test_missing_fields()
    print("🏁 Tests Completed")

if __name__ == "__main__":
    run_tests()
