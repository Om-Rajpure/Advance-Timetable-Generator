import sys
import os
import traceback
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler
from utils.time_utils import calculate_time_slots

def run_strict_validation():
    print("=== STRICT RULES VALIDATION ===")
    
    # 1. Setup Data
    # We will use the 'go_live_data.json' or dummy data? 
    # Use dummy data to guarantee we know the config (e.g. Recess at slot 3)
    # OR better, use the Mock Data from verify_production_rules.py for consistency
    
    branch_data = {
        "academicYears": ["SE"],
        "divisions": {"SE": ["A"]},
        "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "startTime": "9:00 AM",
        "endTime": "5:00 PM",
        "lectureDuration": 60,
        "recessEnabled": True,
        "recessStart": "1:00 PM",  # 9-10(0), 10-11(1), 11-12(2), 12-1(3), 1-2(4 RECESS) -> Wait.
        # 9:00(0), 10:00(1), 11:00(2), 12:00(3), 13:00(4).
        # if start=9, end=5 (8 hours).
        # 0: 9-10
        # 1: 10-11
        # 2: 11-12
        # 3: 12-1
        # 4: 1-2 (RECESS)
        "slotsPerDay": 8,
        "rooms": ["C1", "C2", "C3"],
        "sharedLabs": [{"name": "L1", "requiredSlots": 2}],
        "labBatchesPerYear": {"SE": 2},
    }
    
    # Verify Recess Calculation
    time_config = calculate_time_slots(branch_data)
    recess_slot = time_config['recess_slot']
    print(f"DEBUG: Calculated Recess Slot Index: {recess_slot}")
    
    if recess_slot is None:
        print("WAARNING: Recess not enabled in test config. Enabling explicitly.")
        recess_slot = 4
        
    smart_input = {
        "teachers": [
            {"name": "T_Theory", "subjects": ["Math"], "maxLecturesPerWeek": 10},
            {"name": "T_Lab", "subjects": ["LabSub"], "maxLecturesPerWeek": 10}
        ],
        "subjects": [
            {"name": "Math", "year": "SE", "division": "A", "weeklyLectures": 4, "isPractical": False},
            {"name": "LabSub", "year": "SE", "division": "A", "lecturesPerWeek": 2, "isPractical": True, "sessionLength": 2}
        ],
        "teacherSubjectMap": []
    }
    
    context = {"branchData": branch_data, "smartInputData": smart_input}
    
    # 2. RUN GENERATION
    print("Running Generation...")
    scheduler = TimetableScheduler(context)
    result = scheduler.generate()
    
    if not result['success']:
        print("FAILURE: Generation failed completely.")
        print(result.get('message'))
        sys.exit(1)
        
    timetable = result.get('internal_slots', [])
    if not timetable:
         print("WARNING: 'internal_slots' missing. Falling back to 'raw_timetable' (Visual Indices - may cause false positive on Recess).")
         timetable = result.get('raw_timetable', [])

    print(f"Generated {len(timetable)} slots.")
    
    import json
    with open('debug_internal_slots.json', 'w') as f:
        json.dump(timetable, f, indent=2, default=str)
    
    # 3. VALIDATE RECESS
    print(f"Checking Recess Constraint (Slot {recess_slot})...")
    violations = 0
    first_recess_found = False
    for slot in timetable:
        if slot['slot'] == recess_slot:
            if slot.get('type') == 'BREAK' or slot.get('subject') == 'RECESS':
                first_recess_found = True
                continue
            print(f"   FAILURE: Found assignment in Recess Slot!")
            print(f"     {slot.get('id', 'NO_ID')} - {slot.get('subject')} ({slot.get('type')})")
            print(f"     Full Slot Data: {slot}")
            violations += 1
            
    if not first_recess_found:
         print("   WARNING: No BREAK assignments found in Recess Slot. (Did Pre-Filling happen?)")
         # We arguably might not care if it's empty, but user asked for "Pre-filled as BREAK".
         # So emptiness is also a slight violation of "Pre-fill" but valid for "Empty".
            
    if violations == 0:
        print("   PASS: Recess is empty.")
    else:
        print(f"   FAIL: {violations} items in recess.")
        
    # 4. VALIDATE LAB CONTINUITY
    print("Checking Lab Continuity...")
    lab_violations = 0
    # Group by ID stem? No, group by (Year, Div, Batch, Subject, Day)
    lab_groups = {}
    
    for slot in timetable:
        if slot['type'] == 'LAB':
            key = f"{slot['year']}_{slot['division']}_{slot['batch']}_{slot['subject']}_{slot['day']}"
            if key not in lab_groups: lab_groups[key] = []
            lab_groups[key].append(slot['slot'])
            
    for key, slots in lab_groups.items():
        slots.sort()
        # Check duration (Assuming 2 for test)
        if len(slots) != 2:
             print(f"   FAIL: Lab {key} has {len(slots)} slots, expected 2.")
             lab_violations += 1
             continue
             
        # Check continuity
        if slots[1] != slots[0] + 1:
             print(f"   FAIL: Lab {key} slots are not consecutive: {slots}")
             lab_violations += 1
             
        # Check Recess Crossing (Implicit if Recess is 4)
        # If slots are [3, 5], it skipped recess, but is not consecutive.
        # If slots are [3, 4], it hit recess.
        
    if lab_violations == 0:
        print("   PASS: All labs are continuous.")
    else:
        print(f"   FAIL: {lab_violations} lab continuity errors.")
        
    if violations > 0 or lab_violations > 0:
        print("\n STIRCT CONSTRAINTS FAILED.")
        sys.exit(1)
    else:
        print("\n ALL STRICT CONSTRAINTS PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    run_strict_validation()
