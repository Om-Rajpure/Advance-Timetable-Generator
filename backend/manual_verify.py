
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

# Mock Context
context = {
    "branchData": {
        "academicYears": ["SE", "TE"],
        "divisions": {
            "SE": ["A", "B"],
            "TE": ["A"]
        },
        "labs": ["Lab1", "Lab2"],
        "sharedLabs": [{"name": "Lab1"}, {"name": "Lab2"}],
        "labBatchesPerYear": {"SE": 3, "TE": 3}
    },
    "smartInputData": {
        "subjects": [
            {"name": "Maths", "type": "Theory", "year": "SE", "lecturesPerWeek": 4},
            {"name": "Physics", "type": "Theory", "year": "SE", "lecturesPerWeek": 3},
            {"name": "Chemistry Lab", "type": "Practical", "year": "SE", "lecturesPerWeek": 2, "isPractical": True}
        ],
        "teachers": [
            {"name": "T1", "subjects": ["Maths"]},
            {"name": "T2", "subjects": ["Physics"]},
            {"name": "T3", "subjects": ["Chemistry Lab"]}
        ]
    }
}

print("\n--- STARTING REPRODUCTION SCRIPT ---\n")
try:
    scheduler = TimetableScheduler(context)
    result = scheduler.generate()
    print("\n--- RESULT ---")
    print("Success:", result.get('success'))
    print("Failures:", result.get('failures'))
    if result.get('success'):
        print("Timetables Keys:", list(result.get('timetables', {}).keys()))
except Exception as e:
    print(f"\nCRASH CAUGHT: {e}")
    import traceback
    traceback.print_exc()
