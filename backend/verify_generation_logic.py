
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
    # TEST CASE 1: MISSING DATA (Should FAIL LOUDLY)
    # ---------------------------------------------------------
    print("\n[TEST 1] Missing Data for BE-A")
    
    context_missing = {
        "branchData": {
            "academicYears": ["SE", "BE"],
            "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "divisions": {
                "SE": ["A"],
                "BE": ["A"]  # Defined here but NO subjects below
            },
            "slotsPerDay": 4,
            "rooms": ["Room-1", "Room-2"],
            "labs": [],
            "labBatchesPerYear": {"SE": 3, "BE": 3}
        },
        "smartInputData": {
            "subjects": [
                # ONLY SE-A subjects
                {"name": "SE Sub 1", "year": "SE", "division": "A", "type": "Lecture"},
                {"name": "SE Sub 2", "year": "SE", "division": "A", "type": "Lecture"}
            ],
            "teachers": [
                {"name": "T1", "subjects": ["SE Sub 1", "SE Sub 2", "BE Sub 1"]}
            ]
        }
    }
    
    scheduler_1 = TimetableScheduler(context_missing, max_iterations=100)
    
    try:
        print("Running generation (Expect Crash/Failure)...")
        result = scheduler_1.generate()
        
        if result.get('success') is False:
             print("✅ SUCCESS: Generation failed explicitly as expected!")
             msg = result.get('message', '') + " " + result.get('details', '')
             print(f"Error Message: {msg}")
             if "No subjects found" in msg or "CRITICAL DATA ERROR" in msg or "FAILED to generate" in msg:
                 print(">> Verified: Correct error caught.")
             else:
                 print(f">> Warning: Failed but with different error? {msg}")
        else:
            print("❌ FAILURE: Generation succeeded silently but should have failed!")
            print(f"Timetables: {result.get('timetables').keys()}")
            return False
            
    except Exception as e:
        print("✅ SUCCESS: Generation execution crashed!")  # This is also fine
        print(f"Error: {e}")

    # ---------------------------------------------------------
    # TEST CASE 2: CORRECT DATA (Should SUCCEED)
    # ---------------------------------------------------------
    print("\n[TEST 2] Valid Data for All Divisions")
    
    context_valid = context_missing.copy()
    # Add BE-A subjects
    context_valid['smartInputData']['subjects'] = [
        {"name": "SE Sub 1", "year": "SE", "division": "A", "type": "Lecture", "lecturesPerWeek": 2, "subjects":["SE Sub 1"]},
        {"name": "BE Sub 1", "year": "BE", "division": "A", "type": "Lecture", "lecturesPerWeek": 2, "subjects":["BE Sub 1"]}
    ]
    
    scheduler_2 = TimetableScheduler(context_valid, max_iterations=100)
    
    try:
        print("Running generation (Expect Success)...")
        result = scheduler_2.generate()
        
        if not result.get('success'):
             print(f"❌ FAILURE: Generation failed with valid data. Msg: {result.get('message')}")
             return False
             
        timetables = result.get('timetables', {})
        
        # Verify SE-A
        if "SE" in timetables and "A" in timetables["SE"]:
             print(">> Verified: SE-A generated.")
        else:
             print("❌ FAILURE: SE-A missing from result.")
             return False
             
        # Verify BE-A
        if "BE" in timetables and "A" in timetables["BE"]:
             print(">> Verified: BE-A generated.")
        else:
             print("❌ FAILURE: BE-A missing from result (Silent Skip?).")
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
