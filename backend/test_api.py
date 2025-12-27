"""
Test Constraint API Endpoints via HTTP

This script tests the constraint API endpoints running on Flask server.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/constraints"

# Sample test data
sample_timetable = [
    {
        "id": "slot1",
        "day": "Monday",
        "slot": 0,
        "year": "SE",
        "division": "A",
        "subject": "ML",
        "teacher": "Neha",
        "room": "Lab-2",
        "type": "Lecture"
    },
    {
        "id": "slot2",
        "day": "Monday",
        "slot": 0,
        "year": "TE",
        "division": "B",
        "subject": "AI",
        "teacher": "Neha",  # Teacher overlap violation
        "room": "Lab-3",
        "type": "Lecture"
    }
]

sample_context = {
    "branchData": {
        "academicYears": ["SE", "TE"],
        "divisions": {
            "SE": ["A"],
            "TE": ["B"]
        },
        "rooms": ["Lab-2", "Lab-3"],
        "labs": []
    },
    "smartInputData": {
        "subjects": [
            {"name": "ML", "year": "SE", "division": "A", "lecturesPerWeek": 4},
            {"name": "AI", "year": "TE", "division": "B", "lecturesPerWeek": 4}
        ],
        "teachers": [
            {"name": "Neha"}
        ]
    }
}

def test_list_constraints():
    """Test GET /api/constraints/list"""
    print("\n[TEST 1] GET /api/constraints/list")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/list")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data['hard'])} hard and {len(data['soft'])} soft constraints")
            print(f"\nHard Constraints:")
            for c in data['hard'][:3]:
                print(f"  - {c['name']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_validate_timetable():
    """Test POST /api/constraints/validate"""
    print("\n[TEST 2] POST /api/constraints/validate")
    print("-" * 60)
    
    try:
        payload = {
            "timetable": sample_timetable,
            "context": sample_context
        }
        
        response = requests.post(
            f"{BASE_URL}/validate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Valid: {data['valid']}")
            print(f"Hard Violations: {data['summary']['hardViolations']}")
            print(f"Soft Violations: {data['summary']['softViolations']}")
            print(f"Quality Score: {data['qualityScore']}/100")
            
            if data['hardViolations']:
                print(f"\nDetected Violations:")
                for v in data['hardViolations'][:2]:
                    print(f"  [{v['constraint']}] {v['message']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_check_slot():
    """Test POST /api/constraints/check-slot"""
    print("\n[TEST 3] POST /api/constraints/check-slot")
    print("-" * 60)
    
    try:
        new_slot = {
            "id": "slot3",
            "day": "Tuesday",
            "slot": 1,
            "year": "SE",
            "division": "A",
            "subject": "DBMS",
            "teacher": "John",
            "room": "Lab-1",
            "type": "Lecture"
        }
        
        payload = {
            "slot": new_slot,
            "existingTimetable": sample_timetable,
            "context": sample_context
        }
        
        response = requests.post(
            f"{BASE_URL}/check-slot",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Slot Valid: {data['valid']}")
            print(f"Violations: {len(data['violations'])}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_quality_score():
    """Test POST /api/constraints/quality-score"""
    print("\n[TEST 4] POST /api/constraints/quality-score")
    print("-" * 60)
    
    try:
        payload = {
            "timetable": sample_timetable,
            "context": sample_context
        }
        
        response = requests.post(
            f"{BASE_URL}/quality-score",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Quality Score: {data['qualityScore']}/100")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Constraint Engine API Endpoints")
    print("=" * 60)
    
    test_list_constraints()
    test_validate_timetable()
    test_check_slot()
    test_quality_score()
    
    print("\n" + "=" * 60)
    print("API Tests Completed!")
    print("=" * 60)
