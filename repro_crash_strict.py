
import requests
import json
import time

API_URL = "http://localhost:5000/api/generate/full"

def run_repro():
    print(f"🚀 TARGETING API: {API_URL}")
    
    # Mock data mimicking Frontend LOCAL STORAGE + AGGREGATED DATA
    
    # 1. Branch Data (Sanitized as per my fix)
    branch_data = {
        "academicYears": ["SE", "TE", "BE"], # Array
        "divisions": { # Dict
            "SE": ["A", "B"], 
            "TE": ["A", "B"], 
            "BE": ["A", "B"]
        },
        "slotsPerDay": 6,
        "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "rooms": ["R1", "R2", "R3"],
        "labs": [], 
        "sharedLabs": [{"name": "L1", "capacity": 30}],
        "labBatchesPerYear": {"SE": 3, "TE": 3, "BE": 3}
    }

    # 2. Smart Input Data
    # Minimized but valid
    sorted_subjects = [
        {"name": "SE_T1", "year": "SE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False, "sessionLength": 1},
        {"name": "SE_L1", "year": "SE", "type": "Practical", "lecturesPerWeek": 2, "isPractical": True, "sessionLength": 2}
    ]
    
    teachers = [
        {"name": "T1", "subjects": ["SE_T1", "SE_L1"]}
    ]
    
    map_data = [
        {"teacherName": "T1", "subjectName": "SE_T1"},
        {"teacherName": "T1", "subjectName": "SE_L1"}
    ]

    payload = {
        "branchData": branch_data,
        "smartInputData": {
            "subjects": sorted_subjects,
            "teachers": teachers,
            "teacherSubjectMap": map_data
        }
    }
    
    print(f"📡 Sending Payload...")
    try:
        response = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'})
        
        print(f"STATUS CODE: {response.status_code}")
        print("--- RESPONSE BODY ---")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
    except Exception as e:
        print(f"❌ REPRO FAILED: {e}")

if __name__ == "__main__":
    run_repro()
