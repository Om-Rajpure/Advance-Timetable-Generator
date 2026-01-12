
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

def test_generation():
    print("Testing Timetable Generation...")
    
    # Mock context
    context = {
        "teachers": [{"id": "t1", "name": "TESTER", "subject": "SUB1"}],
        "subjects": [{"id": "s1", "name": "SUB1", "lectureHours": 4}],
        "classrooms": ["101"],
        "labs": [],
        "mappings": [{"year": "SE", "division": "A", "subjects": [{"name": "SUB1", "teacher": "TESTER", "hours": 4}]}],
        "branchData": {
            "startTime": "9:00 AM",
            "endTime": "5:00 PM",
            "lectureDuration": 60,
            "recessEnabled": True,
            "recessStart": "1:00 PM"
        }
    }

    scheduler = TimetableScheduler(context)
    result = scheduler.generate()
    
    print(f"Generation Complete.")
    print(f"Keys: {list(result.keys())}")
    
    if 'dayLayout' in result:
        print("\n[SUCCESS] dayLayout found:")
        print(json.dumps(result['dayLayout'], indent=2))
        if len(result['dayLayout']) > 0:
            print("Layout has content.")
        else:
            print("Layout is empty.")
    else:
        print("\n[FAILURE] dayLayout NOT found in result.")

if __name__ == "__main__":
    test_generation()
