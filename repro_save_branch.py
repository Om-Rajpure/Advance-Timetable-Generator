
import requests
import json

url = 'http://localhost:5000/api/branch/setup'

payload = {
    "branchName": "Test Branch",
    "academicYears": ["SE", "TE"],
    "divisions": {
        "SE": ["A", "B"],
        "TE": ["A"]
    },
    "workingDays": ["Monday", "Tuesday", "Wednesday"],
    "startTime": "8:00 AM",
    "endTime": "5:00 PM",
    "lectureDuration": 60,
    "recessEnabled": True,
    "recessStart": "12:00 PM",
    "recessDuration": 60,
    "classrooms": {
        "SE": ["Room 101"],
        "TE": ["Room 201"]
    },
    "sharedLabs": [
        {
            "name": "Computer Lab 1", 
            "capacity": 30,
            "availableDays": ["Monday", "Tuesday"], 
            "availableSlots": [1, 2, 3, 4]
        }
    ],
    "labBatchesPerYear": {
        "SE": 3,
        "TE": 3
    }
}

try:
    print("Sending payload...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
