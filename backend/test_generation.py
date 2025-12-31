"""
Test Core Timetable Generation Engine

Tests the CSP-based generation algorithm with simple sample data.
"""

import sys
import os

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
sys.path.insert(0, backend_dir)

from engine.scheduler import TimetableScheduler
from engine.optimizer import TimetableOptimizer


# Simple test data
test_context = {
    "branchData": {
        "academicYears": ["SE"],
        "divisions": {
            "SE": ["A"]
        },
        "slotsPerDay": 6,  # Increased slots per day
        "rooms": ["Room-1", "Room-2"],
        "sharedLabs": [
            {"name": "Lab-1", "capacity": 30},
            {"name": "Lab-2", "capacity": 30},
            {"name": "Lab-3", "capacity": 30}
        ],
        "labBatchesPerYear": {
            "SE": 3
        }
    },
    "smartInputData": {
        "subjects": [
            {
                "name": "Machine Learning",
                "year": "SE",
                "division": "A",
                "lecturesPerWeek": 2,
                "type": "Lecture",
                "isPractical": False,
                "subjects": ["Machine Learning"]
            },
            {
                "name": "AI",
                "year": "SE",
                "division": "A",
                "lecturesPerWeek": 2,
                "type": "Lecture",
                "isPractical": False,
                "subjects": ["AI"]
            },
            {
                "name": "Python Lab",
                "year": "SE",
                "division": "A",
                "lecturesPerWeek": 4, # 2 sessions?
                "type": "Practical",
                "isPractical": True,
                "subjects": ["Python Lab"]
            },
            {
                "name": "AI Lab",
                "year": "SE",
                "division": "A",
                "lecturesPerWeek": 4,
                "type": "Practical",
                "isPractical": True,
                "subjects": ["AI Lab"]
            },
             {
                "name": "Data Lab",
                "year": "SE",
                "division": "A",
                "lecturesPerWeek": 4,
                "type": "Practical",
                "isPractical": True,
                "subjects": ["Data Lab"]
            }
        ],
        "teachers": [
            {
                "name": "Neha",
                "subjects": ["Machine Learning", "AI", "Python Lab"]
            },
            {
                "name": "John",
                "subjects": ["AI Lab", "Data Lab"] 
            },
            {
                "name": "Sarah",
                "subjects": ["Machine Learning", "AI", "Python Lab", "Data Lab", "AI Lab"]
            },
             {
                "name": "Amit",
                "subjects": ["Data Lab", "AI Lab"] 
            }
        ]
    }
}


def test_generation():
    """Test basic timetable generation"""
    
    print("=" * 60)
    print("Testing Core Timetable Generation Engine")
    print("=" * 60)
    
    print("\n[TEST CONFIG]")
    print(f"Years: {test_context['branchData']['academicYears']}")
    print(f"Divisions: SE-A")
    print(f"Slots per day: {test_context['branchData']['slotsPerDay']}")
    print(f"Total slots available: {test_context['branchData']['slotsPerDay']} * 6 days = {test_context['branchData']['slotsPerDay'] * 6}")
    print(f"Subjects: 2 (lectures only, 2 per week each)")
    print(f"Total lectures needed: 4")
    print(f"Teachers: 3")
    print(f"Rooms: 2")
    print(f"Labs: 3")
    
    print("\n[STARTING GENERATION]")
    print("-" * 60)
    
    # Initialize scheduler
    scheduler = TimetableScheduler(test_context, max_iterations=5000)
    
    # Generate timetable
    result = scheduler.generate()
    
    print(f"\nGeneration Result: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Valid: {result.get('valid', False)}")
    
    if result['success']:
        print(f"\n[STATISTICS]")
        print(f"Total Slots Filled: {result['stats']['totalSlots']}")
        print(f"Iterations: {result['stats']['iterations']}")
        print(f"Backtracks: {result['stats']['backtracks']}")
        print(f"Quality Score: {result.get('qualityScore', 0)}/100")
        
        print(f"\n[VIOLATIONS]")
        hard_violations = result.get('violations', [])
        hard_count = sum(1 for v in hard_violations if v.get('severity') == 'HARD')
        soft_count = sum(1 for v in hard_violations if v.get('severity') == 'SOFT')
        
        print(f"Hard Violations: {hard_count}")
        print(f"Soft Violations: {soft_count}")
        
        if hard_violations and hard_count > 0:
            print("\nHard Violations Found:")
            for v in hard_violations[:3]:
                if v.get('severity') == 'HARD':
                    print(f"  - [{v.get('constraint')}] {v.get('message')}")
        
        # Show sample slots
        print(f"\n[SAMPLE SLOTS]")
        timetable = result.get('timetable', [])
        for i, slot in enumerate(timetable[:5]):
            print(f"{i+1}. {slot.get('day')} Slot {slot.get('slot')}: "
                  f"{slot.get('subject')} - {slot.get('teacher')} - {slot.get('room')}")
        
        if len(timetable) > 5:
            print(f"... and {len(timetable) - 5} more slots")
    
    else:
        print(f"\n[FAILURE REASON]")
        print(f"Message: {result.get('message')}")
        
        if 'blockers' in result:
            print(f"\nBlockers:")
            for blocker in result['blockers']:
                print(f"  - {blocker.get('issue')}: {blocker.get('details')}")
        
        if 'suggestions' in result:
            print(f"\nSuggestions:")
            for suggestion in result['suggestions']:
                print(f"  - {suggestion}")
    
    print("\n" + "=" * 60)
    print("Test Completed!")
    print("=" * 60)
    
    # Final Assertions for Pytest
    assert result['success'] is True, f"Generation failed: {result.get('message')}"
    assert result['valid'] is True, "Generated timetable is invalid"
    assert result['stats']['totalSlots'] > 0, "No slots were filled"



if __name__ == "__main__":
    result = test_generation()
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)
