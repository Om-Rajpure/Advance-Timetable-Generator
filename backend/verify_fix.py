
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from analytics.workload_analysis import compute_teacher_workload

# SCENARIO: Whitespace Mismatch
timetable = [{"teacher": "Dr. Sharma ", "day": "Monday"}]
context = {"smartInputData": {"teachers": [{"name": "Dr. Sharma"}]}, "branchData": {}}

print("--- Testing Fix ---")
result = compute_teacher_workload(timetable, context)
print(f"Result for 'Dr. Sharma': {result['perTeacher']['Dr. Sharma']['totalLectures']}")
