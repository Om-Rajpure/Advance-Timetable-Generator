import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

def test_recess_and_compulsory_days():
    print("=== TEST: STRICT RECESS & COMPULSORY DAYS ===")
    
    # SETUP:
    # 5 Working Days (Mon-Fri)
    # Recess at Slot 4 (0-indexed)
    # Total Slots: 8
    
    # SUBJECTS:
    # "Math": 6 Lectures (Ideally 1 or 2 per day)
    # If standard balanced logic is used: 6 / 5 = 1.2 -> 1 or 2 per day.
    # Should use ALL days.
    # 
    # "Physics": 1 Lecture (Total 7) => Coverage should be easy.
    
    # IMPORTANT: We want to test minimal load too? 
    # Let's start with just enough sessions to cover days (5 sessions).
    
    context = {
        "branchData": {
            "academicYears": ["SE"],
            "divisions": {"SE": ["A"]},
            "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
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
                 {"name": "Math", "year": "SE", "division": "A", "weeklyLectures": 3, "type": "Theory"},
                 {"name": "Physics", "year": "SE", "division": "A", "weeklyLectures": 3, "type": "Theory"}
            ], 
            "teachers": [{"name": "Prof. T", "subjects": ["Math", "Physics"]}]
        }
    }
    
    scheduler = TimetableScheduler(context)
    
    try:
        print("Running Generation...")
        result = scheduler.generate()
        
        if not result['success']:
            print("❌ FAILURE: Generation Failed.")
            return

        tt = result['timetables'].get('SE', {}).get('A', {}).get('timetable', {})
        print(f"Timetable Keys: {list(tt.keys())}")
        
        # VERIFY 1: COMPULSORY DAYS
        # Expect keys for Mon, Tue, Wed, Thu, Fri
        missing_days = []
        for day in context['branchData']['workingDays']:
            if day not in tt or not tt[day]:
                missing_days.append(day)
                
        if missing_days:
            print(f"❌ COMPULSORY DAY FAILURE: Missing days {missing_days}")
        else:
            print("✅ compulsory Days: All 5 days have classes.")
            
        # VERIFY 2: RECESS (Slot 4)
        recess_violation = False
        recess_slot = 4
        for day, slots in tt.items():
            for s in slots:
                # Scheduler output currently uses 0-based 'slot' from _fill_day or 1-based?
                # scheduler.py format_to_canonical converts to 1-based.
                # BUT 'result' from scheduler.generate() returns the Canonical format?
                # Let's check format_to_canonical in scheduler.py
                
                # ... 
                # clean_slot['slot'] = visual_idx (raw + 1)
                
                # So Recess Slot 4 (0-based) becomes Slot 5 (1-based).
                # Wait, 'recess_slot' config is 0-based logic.
                # If output is 1-based, we check if slot == 5.
                
                idx = int(s['slot']) 
                if idx == recess_slot + 1:
                    print(f"❌ RECESS VIOLATION: {s} on {day} uses visual slot {idx}")
                    recess_violation = True
                    
        if not recess_violation:
            print("✅ Recess: Slot 5 (Index 4) is clean.")
            
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recess_and_compulsory_days()
