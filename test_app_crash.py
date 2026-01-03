
import sys
import os
import json
from app import app

def reproduce_crash():
    print("🚀 RUNNING FLASK TEST CLIENT")
    client = app.test_client()
    
    # Same Payload as test_api_integration.py
    user_data = {
      "years": ["SE", "TE", "BE"],
      "divisions": {
        "SE": ["A", "B"],
        "TE": ["A", "B"],
        "BE": ["A", "B"]
      },
      "batches": ["A", "B", "C"],
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "slots_per_day": 6,
      "subjects": {
        "SE": {
          "theory": ["SE_T1", "SE_T2"], # Simplified
          "labs": ["SE_L1"]
        },
        "TE": {"theory": [], "labs": []},
        "BE": {"theory": [], "labs": []}
      },
      "teachers": {}, # Empty fine for structure check
      "labs": ["Lab_1"],
      "classrooms": ["R1"]
    }
    
    # Construct minimally valid payload
    branch_data = {
        "academicYears": user_data['years'],
        "divisions": user_data['divisions'],
        "slotsPerDay": 6,
        "workingDays": user_data['days'],
        "rooms": user_data['classrooms'],
        "labs": [], 
        "sharedLabs": [{"name": l, "capacity": 30} for l in user_data['labs']],
        "labBatchesPerYear": {y: 3 for y in user_data['years']} 
    }
    
    smart_input_data = {
        "subjects": [{"name": "SE_T1", "year": "SE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False}],
        "teachers": [{"name": "T1", "subjects": ["SE_T1"]}]
    }

    payload = {
        "branchData": branch_data,
        "smartInputData": smart_input_data
    }
    
    try:
        resp = client.post('/api/generate/full', json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Data: {resp.json}")
    except Exception as e:
        print(f"CAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce_crash()
