
import json
import os
import sys

# Setup Path
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, "backend")
sys.path.append(backend_dir)

# Now we can import engine modules as if we are in backend package
# BUT scheduler uses relative imports like 'from .state_manager'.
# To fix this, we must run this script from the parent dir and use -m, 
# OR we can just hack the sys.modules or use source file loading.
# EASIEST: Just import internal classes directly if possible, or use standard import if sys.path is right.

# If we append 'backend/engine' to sys.path, 'import scheduler' works but 'from .state_manager' fails.
# If we append 'backend' to sys.path, 'from engine.scheduler import ...' might work if we treat it as package.

# Let's try inserting the root so 'backend.engine' works
sys.path.insert(0, current_dir)

from backend.engine.scheduler import TimetableScheduler

# Define minimal valid context
context = {
    "branchData": {
        "academicYears": ["SE"],
        "divisions": {"SE": ["A"]},
        "classrooms": {"SE": ["Room 304"]}, # Real Room configuration
        "workingDays": ["Monday"],
        "startTime": "9:00 AM",
        "lectureDuration": 60,
        "labs": [], # Legacy
        "sharedLabs": []
    },
    "smartInputData": {
         "subjects": [{"name": "Theory1", "code": "TH1", "year": "SE", "weeklyLectures": 1, "type": "Theory"}],
         "teachers": [{"name": "T1", "subject": "Theory1"}],
         "teacherSubjectMap": [{"teacherName": "T1", "subjectName": "Theory1"}]
    }
}

try:
    scheduler = TimetableScheduler(context)
    # We won't run full generate() because it needs CandidateGenerator etc.
    # Instead, we will simulate the specific function call that Formats Output.
    
    # 1. Simulate a raw slot from internal state
    raw_slots = [
        {
            "id": "test-slot-1",
            "year": "SE",
            "division": "A",
            "day": "Monday",
            "slot": 1,
            "subject": "Theory1",
            "type": "THEORY",
            # "room": None  <-- Intentional missing room to trigger logic
        }
    ]
    
    print("--- INPUT SLOT ---")
    print(raw_slots[0])
    
    # 2. Call format_to_canonical
    result = scheduler.format_to_canonical(raw_slots)
    
    print("\n--- OUTPUT STRUCTURE ---")
    print(json.dumps(result, indent=2))
    
    # 3. Check for Room
    slot_out = result.get('SE-A', {}).get('Monday', [])[0]
    if 'room' in slot_out:
        print(f"\n✅ SUCCESS: Room key present: '{slot_out['room']}'")
    else:
        print("\n❌ FAILURE: Room key MISSING.")

except Exception as e:
    import traceback
    traceback.print_exc()
