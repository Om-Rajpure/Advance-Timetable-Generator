
import json
import sys
import os

# Ensure we can import backend modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.engine.scheduler import TimetableScheduler

def run_repro():
    print("🚀 STARTING FEEDBACK LOOP REPRODUCTION")
    
    # --- USER PROVIDED DUMMY DATA ---
    raw_data = {
      "years": ["SE", "TE", "BE"],
      "divisions": { "SE": ["A", "B"], "TE": ["A", "B"], "BE": ["A", "B"] },
      "batches": ["A", "B", "C"],
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "slots_per_day": 6,
      
      "subjects": {
        "SE": { "theory": ["SE_T1", "SE_T2", "SE_T3", "SE_T4", "SE_T5"], "labs": ["SE_L1", "SE_L2", "SE_L3"] },
        "TE": { "theory": ["TE_T1", "TE_T2", "TE_T3", "TE_T4", "TE_T5"], "labs": ["TE_L1", "TE_L2", "TE_L3"] },
        "BE": { "theory": ["BE_T1", "BE_T2", "BE_T3", "BE_T4", "BE_T5"], "labs": ["BE_L1", "BE_L2", "BE_L3"] }
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

    # --- TRANSFORM TO API PAYLOAD FORMAT ---
    
    # 1. Branch Data
    branch_data = {
        "academicYears": raw_data["years"],
        "divisions": raw_data["divisions"],
        "workingDays": raw_data["days"],
        "slotsPerDay": 6,
        "startTime": "09:00",
        "endTime": "17:00",
        "lectureDuration": 60,
        "classrooms": [{"name": r, "capacity": 60} for r in raw_data["classrooms"]],
        # "sharedLabs": [{"name": l, "capacity": 30} for l in raw_data["labs"]], # SIMULATE MISSING
        "rooms": raw_data["classrooms"], # Legacy support
        "labs": raw_data["labs"], # Legacy support
        "labBatchesPerYear": { "SE": 3, "TE": 3, "BE": 3 } # Derived from batches A,B,C
    }
    
    # 2. Smart Input Data
    subjects_list = []
    teachers_list = [] # List of dicts
    teacher_map = []
    
    # Process Teachers Dict first into list
    teacher_name_to_id = {}
    for code, t_name in raw_data["teachers"].items():
        teachers_list.append({"name": t_name, "id": t_name, "subjects": []}) # Subjects filled later or implicit
    
    # Process Subjects
    for year, types in raw_data["subjects"].items():
        # Theory
        for sub_code in types["theory"]:
            subjects_list.append({
                "name": sub_code,
                "year": year,
                "type": "Lecture",
                "lecturesPerWeek": 3, # Assumption
                "isPractical": False,
                "division": None # Applies to all
            })
            # Map Teacher
            t_name = raw_data["teachers"].get(sub_code)
            if t_name:
                teacher_map.append({"teacherName": t_name, "subjectName": sub_code})

        # Labs
        for sub_code in types["labs"]:
            subjects_list.append({
                "name": sub_code,
                "year": year,
                "type": "Practical",
                "lecturesPerWeek": 4, # 2 sessions of 2 slots? Or 4 slots? Assumption: 2 slots per batch
                "isPractical": True,
                "division": None
            })
            # Map Teacher
            t_name = raw_data["teachers"].get(sub_code)
            if t_name:
                teacher_map.append({"teacherName": t_name, "subjectName": sub_code})

    smart_input = {
        "subjects": subjects_list,
        "teachers": teachers_list,
        "teacherSubjectMap": teacher_map
    }
    
    context = {
        "branchData": branch_data,
        "smartInputData": smart_input
    }
    
    with open('repro_result.txt', 'w', encoding='utf-8') as f:
        f.write("🚀 REPRO EXECUTION STARTED\n")
        
        try:
            scheduler = TimetableScheduler(context)
            result = scheduler.generate()
            
            f.write("\n✅ GENERATION FINISHED\n")
            f.write(f"Success: {result['success']}\n")
            
            if 'timetables' in result:
                tt = result['timetables']
                f.write(f"\nTimeTable Structure Keys: {list(tt.keys())}\n")
                for year in tt:
                    f.write(f"  {year}: {list(tt[year].keys())}\n")
                    for div in tt[year]:
                        slots = tt[year][div].get('timetable', {})
                        count = 0
                        if isinstance(slots, dict):
                            count = sum(len(s) for s in slots.values())
                        elif isinstance(slots, list):
                            count = len(slots)
                        f.write(f"    {div}: {count} slots filled\n")
            else:
                f.write("❌ 'timetables' key missing in result\n")
                f.write(str(result) + "\n")

        except Exception as e:
            import traceback
            f.write(f"❌ CRASH: {e}\n")
            f.write(traceback.format_exc())

    print("DONE writing to repro_result.txt")


if __name__ == "__main__":
    run_repro()
