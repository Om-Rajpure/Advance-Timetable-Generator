
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from engine.lab_scheduler import LabScheduler
from engine.state_manager import TimetableState

def debug_se_a_labs():
    print("=== DEBUGGING SE-A LAB SCHEDULING ===")
    
    # Mock Context based on test_generation.py
    context = {
        "branchData": {
            "academicYears": ["SE"],
            "workingDays": ["Monday"], # Just 1 day to force collision/density checks
            "slotsPerDay": 6,
            "divisions": {"SE": ["A"]},
            "rooms": ["Room-1", "Room-2", "Room-3"],
            "sharedLabs": [
                {"name": "Lab-1"},
                {"name": "Lab-2"},
                {"name": "Lab-3"}
            ],
            "labBatchesPerYear": {"SE": 3}
        },
        "smartInputData": {
            "subjects": [
                # SE-A Labs
                {"name": "Python Lab", "year": "SE", "division": "A", "type": "Practical", "isPractical": True},
                {"name": "AI Lab", "year": "SE", "division": "A", "type": "Practical", "isPractical": True}
            ],
            "teachers": [
                # Teachers from test_generation.py
                {"name": "Neha", "subjects": ["Python Lab"]}, # 1 Py
                {"name": "John", "subjects": ["AI Lab"]},     # 1 AI
                {"name": "Sarah", "subjects": ["Python Lab", "AI Lab"]}, # 1 Py, 1 AI
                {"name": "Amit", "subjects": ["AI Lab"]}      # 1 AI
                
                # Total for Parallel of 3 Batches:
                # Need 3 distinct teachers.
                # Py Teachers: Neha, Sarah (2)
                # AI Teachers: John, Sarah, Amit (3)
                
                # Possible Combo: 
                # A1: Py(Neha), A2: Py(Sarah), A3: AI(John) -> Valid
                # A1: AI(Amit), A2: AI(John), A3: AI(Sarah) -> Valid
            ]
        }
    }
    
    state = TimetableState(context)
    scheduler = LabScheduler(state, context)
    
    class_info = {
        "year": "SE",
        "division": "A",
        "batches": ["A1", "A2", "A3"]
    }
    
    print("\nAttempting to schedule...")
    success = scheduler.schedule_class_labs(class_info)
    
    print(f"\nResult: {success}")
    
    # Inspect State
    print("\nSlot Assignments:")
    count = 0
    for key, val in state.slot_grid.items():
        if isinstance(val, list):
             for v in val:
                 print(f"  {key}: {v.get('batch')} - {v.get('subject')} ({v.get('teacher')})")
                 count+=1
        else:
             print(f"  {key}: {val.get('batch')} - {val.get('subject')} ({val.get('teacher')})")
             count+=1
             
    if count == 0:
        print("❌ NO SLOTS ASSIGNED!")
    else:
        print(f"✅ {count} Slots Assigned.")

if __name__ == "__main__":
    debug_se_a_labs()
