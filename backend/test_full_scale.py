
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.scheduler import TimetableScheduler

def test_full_scale_generation():
    print("🚀 STARTING FULL SCALE GENERATION TEST (FE, SE, TE, BE)")
    
    # 1. Full Config
    context = {
        "branchData": {
            "academicYears": ["FE", "SE", "TE", "BE"],
            "divisions": {
                "FE": ["A", "B"],
                "SE": ["A", "B"],
                "TE": ["A"],
                "BE": ["A"]
            },
            "slotsPerDay": 6,
            "rooms": ["R1", "R2", "R3", "R4", "R5"],
            "sharedLabs": [
                {"name": "Lab-1", "capacity": 30},
                {"name": "Lab-2", "capacity": 30},
                {"name": "Lab-3", "capacity": 30},
                 {"name": "Lab-4", "capacity": 30}
            ],
            "labBatchesPerYear": {
                "FE": 3, "SE": 3, "TE": 3, "BE": 3
            }
        },
        "smartInputData": {
            "teachers": [
                {"name": "T1", "subjects": ["Sub1_FE"]},
                {"name": "T2", "subjects": ["Sub1_SE"]},
                {"name": "T3", "subjects": ["Sub1_TE"]},
                {"name": "T4", "subjects": ["Sub1_BE"]},
                {"name": "T_Lab", "subjects": ["Lab_FE", "Lab_SE", "Lab_TE", "Lab_BE"]},
                {"name": "T_Lab2", "subjects": ["Lab_FE", "Lab_SE", "Lab_TE", "Lab_BE"]},
                {"name": "T_Lab3", "subjects": ["Lab_FE", "Lab_SE", "Lab_TE", "Lab_BE"]}
            ],
            "subjects": [
                # FE
                {"name": "Sub1_FE", "year": "FE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False},
                {"name": "Lab_FE", "year": "FE", "type": "Practical", "lecturesPerWeek": 4, "isPractical": True},
                # SE
                {"name": "Sub1_SE", "year": "SE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False},
                {"name": "Lab_SE", "year": "SE", "type": "Practical", "lecturesPerWeek": 4, "isPractical": True},
                 # TE
                {"name": "Sub1_TE", "year": "TE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False},
                {"name": "Lab_TE", "year": "TE", "type": "Practical", "lecturesPerWeek": 4, "isPractical": True},
                 # BE
                {"name": "Sub1_BE", "year": "BE", "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False},
                {"name": "Lab_BE", "year": "BE", "type": "Practical", "lecturesPerWeek": 4, "isPractical": True}
            ]
        }
    }
    
    scheduler = TimetableScheduler(context, max_iterations=1000)
    result = scheduler.generate()
    
    print(f"\n✅ Result Status: {result['success']}")
    
    # Verify Hierarchy
    tt = result.get('timetables', {})
    print(f"Keys Generated: {list(tt.keys())}")
    
    assert "FE" in tt, "Missing FE"
    assert "SE" in tt, "Missing SE"
    assert "TE" in tt, "Missing TE"
    assert "BE" in tt, "Missing BE"
    
    assert "A" in tt["FE"], "Missing FE-A"
    assert "B" in tt["FE"], "Missing FE-B"
    
    print("\n✅ Hierarchy Verification Passed")
    
    # Verify Lab Concurrency
    # Check FE-A for parallel batches
    fe_a_timetable = tt["FE"]["A"]["timetable"]
    # Flatten
    slots = []
    for day in fe_a_timetable.values():
        slots.extend(day)
        
    lab_entries = [s for s in slots if s['type'] == 'LAB']
    print(f"FE-A Lab Entries: {len(lab_entries)}")
    
    # Count duplicates per slot
    slot_map = {}
    for l in lab_entries:
        key = f"{l['day']}_{l['slot']}"
        slot_map[key] = slot_map.get(key, 0) + 1
        
    max_concurrency = max(slot_map.values()) if slot_map else 0
    print(f"Max Concurrency in one slot: {max_concurrency}")
    
    if max_concurrency < 2:
        print("⚠️ WARNING: No parallel batches found! (Expected 3)")
    else:
        print(f"✅ Parallel Batches Confirmed (Count: {max_concurrency})")
        
    return True

if __name__ == "__main__":
    test_full_scale_generation()
