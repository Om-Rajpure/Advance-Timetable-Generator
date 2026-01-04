
from collections import defaultdict
import json

def compute_teacher_workload(timetable, context):
    smart_input = context.get('smartInputData', {})
    teachers = smart_input.get('teachers', [])
    
    # Track lectures
    teacher_total_lectures = defaultdict(int)
    
    print("\n--- Counting Slots ---")
    for slot in timetable:
        teacher = slot.get('teacher')
        if teacher:
            print(f"Slot teacher: '{teacher}'")
            teacher_total_lectures[teacher] += 1
    
    print("\n--- Matching with Teachers List ---")
    results = {}
    for teacher_data in teachers:
        teacher_name = teacher_data.get('name')
        print(f"Checking list teacher: '{teacher_name}'")
        total = teacher_total_lectures.get(teacher_name, 0)
        results[teacher_name] = total
        
    return results

# SCENARIO 1: Exact Match
print("SCENARIO 1: Exact Match")
timetable1 = [{"teacher": "Dr. Sharma"}]
context1 = {"smartInputData": {"teachers": [{"name": "Dr. Sharma"}]}}
print(compute_teacher_workload(timetable1, context1))

# SCENARIO 2: Whitespace Mismatch (Slot has space)
print("\nSCENARIO 2: Slot has space")
timetable2 = [{"teacher": "Dr. Sharma "}]
context2 = {"smartInputData": {"teachers": [{"name": "Dr. Sharma"}]}}
print(compute_teacher_workload(timetable2, context2))

# SCENARIO 3: List has space
print("\nSCENARIO 3: List has space")
timetable3 = [{"teacher": "Dr. Sharma"}]
context3 = {"smartInputData": {"teachers": [{"name": "Dr. Sharma "}]}}
print(compute_teacher_workload(timetable3, context3))
