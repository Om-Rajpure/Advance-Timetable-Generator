
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from analytics.workload_analysis import compute_teacher_workload

# SCENARIO: Case & Whitespace Mismatch
timetable = [
    {"teacher": "Dr. Sharma ", "day": "Monday"}, # Trailing space
    {"teacher": "dr. sharma", "day": "Tuesday"}, # Lowercase
    {"teacher": "DR. SHARMA", "day": "Wednesday"} # Uppercase
]
context = {
    "smartInputData": {
        "teachers": [
            {"name": "Dr. Sharma"}, # Standard
            {"name": "Prof. Patel"}
        ]
    }, 
    "branchData": {}
}

print("--- Testing Robust Fix ---")
result = compute_teacher_workload(timetable, context)

sharma_stats = result['perTeacher']['Dr. Sharma']
print(f"Result for 'Dr. Sharma': {sharma_stats['totalLectures']} (Expected 3)")
print(f"Daily: {sharma_stats['lecturesPerDay']}")

if sharma_stats['totalLectures'] == 3:
    print("✅ SUCCESS: Correctly aggregated despite variations.")
else:
    print("❌ FAILURE: Counts did not match.")
