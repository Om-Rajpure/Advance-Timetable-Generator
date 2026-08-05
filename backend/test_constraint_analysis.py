"""
Test suite for Constraint Resource Analysis & Resource Recommendation Report
"""

import os
import sys

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from engine.constraint_analyzer import ConstraintAnalyzer
from engine.diagnostics import FailureRecord


def test_constraint_analysis_report():
    print("=== Testing Constraint Resource Analysis Engine ===")

    mock_context = {
        "branchData": {
            "academicYears": ["BE"],
            "divisions": {"BE": ["B"]},
            "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "slotsPerDay": 7,
            "maxLecturesPerDay": 6,
            "classrooms": ["Room 101"],
            "labs": [{"name": "Lab 1", "capacity": 25}]
        },
        "smartInputData": {
            "subjects": [
                {"name": "DWM Theory", "year": "BE", "division": "B", "weeklyLectures": 4, "isLab": False},
                {"name": "BT Lab", "year": "BE", "division": "B", "weeklyLectures": 2, "isLab": True}
            ],
            "teachers": [
                {"name": "Mr. Patil", "subjects": ["DWM Theory"], "maxWeeklyLectures": 16}
            ],
            "teacherSubjectMap": [
                {"subjectName": "DWM Theory", "teacherName": "Mr. Patil"}
                # Notice BT Lab has NO teacher mapped!
            ]
        }
    }

    cpsat_result = {
        "status": "INFEASIBLE",
        "incomplete": [("BE-B", "DWM Theory", 0, 4)]
    }

    lab_failures = [
        {"division": "BE-B", "subject": "BT Lab", "batch": "B1-B3", "reason": "No teacher mapped"}
    ]

    analyzer = ConstraintAnalyzer(
        context=mock_context,
        cpsat_result=cpsat_result,
        lab_failures=lab_failures
    )

    report_data = analyzer.analyze(target_division="BE-B")
    report_text = report_data.get("reportText", "")

    print("\n--- GENERATED REPORT OUTPUT ---")
    print(report_text)
    print("--------------------------------\n")

    # Assertions
    assert "RESOURCE ANALYSIS" in report_text
    assert "Division: BE-B" in report_text
    assert "MINIMUM ADDITIONAL RESOURCES NEEDED" in report_text
    assert "BT Lab" in report_text or "Teacher" in report_text
    assert report_data["reasonForFailure"]["theoryRemaining"] == 4
    assert report_data["reasonForFailure"]["practicalsRemaining"] == 1

    # Verify FailureRecord formatting with report
    record = FailureRecord(
        division="BE-B",
        batch="B1-B3",
        subject="Bt L",
        teacher="NOT FOUND",
        lab="NOT ASSIGNED",
        stage="Post-Solver Scheduled Coverage Check",
        reason="Practical placement incomplete for sub-batches",
        resource_report=report_text
    )

    exc_msg = record.to_exception_message(solver_status="OPTIMAL")
    print("--- EXCEPTION MESSAGE WITH REPORT ---")
    print(exc_msg)
    print("------------------------------------")

    assert "TIMETABLE GENERATION FAILED" in exc_msg
    assert "MINIMUM ADDITIONAL RESOURCES NEEDED" in exc_msg

    print("\n✅ ALL CONSTRAINT RESOURCE ANALYSIS TESTS PASSED!")


if __name__ == "__main__":
    test_constraint_analysis_report()
