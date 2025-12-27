"""
Test Constraint Engine

Basic tests to verify constraint engine functionality.
"""

from constraints.constraint_engine import ConstraintEngine

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
        "teacher": "Neha",  # VIOLATION: Same teacher at same time
        "room": "Lab-3",
        "type": "Lecture"
    },
    {
        "id": "slot3",
        "day": "Tuesday",
        "slot": 1,
        "year": "SE",
        "division": "A",
        "batch": "B1",
        "subject": "DBMS Lab",
        "teacher": "John",
        "room": "Lab-1",
        "type": "Practical"
    },
    {
        "id": "slot4",
        "day": "Tuesday",
        "slot": 2,  # VIOLATION: Different time for practical batch
        "year": "SE",
        "division": "A",
        "batch": "B2",
        "subject": "DBMS Lab",
        "teacher": "John",
        "room": "Lab-2",
        "type": "Practical"
    }
]

sample_context = {
    "branchData": {
        "academicYears": ["FE", "SE", "TE", "BE"],
        "divisions": {
            "SE": ["A", "B"],
            "TE": ["A", "B"]
        },
        "rooms": ["Room-1", "Room-2"],
        "labs": ["Lab-1", "Lab-2", "Lab-3"]
    },
    "smartInputData": {
        "subjects": [
            {"name": "ML", "year": "SE", "division": "A", "lecturesPerWeek": 4},
            {"name": "AI", "year": "TE", "division": "B", "lecturesPerWeek": 4},
            {"name": "DBMS Lab", "year": "SE", "division": "A", "lecturesPerWeek": 2}
        ],
        "teachers": [
            {"name": "Neha"},
            {"name": "John"}
        ]
    }
}


def test_constraint_engine():
    """Test basic constraint engine functionality"""
    
    print("=" * 60)
    print("Testing Constraint Engine")
    print("=" * 60)
    
    # Initialize engine
    engine = ConstraintEngine()
    
    # Test 1: List constraints
    print("\n[TEST 1] Listing Constraints")
    print("-" * 60)
    constraints = engine.list_constraints()
    print(f"Hard Constraints: {len(constraints['hard'])}")
    for c in constraints['hard']:
        print(f"  - {c['name']}: {c['description']}")
    
    print(f"\nSoft Constraints: {len(constraints['soft'])}")
    for c in constraints['soft']:
        print(f"  - {c['name']}: {c['description']}")
    
    # Test 2: Validate timetable with violations
    print("\n[TEST 2] Validating Sample Timetable")
    print("-" * 60)
    result = engine.validate_timetable(sample_timetable, sample_context)
    
    print(f"Valid: {result['valid']}")
    print(f"Hard Violations: {result['summary']['hardViolations']}")
    print(f"Soft Violations: {result['summary']['softViolations']}")
    print(f"Quality Score: {result['qualityScore']}/100")
    
    # Print violations
    if result['hardViolations']:
        print("\nHard Violations:")
        for v in result['hardViolations']:
            print(f"  [{v['constraint']}] {v['message']}")
    
    if result['softViolations']:
        print("\nSoft Violations:")
        for v in result['softViolations'][:3]:  # Show first 3
            print(f"  [{v['constraint']}] {v['message']}")
    
    # Test 3: Validate single slot
    print("\n[TEST 3] Validating Single Slot")
    print("-" * 60)
    new_slot = {
        "id": "slot_new",
        "day": "Wednesday",
        "slot": 3,
        "year": "SE",
        "division": "A",
        "subject": "ML",
        "teacher": "Neha",
        "room": "Room-1",
        "type": "Lecture"
    }
    
    slot_result = engine.validate_slot(new_slot, sample_timetable, sample_context)
    print(f"Slot Valid: {slot_result['valid']}")
    print(f"Violations: {len(slot_result['violations'])}")
    
    # Test 4: Compute quality score
    print("\n[TEST 4] Computing Quality Score")
    print("-" * 60)
    score = engine.compute_quality_score(sample_timetable, sample_context)
    print(f"Quality Score: {score}/100")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_constraint_engine()
