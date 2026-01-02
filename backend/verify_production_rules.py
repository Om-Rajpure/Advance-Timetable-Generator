
import sys
import os
import traceback

# Add backend to path (prioritize it)
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler
from constraints.constraint_engine import ConstraintEngine

# Mock Data
branch_data = {
    "academicYears": ["SE"],
    "divisions": {"SE": ["A"]},
    "workingDays": 5,
    "slotsPerDay": 6,
    "recessSlot": 3,
    "rooms": ["Classroom1", "Classroom2"],
    "labs": ["Lab1"], # Legacy
    "sharedLabs": [{"name": "Lab1", "requiredSlots": 2}, {"name": "Lab2", "requiredSlots": 2}],
    "labBatchesPerYear": {"SE": 2},
    "classrooms": {"SE": ["Classroom1"]}
}

smart_input = {
    "teachers": [
        {"name": "T1", "subjects": ["Math"], "maxLecturesPerWeek": 20},
        {"name": "T2", "subjects": ["Physics"], "maxLecturesPerWeek": 20},
        {"name": "T3", "subjects": ["Python Lab"], "maxLecturesPerWeek": 20},
        {"name": "T4", "subjects": ["Physics Lab"], "maxLecturesPerWeek": 20}
    ],
    "subjects": [
        {"name": "Math", "year": "SE", "division": "A", "lecturesPerWeek": 3, "isPractical": False},
        {"name": "Physics", "year": "SE", "division": "A", "lecturesPerWeek": 2, "isPractical": False},
        {"name": "Python Lab", "year": "SE", "division": "A", "lecturesPerWeek": 2, "isPractical": True, "batches": 2, "sessionLength": 2},
        {"name": "Physics Lab", "year": "SE", "division": "A", "lecturesPerWeek": 2, "isPractical": True, "batches": 2, "sessionLength": 2}
    ],
    "teacherSubjectMap": [
        {"subjectName": "Math", "teacherName": "T1"},
        {"subjectName": "Physics", "teacherName": "T2"},
        {"subjectName": "Python Lab", "teacherName": "T3"},
        {"subjectName": "Physics Lab", "teacherName": "T4"}
    ]
}

context = {
    "branchData": branch_data,
    "smartInputData": smart_input
}

def run_test():
    print("Initializing Scheduler...")
    try:
        scheduler = TimetableScheduler(context)
        print("Starting Generation...")
        result = scheduler.generate()
        
        if result['success']:
            print("SUCCESS: Timetable Generated!")
            print(f"Violations: {result.get('violations')}")
            
            # Verify specific rules
            timetable = result['timetable']
            
            # Check 1: Recess Crossing
            recess_violations = 0
            for slot in timetable:
                if slot['type'] == 'LAB':
                     # Slot is start time? No, LabScheduler produces multiple slots.
                     # But we can check if any assigned slot is recess (Assuming index 3 is recess)
                     if slot['slot'] == 3:
                         print(f"FAILURE: Lab assigned to recess slot! {slot}")
                         recess_violations += 1
            if recess_violations == 0:
                print("PASS: No recess crossing.")
                
            # Check 2: Simultaneous Batches (Rule 10)
            # Find all lab slots for SE-A
            lab_slots = [s for s in timetable if s['type'] == 'LAB']
            # Group by Day/Slot
            grouped = {}
            for s in lab_slots:
                key = (s['day'], s['slot'])
                if key not in grouped: grouped[key] = []
                grouped[key].append(s)
            
            all_sync = True
            for k, batch_slots in grouped.items():
                if len(batch_slots) != 2:
                    print(f"WARNING: Batch count mismatch at {k}. Got {len(batch_slots)}, expected 2.")
                    # Could happen if one batch has lab and other doesn't? 
                    # Ideally strictly 2 for Rotation.
                    # But if we have 2 batches and 2 subjects, we expect both to run.
                    all_sync = False
            
            if all_sync:
                print("PASS: Batches are synchronized.")
            else:
                print("WARNING: Some batches might not be synchronized (check warnings).")

            # Check 3: Unique Subjects per batch
            for k, batch_slots in grouped.items():
                subjects = set(s['subject'] for s in batch_slots)
                if len(subjects) != len(batch_slots):
                    print(f"FAILURE: Duplicate subject in simultaneous batches at {k}: {subjects}")
                else:
                    pass # Good
                    
        else:
            print("FAILURE: Generation Failed")
            print(result['message'])
            print(result.get('blockers'))
            
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
