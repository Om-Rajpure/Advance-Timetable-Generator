
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

def run_user_test():
    print("🚀 PREPARING USER DUMMY DATA TEST...")
    
    # --- 1. RAW USER DATA ---
    user_data = {
      "years": ["SE", "TE", "BE"],
      "divisions": {
        "SE": ["A", "B"],
        "TE": ["A", "B"],
        "BE": ["A", "B"]
      },
      "batches": ["A", "B", "C"],
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "slots_per_day": 6,
      "subjects": {
        "SE": {
          "theory": ["SE_T1", "SE_T2", "SE_T3", "SE_T4", "SE_T5"],
          "labs": ["SE_L1", "SE_L2", "SE_L3"]
        },
        "TE": {
          "theory": ["TE_T1", "TE_T2", "TE_T3", "TE_T4", "TE_T5"],
          "labs": ["TE_L1", "TE_L2", "TE_L3"]
        },
        "BE": {
          "theory": ["BE_T1", "BE_T2", "BE_T3", "BE_T4", "BE_T5"],
          "labs": ["BE_L1", "BE_L2", "BE_L3"]
        }
      },
      "teachers": {
        "SE_T1": "Teacher_1", "SE_T2": "Teacher_2", "SE_T3": "Teacher_3", "SE_T4": "Teacher_4", "SE_T5": "Teacher_5",
        "SE_L1": "Teacher_6", "SE_L2": "Teacher_7", "SE_L3": "Teacher_8",
        "TE_T1": "Teacher_9", "TE_T2": "Teacher_10", "TE_T3": "Teacher_11", "TE_T4": "Teacher_12", "TE_T5": "Teacher_13",
        "TE_L1": "Teacher_14", "TE_L2": "Teacher_15", "TE_L3": "Teacher_16",
        "BE_T1": "Teacher_17", "BE_T2": "Teacher_18", "BE_T3": "Teacher_19", "BE_T4": "Teacher_20", "BE_T5": "Teacher_21",
        "BE_L1": "Teacher_22", "BE_L2": "Teacher_23", "BE_L3": "Teacher_24"
      },
      "labs": ["Lab_1", "Lab_2", "Lab_3"],
      "classrooms": ["Room_101", "Room_102", "Room_103", "Room_104"]
    }

    # --- 2. TRANSFORM TO BACKEND CONTEXT ---
    
    # A. Branch Data
    branch_data = {
        "academicYears": user_data['years'],
        "divisions": user_data['divisions'], # Already in Correct Dict Format {"Year": ["A", "B"]}
        "slotsPerDay": user_data['slots_per_day'],
        "workingDays": user_data['days'],
        "rooms": user_data['classrooms'],
        "labs": [], # Legacy
        "sharedLabs": [{"name": l, "capacity": 30} for l in user_data['labs']],
        "labBatchesPerYear": {y: len(user_data['batches']) for y in user_data['years']} 
    }

    # B. Smart Input Data
    smart_input_data = {
        "subjects": [],
        "teachers": []
    }

    # Map Teachers to Subjects for "teachers" list construction
    teacher_map = {} # Name -> [Subjects]

    # Process Subjects
    for year, subs in user_data['subjects'].items():
        # Theory
        for subj_name in subs['theory']:
            smart_input_data['subjects'].append({
                "name": subj_name,
                "year": year,
                "type": "Lecture",
                "lecturesPerWeek": 3, # DEFAULT ASSUMPTION
                "isPractical": False
            })
            
            # Map Teacher
            t_name = user_data['teachers'].get(subj_name, "TBA")
            if t_name not in teacher_map: teacher_map[t_name] = []
            teacher_map[t_name].append(subj_name)

        # Labs
        for subj_name in subs['labs']:
            smart_input_data['subjects'].append({
                "name": subj_name,
                "year": year,
                "type": "Practical",
                "lecturesPerWeek": 4, # DEFAULT ASSUMPTION (2 slots * 2 sessions approx? Or just 4 slots load)
                "isPractical": True
            })
            
            # Map Teacher
            t_name = user_data['teachers'].get(subj_name, "TBA")
            if t_name not in teacher_map: teacher_map[t_name] = []
            teacher_map[t_name].append(subj_name)

    # Process Teachers
    for t_name, t_subjects in teacher_map.items():
        smart_input_data['teachers'].append({
            "name": t_name,
            "subjects": t_subjects
        })

    context = {
        "branchData": branch_data,
        "smartInputData": smart_input_data
    }
    
    # --- 3. EXECUTE GENERATION ---
    print("\n📦 CONTEXT BUILT. INITIALIZING SCHEDULER...")
    try:
        scheduler = TimetableScheduler(context, max_iterations=5000) # Increased iterations for full data
        result = scheduler.generate()
        
        print("\n--- GENERATION RESULT ---")
        print(f"Success: {result.get('success')}")
        
        if result.get('success'):
            timetables = result.get('timetables', {})
            print(f"Generated Years: {list(timetables.keys())}")
            for year, divs in timetables.items():
                print(f"  {year}: {list(divs.keys())}")
                for div, data in divs.items():
                    tt = data.get('timetable', {})
                    total_slots = sum(len(d) for d in tt.values())
                    print(f"    {year}-{div}: {total_slots} slots filled")
        else:
            print(f"Failure Stage: {result.get('stage')}")
            print(f"Errors: {result.get('errors')}")
            print(f"Values Crash Details: {result.get('details')}")

    except Exception as e:
        print(f"\n❌ CRITICAL CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_user_test()
