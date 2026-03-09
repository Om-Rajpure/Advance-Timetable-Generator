
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler, InfeasibleScheduleError

def test_strict_infeasibility():
    print("=== TEST STRICT INFEASIBILITY (GAP) ===")
    
    # SETUP:
    # 1 Day (Monday)
    # 8 Slots total
    # Recess at index 4 (5th slot)
    # Morning Block: 0, 1, 2, 3 (4 slots)
    # Afternoon Block: 5, 6, 7 (3 slots)
    
    # SUBJECTS:
    # "Math": 1 Lecture
    # Total Load: 1 Lecture.
    # Morning Block needs 4 slots filled.
    # Math fills 1. 
    # 3 Empty slots.
    # RESULT: Should FAIL Strict continuous check.
    
    context = {
        "branchData": {
            "academicYears": ["SE"],
            "divisions": {"SE": ["A"]},
            "workingDays": ["Monday"],
            "timeSlots": {
                 "startTime": "09:00",
                 "endTime": "17:00",
                 "slotDuration": 60
            },
            "recess_slot": 4,  # Index 4
            "labs": ["LabA"],
            "labBatchesPerYear": {"SE": 3},
            "classrooms": ["Room1"]
        },
        "smartInputData": {
            "subjects": [
                 {"name": "Math", "year": "SE", "division": "A", "weeklyLectures": 1, "type": "Theory"}
            ], 
            "teachers": [{"name": "Prof. Math", "subjects": ["Math"]}]
        }
    }
    
    scheduler = TimetableScheduler(context)
    
    try:
        print("Running Generation...")
        result = scheduler.generate()
        
        if result['success']:
            print("✅ SUCCESS: Generated a timetable (Gracefully Relaxed)!")
            print(f"Stats: {result.get('stats')}")
            # Check if gaps were introduced? 
            # We don't have explicit gap metrics in 'stats' yet, but success means relaxation worked.
            
            # Verify Structure
            tt = result['timetables'].get('SE', {}).get('A', {}).get('timetable', {})
            print(f"Timetable Keys: {list(tt.keys())}")
            
            # Check Monday
            monday_slots = tt.get('Monday', [])
            print(f"Monday Assignments: {len(monday_slots)} slots filled.")
            for s in monday_slots:
                print(f"  Slot {s['slot']}: {s.get('subject') or s.get('type')}")
                
        else:
            print(f"❌ FAILURE: Generation Failed even with relaxation.")
            print(f"   Stage: {result.get('stage')}")
            print(f"   Message: {result.get('message')}")

                
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strict_infeasibility()
