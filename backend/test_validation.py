"""
Test Validation & Optimization Layer

Tests validation, scoring, and optimization functionality.
"""

import sys
import os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
sys.path.insert(0, backend_dir)

from validation.validation_report import ValidationReport

# Sample timetable data
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
        "subject": "ML",
        "teacher": "Neha",
        "room": "Room-1",
        "type": "Lecture"
    },
    {
        "id": "wed_0_se_a",
        "day": "Wednesday",
        "slot": 0,
        "year": "SE",
        "division": "A",
        "subject": "AI",
        "teacher": "Sarah",
        "room": "Room-2",
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
            {"name": "AI", "year": "SE", "division": "A", "lecturesPerWeek": 2}
        ],
        "teachers": [
            {"name": "Neha", "subjects": ["ML"]},
            {"name": "John", "subjects": ["AI"]},
            {"name": "Sarah", "subjects": ["AI"]}
        ]
    }
}

print("=" * 60)
print("Testing Validation & Optimization Layer")
print("=" * 60)

print("\n[TEST 1] Quick Validation")
print("-" * 60)
report_gen = ValidationReport(context)
quick_result = report_gen.generate_quick_report(sample_timetable)
print(f"Valid: {quick_result['valid']}")
print(f"Can Proceed: {quick_result['canProceed']}")
print(f"Score: {quick_result['score']}/100")
print(f"Grade: {quick_result['grade']}")
print(f"Message: {quick_result['message']}")

print("\n[TEST 2] Full Validation (No Optimization)")
print("-" * 60)
full_report = report_gen.generate_full_report(sample_timetable, optimize=False)
print(f"Valid: {full_report['validation']['valid']}")
print(f"Quality Score: {full_report['qualityScore']['score']}/100")
print(f"Grade: {full_report['qualityScore']['grade']}")

print("\n[Resource Utilization]")
resources = full_report['resourceAnalysis']
print(f"Teacher Utilization: {resources['teacherUtilization']['overall']}%")
print(f"Lab Utilization: {resources['labUtilization']}%")
print(f"Room Utilization: {resources['roomUtilization']}%")

print("\n[Explanation]")
explanation = full_report['explanation']
print(f"Summary: {explanation['summary']}")
print(f"Score Explanation: {explanation['scoreExplanation']}")

if explanation['mainIssues']:
    print(f"\nMain Issues:")
    for issue in explanation['mainIssues']:
        print(f"  - {issue}")

if explanation['suggestions']:
    print(f"\nSuggestions:")
    for suggestion in explanation['suggestions']:
        print(f"  - {suggestion}")

print("\n[TEST 3] With Optimization")
print("-" * 60)
optimized_report = report_gen.generate_full_report(sample_timetable, optimize=True)

if optimized_report['optimization']:
    opt = optimized_report['optimization']
    print(f"Improved: {opt['improved']}")
    print(f"Score Improvement: {opt['scoreImprovement']} points")
    print(f"Final Score: {opt['finalScore']}/100")
    
    if opt['improvements']:
        print(f"\nImprovements Made:")
        for improvement in opt['improvements']:
            print(f"  - {improvement}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
