
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.scheduler import TimetableScheduler

print("\n--- ATTACK OF THE LISTS ---\n")

# CRASH CASE 1: branchData.divisions is a LIST (simulating bad JSON from frontend)
context_bad_divisions = {
    "branchData": {
        "academicYears": ["FE"],
        "divisions": ["A", "B"], # ERROR: Should be {"FE": ["A", "B"]}
        "labs": [],
        "sharedLabs": [],
        "labBatchesPerYear": {}
    },
    "smartInputData": {"subjects": [], "teachers": []}
}

try:
    print("TEST 1: divisions is a list (Expected TypeError from my fix)")
    scheduler = TimetableScheduler(context_bad_divisions)
    scheduler.generate()
except Exception as e:
    print(f"CAUGHT: {e}")

# CRASH CASE 2: subjects is not a list? No, user says list object has no value.
# Maybe 'divisions' inside branchData iteration?

context_bad_years = {
    "branchData": {
        "academicYears": {"FE": "True"}, # Bad type
        "divisions": {"FE": ["A"]},
        "labs": [],
        "sharedLabs": [],
        "labBatchesPerYear": {}
    },
    "smartInputData": {"subjects": [], "teachers": []}
}

try:
    print("\nTEST 2: academicYears is a dict (Maybe iterates values?)")
    scheduler = TimetableScheduler(context_bad_years)
    scheduler.generate()
except Exception as e:
    print(f"CAUGHT: {e}")
