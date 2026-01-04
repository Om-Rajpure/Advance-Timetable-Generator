
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

def run_test():
    print("🚀 TESTING DYNAMIC ROOM ALLOCATION...")
    
    # 1. Setup Data with SCARCE ROOMS
    # 2 Rooms total.
    # 3 Classes (Years) needing slots at same time.
    
    branch_data = {
        "academicYears": ["SE", "TE", "BE"],
        "divisions": {
            "SE": ["A"],
            "TE": ["A"],
            "BE": ["A"]
        },
        "days": ["Monday"], # Just 1 day to force conflict
        "workingDays": ["Monday"],
        "slotsPerDay": 3,
        # KEY: Only 2 Classrooms!
        "classrooms": ["Room_101", "Room_102"], 
        "labs": [],
        "sharedLabs": [],
        "labBatchesPerYear": {"SE": 1, "TE": 1, "BE": 1}
    }

    smart_input_data = {
        "subjects": [
            # SE Subjects
            {"name": "SE_Sub1", "year": "SE", "type": "Lecture", "weeklyLectures": 1},
            {"name": "SE_Sub2", "year": "SE", "type": "Lecture", "weeklyLectures": 1},
            {"name": "SE_Sub3", "year": "SE", "type": "Lecture", "weeklyLectures": 1},
            
            # TE Subjects
            {"name": "TE_Sub1", "year": "TE", "type": "Lecture", "weeklyLectures": 1},
            {"name": "TE_Sub2", "year": "TE", "type": "Lecture", "weeklyLectures": 1},
            {"name": "TE_Sub3", "year": "TE", "type": "Lecture", "weeklyLectures": 1},

            # BE Subjects
            {"name": "BE_Sub1", "year": "BE", "type": "Lecture", "weeklyLectures": 1},
            {"name": "BE_Sub2", "year": "BE", "type": "Lecture", "weeklyLectures": 1},
            {"name": "BE_Sub3", "year": "BE", "type": "Lecture", "weeklyLectures": 1},
        ],
        "teachers": [
            {"name": "T1", "subjects": ["SE_Sub1", "TE_Sub1", "BE_Sub1"]}, 
            {"name": "T2", "subjects": ["SE_Sub2", "TE_Sub2", "BE_Sub2"]},
            {"name": "T3", "subjects": ["SE_Sub3", "TE_Sub3", "BE_Sub3"]},
            {"name": "T4", "subjects": []},
            {"name": "T5", "subjects": []},
            {"name": "T6", "subjects": []}
        ],
        "teacherSubjectMap": []
    }

    context = {
        "branchData": branch_data,
        "smartInputData": smart_input_data
    }
    
    # Run
    scheduler = TimetableScheduler(context, max_iterations=100)
    result = scheduler.generate()
    
    print(f"Success: {result.get('success')}")
    timetables = result.get('timetables', {})
    
    # Analyze Room Usage per Slot
    # Map: Slot -> [Rooms Used]
    slot_usage = {}
    
    for year, divs in timetables.items():
        for div, data in divs.items():
            tt = data.get('timetable', {})
            for day, slots in tt.items():
                for slot in slots:
                    time_idx = slot['slot']
                    room = slot.get('room')
                    
                    if time_idx not in slot_usage: slot_usage[time_idx] = []
                    slot_usage[time_idx].append(f"{year}-{div}:{room}")

    print("\n--- ROOM USAGE ANALYSIS ---")
    for s_idx in sorted(slot_usage.keys()):
        print(f"Slot {s_idx}: {slot_usage[s_idx]}")
        
    # Validation:
    # 1. No distinct room should appear twice in the same slot (Already enforced by logic, but checking print)
    # 2. We should see Room_101 AND Room_102 being used.
    # 3. We might see one class missing a slot if strict room constraint works (since 3 classes > 2 rooms).
    
    assigned_count = sum(len(x) for x in slot_usage.values())
    print(f"\nTotal Lectures Scheduled: {assigned_count}/9 (Expected < 9 due to room shortage)")

if __name__ == "__main__":
    run_test()
