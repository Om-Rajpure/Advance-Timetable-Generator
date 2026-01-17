
import sys
import os
import json
import traceback
from app import app

def run_deep_test():
    print("🚀 RUNNING DEEP FLASK TEST (In-Process)")
    client = app.test_client()
    
    # Payload from repro_crash_strict.py (Known to be close to user's)
    # But let's try to break it with "semi-valid" data that might pass sanitizer
    
    branch_data = {
        "academicYears": ["SE", "TE"], 
        "divisions": {"SE": ["A"], "TE": ["A"]},
        "slotsPerDay": 6,
        "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "rooms": ["R1"],
        "labs": [], 
        "sharedLabs": [{"name": "L1", "capacity": 30}],
        "labBatchesPerYear": {"SE": 3, "TE": 3}
    }

    smart_input_data = {
        "subjects": [
             {"name": "Sub1", "year": "SE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False},
             {"name": "Lab1", "year": "SE", "type": "Practical", "lecturesPerWeek": 4, "isPractical": True}
        ],
        "teachers": [
            {"name": "T1", "subjects": ["Sub1", "Lab1"]}
        ],
        "teacherSubjectMap": []
    }

    payload = {
        "branchData": branch_data,
        "smartInputData": smart_input_data
    }
    
    try:
        print("📡 Sending POST request...")
        resp = client.post('/api/generate/full', json=payload)
        print(f"STATUS: {resp.status_code}")
        
        if resp.status_code == 200:
            print("✅ SUCCESS")
            print(json.dumps(resp.json, indent=2))
        else:
            print("❌ FAILURE")
            print(json.dumps(resp.json, indent=2))
            
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    run_deep_test()
