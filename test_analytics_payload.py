
import requests
import json
import sys

# MOCK DATA simulating what frontend sends
timetable_data = [
    # A valid slot
    {
        "day": "Monday",
        "slot": 1,
        "year": "SE",
        "division": "A",
        "teacher": "Dr. Sharma", # Matches
        "subject": "Math",
        "type": "THEORY"
    },
    # A slot with whitespace mismatch
    {
        "day": "Monday",
        "slot": 2,
        "year": "SE",
        "division": "A",
        "teacher": "Prof. Patel ", # Trailing space
        "subject": "Physics",
        "type": "THEORY"
    }
]

branch_data = {
    "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
}

smart_input_data = {
    "teachers": [
        {"name": "Dr. Sharma"},
        {"name": "Prof. Patel"}
    ]
}

payload = {
    "timetable": timetable_data,
    "branchData": branch_data,
    "smartInputData": smart_input_data
}

print("--- Sending POST /api/analytics/full-report ---")
try:
    response = requests.post(
        "http://localhost:5000/api/analytics/full-report",
        json=payload,
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        workload = data.get('workload', {}).get('perTeacher', {})
        print("Workload Result:")
        print(json.dumps(workload, indent=2))
        
        # Validation
        sharma = workload.get('Dr. Sharma', {}).get('totalLectures', 0)
        patel = workload.get('Prof. Patel', {}).get('totalLectures', 0)
        
        if sharma == 1 and patel == 1:
            print("✅ SUCCESS: Backend logic verified via API.")
        else:
            print(f"❌ FAILURE: Expected 1 each. Got Sharma={sharma}, Patel={patel}")
            
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Request failed: {e}")
