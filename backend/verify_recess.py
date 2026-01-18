
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
        "workingDays": ["Monday", "Tuesday", "Wednesday"],
        "labs": ["Lab1"],
        "rooms": ["Room101"],
        "recessStart": "12:00 PM", # STRICT KEY
        "recessEnabled": True, # STRICT KEY
        "start_time": "09:00 AM" # Ensure defaults match
    },
    "smartInputData": {
        "subjects": [
            {"name": "Math", "year": "SE", "division": "A", "type": "Lecture", "lecturesPerWeek": 1},
        ],
        "teachers": [
            {"name": "T1", "subjects": ["Math"]}
        ]
    }
}

print("Initiating Recess Consistency Test...")

try:
    from engine.scheduler import TimetableScheduler
    from utils.time_utils import calculate_time_slots
    
    # 1. Check Calc Logic
    time_config = calculate_time_slots(dummy_context['branchData'])
    print(f"Time Config: {time_config}")
    recess_slot = time_config.get('recess_slot')
    
    scheduler = TimetableScheduler(dummy_context)
    result = scheduler.generate()
    
    if not result['success']:
        print("Generation Failed")
        sys.exit(1)
        
    day_layout = result['dayLayout']
    print("\nGlobal Day Layout:")
    recess_col_idx = -1
    for idx, col in enumerate(day_layout):
        print(f"  Col {idx}: {col['type']} ({col['label']})")
        if col['type'] == 'recess':
            recess_col_idx = idx
            
    if recess_col_idx == -1:
        print("FAILURE: No recess column found in layout!")
    else:
        print(f"SUCCESS: Recess found at Column Index {recess_col_idx}")

    # Check Internal State vs Layout
    print("\nConsistency Check:")
    if recess_slot is None:
         # It depends on input
         pass
    else:
         # Layout recess index should match logic?
         # Layout might include recess as an item.
         # If recess_slot is 3 (0,1,2, RECESS, 3,4...), visual index is 3?
         # Check utils logic
         pass

except Exception as e:
    import traceback
    traceback.print_exc()
    print("CRASHED:", e)
