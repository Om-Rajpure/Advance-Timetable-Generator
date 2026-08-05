import sys
import os

from engine.scheduler import TimetableScheduler

def run_test():
    raw_data = {
      "years": ["SE", "TE", "BE"],
      "divisions": { "SE": ["A", "B"], "TE": ["A", "B", "C"], "BE": ["A", "B"] },
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "slots_per_day": 6,
      
      "subjects": {
        "SE": { "theory": ["SE_T1", "SE_T2", "SE_T3"], "labs": ["SE_L1", "SE_L2"] },
        "TE": { "theory": ["TE_T1", "TE_T2", "TE_T3"], "labs": ["TE_L1", "TE_L2", "TE_L3"] },
        "BE": { "theory": ["BE_T1", "BE_T2", "BE_T3"], "labs": ["BE_L1", "BE_L2", "BE_L3"] }
      },
      
      "labs": ["Lab_1", "Lab_2", "Lab_3", "Lab_4"],
      "classrooms": ["Room_1", "Room_2", "Room_3", "Room_4"]
    }

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
    
    t_idx = 1
    for year, types in raw_data["subjects"].items():
        for sub_code in types["theory"]:
            subjects_list.append({
                "name": sub_code,
                "year": year,
                "type": "Lecture",
                "lecturesPerWeek": 3,
                "isPractical": False,
                "division": ""
            })
            t_name = f"Teacher_{t_idx}"
            t_idx += 1
            teachers_list.append({"name": t_name, "subjects": [sub_code]})
            teacher_map.append({"teacherName": t_name, "subjectName": sub_code})

        for sub_code in types["labs"]:
            subjects_list.append({
                "name": sub_code,
                "year": year,
                "type": "Practical",
                "lecturesPerWeek": 2,
                "isPractical": True,
                "division": ""
            })
            t_name = f"Teacher_{t_idx}"
            t_idx += 1
            teachers_list.append({"name": t_name, "subjects": [sub_code]})
            teacher_map.append({"teacherName": t_name, "subjectName": sub_code})

    context = {
        "branchData": branch_data,
        "smartInputData": {
            "subjects": subjects_list,
            "teachers": teachers_list,
            "teacherSubjectMap": teacher_map
        }
    }

    scheduler = TimetableScheduler(context)
    result = scheduler.generate()
    print("\nResult Success:", result.get('success'))
    if not result.get('success'):
        print("Message:", result.get('message'))

if __name__ == "__main__":
    run_test()
