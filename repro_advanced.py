
import requests
import json

url = 'http://localhost:5000/api/branch/setup'

def test_payload(name, payload):
    print(f"Testing: {name}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code != 201:
            print(f"Error Body: {response.text}")
        else:
            print("Success")
    except Exception as e:
        print(f"Exception: {e}")
    print("-" * 20)

# Base valid payload
base = {
    "branchName": "Adv Test",
    "academicYears": ["Y1"],
    "divisions": {"Y1": ["A"]},
    "workingDays": ["Mon"],
    "startTime": "9:00",
    "endTime": "10:00",
    "lectureDuration": 60,
    "recessEnabled": False,
    "classrooms": {"Y1": ["R1"]},
    "sharedLabs": [],
    "labBatchesPerYear": {"Y1": 1}
}

# Test 1: Empty Shared Labs
payload1 = base.copy()
payload1["branchName"] = "Test Empty Labs"
payload1["sharedLabs"] = []
test_payload("Empty Shared Labs", payload1)

# Test 2: Missing Optional Fields
payload2 = base.copy()
payload2["branchName"] = "Test Missing Optionals"
del payload2["recessEnabled"]
# del payload2["sharedLabs"] # Should work?
test_payload("Missing Optional Fields", payload2)

# Test 3: Shared Labs with Missing Internal Fields
payload3 = base.copy()
payload3["branchName"] = "Test Invalid Lab"
payload3["sharedLabs"] = [{"name": "BadLab"}] # Missing capacity, slots
test_payload("Invalid Lab Structure", payload3)

# Test 4: Unicode chars
payload4 = base.copy()
payload4["branchName"] = "Test Unicode 🎓"
test_payload("Unicode Name", payload4)
