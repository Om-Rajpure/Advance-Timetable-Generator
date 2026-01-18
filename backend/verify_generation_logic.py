
import sys
import os
import traceback

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from engine.scheduler import TimetableScheduler

def run_verification():
    print("=== VERIFYING STRICT GENERATION LOGIC ===")
    
    # ---------------------------------------------------------
    # TEST CASE 1: CONSTRAINT FAILURE (Should return GENERATION_FAILED)
    # ---------------------------------------------------------
    print("\n[TEST 1] Force Constraint Failure (Insufficient Labs)")
    
    context_fail = {
        "branchData": {
            "academicYears": ["SE"],
            "workingDays": ["Monday"],
            "divisions": {"SE": ["A"]},
            "slotsPerDay": 4,
            "rooms": ["Room-1"],
            "labs": [], # NO LABS -> Fails Practical
            "labBatchesPerYear": {"SE": 1},
            "recessEnabled": True,
            "recessStart": "12:00 PM",
            "lectureDuration": 60,
            "startTime": "09:00 AM",
            "endTime": "01:00 PM"
        },
        "smartInputData": {
            "subjects": [
                {"name": "Lab1", "year": "SE", "division": "A", "type": "Practical", "batches": 1, "lecturesPerWeek": 1}
            ],
            "teachers": [
                {"name": "T1", "subjects": ["Lab1"]}
            ]
        }
    }
    
    scheduler_1 = TimetableScheduler(context_fail, max_iterations=10)
    
    try:
        print("Running generation (Expect Failure)...")
        result = scheduler_1.generate()
        
        print(f"Result Stage: {result.get('stage')}")
        
        if result.get('success') is False:
             if result.get('stage') == "GENERATION_FAILED":
                 print("✅ SUCCESS: Generation failed with correct stage 'GENERATION_FAILED'.")
             else:
                 print(f"❌ FAILURE: Generation failed but stage is '{result.get('stage')}' (Expected 'GENERATION_FAILED')")
                 return False
        else:
            print("❌ FAILURE: Generation succeeded unexpectedly!")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: Crashed unexpectedly! {e}")
        traceback.print_exc()
        return False

    # ---------------------------------------------------------
    # TEST CASE 2: CORRECT DATA (Should SUCCEED)
    # ---------------------------------------------------------
    print("\n[TEST 2] Valid Data for All Divisions")
    
    context_valid = {
        "branchData": {
            "academicYears": ["SE"],
            "workingDays": ["Monday", "Tuesday"],
            "divisions": {"SE": ["A"]},
            "slotsPerDay": 4,
            "rooms": ["Room-1"],
            "labs": [],
            "recessEnabled": False, # Simplify
            "lectureDuration": 60,
            "startTime": "09:00 AM",
            "endTime": "12:00 PM"
        },
        "smartInputData": {
             "subjects": [
                {"name": "Theory1", "year": "SE", "division": "A", "type": "Lecture", "lecturesPerWeek": 2}
             ],
            "teachers": [
                {"name": "T1", "subjects": ["Theory1"]}
            ]
        }
    }
    
    scheduler_2 = TimetableScheduler(context_valid, max_iterations=100)
    
    try:
        print("Running generation (Expect Success)...")
        result = scheduler_2.generate()
        
        if not result.get('success'):
             print(f"❌ FAILURE: Generation failed with valid data. Msg: {result.get('message')}")
             # Print blockers if any
             if result.get('blockers'):
                 print(f"Blockers: {result.get('blockers')}")
             return False
             
        timetables = result.get('timetables', {})
        
        # Verify SE-A
        if "SE" in timetables and "A" in timetables["SE"]:
             print(">> Verified: SE-A generated.")
        else:
             print("❌ FAILURE: SE-A missing from result.")
             return False
             
        print("✅ SUCCESS: All divisions generated.")
        return True

    except Exception as e:
        print(f"❌ FAILURE: Crashed unexpected on valid data: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
