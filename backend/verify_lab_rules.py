
import json
import sys
import os

# Ensure we can import backend modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.engine.scheduler import TimetableScheduler

def run_verification():
    print("🚀 VERIFYING LAB RULES")
    
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
    branch_data = {
        "academicYears": raw_data["years"],
        "divisions": raw_data["divisions"],
        "workingDays": raw_data["days"],
        "slotsPerDay": 6,
        "startTime": "09:00",
        "endTime": "17:00",
        "lectureDuration": 60,
        "classrooms": [{"name": r, "capacity": 60} for r in raw_data["classrooms"]],
        "sharedLabs": [{"name": l, "capacity": 30} for l in raw_data["labs"]],
        "rooms": raw_data["classrooms"], 
        "labs": raw_data["labs"],
        "labBatchesPerYear": { "SE": 3, "TE": 3, "BE": 3 } 
    }
    
    subjects_list = []
    teachers_list = []
    teacher_map = []
    
    for code, t_name in raw_data["teachers"].items():
        teachers_list.append({"name": t_name, "id": t_name, "subjects": []})
    
    for year, types in raw_data["subjects"].items():
        for sub_code in types["theory"]:
            subjects_list.append({ "name": sub_code, "year": year, "type": "Lecture", "lecturesPerWeek": 3, "isPractical": False, "division": None })
            if raw_data["teachers"].get(sub_code): teacher_map.append({"teacherName": raw_data["teachers"].get(sub_code), "subjectName": sub_code})

        for sub_code in types["labs"]:
            subjects_list.append({ "name": sub_code, "year": year, "type": "Practical", "lecturesPerWeek": 4, "isPractical": True, "division": None })
            if raw_data["teachers"].get(sub_code): teacher_map.append({"teacherName": raw_data["teachers"].get(sub_code), "subjectName": sub_code})

    smart_input = { "subjects": subjects_list, "teachers": teachers_list, "teacherSubjectMap": teacher_map }
    context = { "branchData": branch_data, "smartInputData": smart_input }
    
    with open('verify_output.txt', 'w') as f:
        try:
            scheduler = TimetableScheduler(context)
            result = scheduler.generate()
            tt = result.get('timetables', {})
            
            f.write(f"Success: {result['success']}\n\n")
            
            # ANALYZE LAB DISTRIBUTION
            # We want to check SE-A for Batches B1, B2, B3
            
            target_year = "SE"
            target_div = "A"
            
            if target_year in tt and target_div in tt[target_year]:
                # Data structure: tt[year][div]['timetable'] -> { Day: [Slots] }
                # OR tt[year][div] -> { Day: [Slots] } (depending on fix)
                
                sched = tt[target_year][target_div]
                if 'timetable' in sched: sched = sched['timetable']
                
                # Build Matrix: Batch -> Day -> Lab Count
                batch_labs = { "B1": {}, "B2": {}, "B3": {} }
                
                for day in raw_data["days"]:
                    day_slots = sched.get(day, [])
                    # Handle Object vs List
                    if isinstance(day_slots, dict): day_slots = list(day_slots.values())
                    
                    for alloc in day_slots:
                        if not isinstance(alloc, dict): continue
                        
                        if alloc.get('type') == 'LAB':
                            b = alloc.get('batch')
                            if b in batch_labs:
                                if day not in batch_labs[b]: batch_labs[b][day] = []
                                # Only count unique subjects per day
                                sub = alloc.get('subject')
                                if sub and sub not in batch_labs[b][day]:
                                    batch_labs[b][day].append(sub)

                f.write(f"--- LAB DISTRIBUTION FOR {target_year}-{target_div} ---\n")
                
                violations = 0
                for b, days_data in batch_labs.items():
                    f.write(f"\nBatch {b}:\n")
                    for day, labs in days_data.items():
                        f.write(f"  {day}: {labs}\n")
                        if len(labs) > 1:
                            f.write(f"  🛑 VIOLATION: More than 1 lab on {day}!\n")
                            violations += 1
                
                if violations == 0:
                    f.write("\n✅ RESULT: All batches obey 'One Lab Per Day' rule.\n")
                else:
                    f.write(f"\n❌ RESULT: Found {violations} violations.\n")

            else:
                 f.write(f"Target {target_year}-{target_div} not found in output.\n")

        except Exception as e:
            import traceback
            f.write(f"❌ CRASH: {e}\n")
            f.write(traceback.format_exc())

    print("DONE writing to verify_output.txt")

if __name__ == "__main__":
    run_verification()
