"""
Test Editable Timetable Module

Tests edit validation and auto-fix functionality.
"""

import sys
import os
import requests
import json

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
sys.path.insert(0, backend_dir)

API_BASE = 'http://localhost:5000/api/edit'

# Sample timetable
sample_timetable = [
    {
        "id": "mon_0_se_a",
        "day": "Monday",
        "slot": 0,
        "year": "SE",
        "division": "A",
        "subject": "ML",
        "teacher": "Neha",
        "room": "Room-1",
        "type": "Lecture"
    },
    {
        "id": "mon_1_se_a",
        "day": "Monday",
        "slot": 1,
        "year": "SE",
        "division": "A",
        "subject": "AI",
        "teacher": "John",
        "room": "Room-2",
        "type": "Lecture"
    },
    {
        "id": "tue_0_se_a",
        "day": "Tuesday",
        "slot": 0,
        "year": "SE",
        "division": "A",
        "subject": "DBMS",
        "teacher": "Sarah",
        "room": "Room-1",
        "type": "Lecture"
    }
]

context = {
    "branchData": {
        "academicYears": ["SE"],
        "divisions": {"SE": ["A"]},
        "slotsPerDay": 6,
        "rooms": ["Room-1", "Room-2"],
        "labs": ["Lab-1", "Lab-2"]
    },
    "smartInputData": {
        "subjects": [
            {"name": "ML", "year": "SE", "division": "A", "lecturesPerWeek": 2},
            {"name": "AI", "year": "SE", "division": "A", "lecturesPerWeek": 2},
            {"name": "DBMS", "year": "SE", "division": "A", "lecturesPerWeek": 2}
        ],
        "teachers": [
            {"name": "Neha", "subjects": ["ML"]},
            {"name": "John", "subjects": ["AI"]},
            {"name": "Sarah", "subjects": ["DBMS"]},
            {"name": "David", "subjects": []}  # Can teach anything
        ]
    }
}

print("=" * 60)
print("Testing Editable Timetable Module")
print("=" * 60)

print("\n[TEST 1] Validate Valid Edit")
print("-" * 60)

# Edit that should be valid
valid_edit = {
    "id": "mon_0_se_a",
    "day": "Monday",
    "slot": 0,
    "year": "SE",
    "division": "A",
    "subject": "ML",
    "teacher": "David",  # Changed to available teacher
    "room": "Room-1",
    "type": "Lecture"
}

try:
    response = requests.post(f'{API_BASE}/validate', json={
        "modifiedSlot": valid_edit,
        "timetable": sample_timetable,
        **context
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Validation successful")
        print(f"Valid: {result.get('valid')}")
        print(f"Conflicts: {len(result.get('conflicts', []))}")
        print(f"Severity: {result.get('severity')}")
    else:
        print(f"❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n[TEST 2] Validate Conflicting Edit (Teacher Overlap)")
print("-" * 60)

# Edit that creates conflict - assign Neha to same time slot where she's already teaching
conflicting_edit = {
    "id": "tue_0_se_a",
    "day": "Monday",  # Same day as first slot
    "slot": 0,        # Same slot as first slot
    "year": "SE",
    "division": "A",
    "subject": "DBMS",
    "teacher": "Neha",  # Neha is already teaching ML at Monday slot 0
    "room": "Room-2",
    "type": "Lecture"
}

try:
    response = requests.post(f'{API_BASE}/validate', json={
        "modifiedSlot": conflicting_edit,
        "timetable": sample_timetable,
        **context
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"Valid: {result.get('valid')}")
        print(f"Conflicts: {len(result.get('conflicts', []))}")
        print(f"Severity: {result.get('severity')}")
        
        if result.get('conflicts'):
            print(f"\nConflict Details:")
            for conflict in result.get('conflicts', []):
                print(f"  - {conflict.get('constraint')}: {conflict.get('message')}")
    else:
        print(f"❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n[TEST 3] Auto-Fix Suggestion")
print("-" * 60)

try:
    # Request auto-fix for the conflicting edit
    response = requests.post(f'{API_BASE}/suggest-fix', json={
        "slot": conflicting_edit,
        "conflicts": [{"constraint": "TEACHER_NON_OVERLAP"}],
        "timetable": sample_timetable,
        **context
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"Fix Available: {result.get('fix') is not None}")
        print(f"Explanation: {result.get('explanation')}")
        print(f"Strategy: {result.get('strategy')}")
        
        if result.get('fix'):
            print(f"\nSuggested Fix:")
            print(f"  Teacher: {result['fix'].get('teacher')}")
    else:
        print(f"❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n[TEST 4] Get Alternatives")
print("-" * 60)

try:
    response = requests.post(f'{API_BASE}/alternatives', json={
        "slot": sample_timetable[0],
        "timetable": sample_timetable,
        **context
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"Available Teachers: {result.get('teachers', [])}")
        print(f"Available Rooms: {result.get('rooms', [])}")
    else:
        print(f"❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
