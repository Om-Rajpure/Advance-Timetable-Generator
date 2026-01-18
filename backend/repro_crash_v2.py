
import sys
import os
import datetime

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Mock Data
dummy_context = {
    "branchData": {
        "academicYears": ["SE"],
        "divisions": {"SE": ["A"]},
        "startTime": "09:00",
        "lectureDuration": 60,
        "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "labs": ["Lab1", "Lab2"],
        "rooms": ["Room101", "Room102"]
    },
    "smartInputData": {
        "subjects": [
            {"name": "Math", "year": "SE", "division": "A", "type": "Lecture", "lecturesPerWeek": 3},
            {"name": "Physics", "year": "SE", "division": "A", "type": "Lecture", "lecturesPerWeek": 3},
            {"name": "Python Lab", "year": "SE", "division": "A", "type": "Practical", "batches": 3}
        ],
        "teachers": [
            {"name": "T1", "subjects": ["Math"]},
            {"name": "T2", "subjects": ["Physics"]},
            {"name": "T3", "subjects": ["Python Lab"]}
        ]
    }
}

print("Initiating Reproduction Test...")

try:
    from engine.scheduler import TimetableScheduler
    scheduler = TimetableScheduler(dummy_context)
    print("Scheduler Initialized.")
    result = scheduler.generate()
    print("Generate returned:", result['success'])
    if not result['success']:
        print("Error Message:", result.get('message'))
        print("Traceback:", result.get('traceback'))

except Exception as e:
    import traceback
    traceback.print_exc()
    print("CRASHED:", e)
