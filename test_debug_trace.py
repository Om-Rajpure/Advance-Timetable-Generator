
import sys
import os
import json

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

def test_failure_trace():
    print("=== TEST FAILURE TRACE ===")
    
    # Context with NO subjects -> Should fail strict block
    context = {
        "branchData": {
            "academicYears": ["SE"],
            "divisions": {"SE": ["A"]},
            "workingDays": ["Monday"],
            "timeSlots": {
                 "startTime": "09:00",
                 "endTime": "10:00", # 1 hour = 1 slot?
                 "slotDuration": 60
            },
            "recess_slot": 4, 
            "labs": ["Lab1"],
            "labBatchesPerYear": {"SE": 3}
        },
        "smartInputData": {
            "subjects": [
                 {"name": "Math", "year": "SE", "division": "A", "weeklyLectures": 4, "type": "Theory"}
            ], 
            "teachers": [{"name": "T1", "subjects": ["Math"]}]
        }
    }
    
    scheduler = TimetableScheduler(context)
    
    try:
        result = scheduler.generate()
    except RuntimeError as e:
        print(f"\nCaught Expected Error: {e}")
        
    # Check if context dumped
    if os.path.exists('backend_failure_context.json'):
        print("\nSUCCESS: backend_failure_context.json exists.")
    else:
        print("\nFAILURE: Context file not found.")

if __name__ == "__main__":
    test_failure_trace()
