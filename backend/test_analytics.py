"""
Analytics Module Tests

Tests for analytics engine and API endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.workload_analysis import compute_teacher_workload, generate_workload_insights
from analytics.lab_usage import compute_lab_heatmap, analyze_lab_efficiency
from analytics.free_slots import find_free_slots, analyze_free_capacity
from analytics.bottleneck_detector import detect_bottlenecks
from analytics.analytics_engine import generate_full_analytics, compute_quality_score


# Sample test data
SAMPLE_TIMETABLE = [
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '9:00-10:00', 'subject': 'Math', 'teacher': 'Dr. Sharma', 'room': 'R101', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '10:00-11:00', 'subject': 'Physics', 'teacher': 'Prof. Patel', 'room': 'R102', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '11:00-12:00', 'subject': 'Physics', 'teacher': 'Prof. Patel', 'room': 'R102', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '2:00-3:00', 'subject': 'Physics', 'teacher': 'Prof. Patel', 'room': 'R102', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '3:00-4:00', 'subject': 'Physics', 'teacher': 'Prof. Patel', 'room': 'R102', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '4:00-5:00', 'subject': 'Physics', 'teacher': 'Prof. Patel', 'room': 'R102', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Monday', 'time': '12:00-1:00', 'subject': 'Physics', 'teacher': 'Prof. Patel', 'room': 'R102', 'type': 'Lecture'},
    {'year': 'FE', 'division': 'A', 'day': 'Tuesday', 'time': '9:00-10:00', 'subject': 'CS Lab', 'teacher': 'Prof. Kumar', 'lab': 'Lab-1', 'room': 'Lab-1', 'type': 'Practical'},
    {'year': 'FE', 'division': 'A', 'day': 'Tuesday', 'time': '10:00-11:00', 'subject': 'CS Lab', 'teacher': 'Prof. Kumar', 'lab': 'Lab-1', 'room': 'Lab-1', 'type': 'Practical'},
    {'year': 'FE', 'division': 'B', 'day': 'Tuesday', 'time': '9:00-10:00', 'subject': 'CS Lab', 'teacher': 'Prof. Kumar', 'lab': 'Lab-2', 'room': 'Lab-2', 'type': 'Practical'},
]

SAMPLE_CONTEXT = {
    'branchData': {
        'workingDays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'timeSlots': ['9:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-1:00', '1:00-2:00', '2:00-3:00', '3:00-4:00', '4:00-5:00'],
        'slotsPerDay': 8,
        'divisions': {'FE': ['A', 'B'], 'SE': ['A']},
        'labs': ['Lab-1', 'Lab-2', 'Lab-3'],
        'rooms': ['R101', 'R102', 'R103', 'R104']
    },
    'smartInputData': {
        'teachers': [
            {'name': 'Dr. Sharma', 'id': 't1'},
            {'name': 'Prof. Patel', 'id': 't2'},
            {'name': 'Dr. Verma', 'id': 't3'},
            {'name': 'Prof. Kumar', 'id': 't4'}
        ],
        'subjects': [
            {'name': 'Math', 'id': 's1'},
            {'name': 'Physics', 'id': 's2'},
            {'name': 'CS Lab', 'id': 's3'}
        ]
    }
}


def test_workload_calculation():
    """Test teacher workload calculation"""
    print("\n=== Testing Teacher Workload Calculation ===")
    
    metrics = compute_teacher_workload(SAMPLE_TIMETABLE, SAMPLE_CONTEXT)
    
    assert 'perTeacher' in metrics
    assert 'averageLectures' in metrics
    
    # Prof. Patel should have 6 lectures (overloaded on Monday)
    patel_workload = metrics['perTeacher'].get('Prof. Patel', {})
    print(f"Prof. Patel workload: {patel_workload}")
    assert patel_workload['totalLectures'] == 6
    assert patel_workload['classification'] in ['slight_overload', 'heavy_overload']
    
    # Generate insights
    insights = generate_workload_insights(metrics)
    print(f"Insights: {insights}")
    assert len(insights) > 0
    
    print("✅ Workload calculation test passed")


def test_lab_usage():
    """Test lab usage heatmap"""
    print("\n=== Testing Lab Usage Heatmap ===")
    
    metrics = compute_lab_heatmap(SAMPLE_TIMETABLE, SAMPLE_CONTEXT)
    
    assert 'perLab' in metrics
    assert 'overallUtilization' in metrics
    
    # Lab-1 should be used on Tuesday 9:00-10:00
    lab1_data = metrics['perLab'].get('Lab-1', {})
    print(f"Lab-1 data: {lab1_data}")
    assert lab1_data['heatmap']['Tuesday']['9:00-10:00'] == 1.0
    
    # Lab-3 should be unused
    lab3_data = metrics['perLab'].get('Lab-3', {})
    assert lab3_data['utilizationPercent'] == 0.0
    
    insights = analyze_lab_efficiency(metrics)
    print(f"Insights: {insights}")
    
    print("✅ Lab usage test passed")


def test_free_slots():
    """Test free slot identification"""
    print("\n=== Testing Free Slot Analysis ===")
    
    metrics = find_free_slots(SAMPLE_TIMETABLE, SAMPLE_CONTEXT)
    
    assert 'freeSlotsPerDay' in metrics
    assert 'totalFreeSlots' in metrics
    assert 'freePercentage' in metrics
    
    print(f"Total free slots: {metrics['totalFreeSlots']}")
    print(f"Free percentage: {metrics['freePercentage']}%")
    print(f"Free slots per day: {metrics['freeSlotsPerDay']}")
    
    # Should have plenty of free slots
    assert metrics['totalFreeSlots'] > 0
    
    insights = analyze_free_capacity(metrics)
    print(f"Insights: {insights}")
    
    print("✅ Free slot test passed")


def test_bottleneck_detection():
    """Test bottleneck detection"""
    print("\n=== Testing Bottleneck Detection ===")
    
    bottlenecks = detect_bottlenecks(SAMPLE_TIMETABLE, SAMPLE_CONTEXT)
    
    assert 'issues' in bottlenecks
    assert 'criticalCount' in bottlenecks
    
    # Should detect Prof. Patel overload (7 lectures on Monday)
    issues = bottlenecks['issues']
    print(f"Detected {len(issues)} bottlenecks:")
    for issue in issues:
        print(f"  - {issue['severity']}: {issue['title']}")
    
    # Check that overload is detected
    overload_found = any('Patel' in issue.get('title', '') for issue in issues)
    assert overload_found, "Should detect Prof. Patel overload"
    
    print("✅ Bottleneck detection test passed")


def test_quality_score():
    """Test quality score calculation"""
    print("\n=== Testing Quality Score ===")
    
    analytics = generate_full_analytics(SAMPLE_TIMETABLE, SAMPLE_CONTEXT)
    
    assert 'summary' in analytics
    summary = analytics['summary']
    
    assert 'qualityScore' in summary
    assert 'grade' in summary
    assert 'stars' in summary
    
    print(f"Quality Score: {summary['qualityScore']}/100")
    print(f"Grade: {summary['grade']}")
    print(f"Stars: {summary['stars']}/5")
    print(f"Top Issues: {summary.get('topIssues', [])}")
    print(f"Top Strengths: {summary.get('topStrengths', [])}")
    
    # Score should be reasonable (not extreme)
    assert 0 <= summary['qualityScore'] <= 100
    assert 1 <= summary['stars'] <= 5
    
    print("✅ Quality score test passed")


def test_full_analytics():
    """Test full analytics generation"""
    print("\n=== Testing Full Analytics Generation ===")
    
    analytics = generate_full_analytics(SAMPLE_TIMETABLE, SAMPLE_CONTEXT)
    
    # Check all sections present
    required_sections = ['workload', 'labUsage', 'freeSlots', 'bottlenecks', 'summary']
    for section in required_sections:
        assert section in analytics, f"Missing section: {section}"
        print(f"✓ {section} section present")
    
    # Check data structure
    assert 'metrics' in analytics['workload']
    assert 'insights' in analytics['workload']
    assert 'metrics' in analytics['labUsage']
    assert 'issues' in analytics['bottlenecks']
    
    print("✅ Full analytics test passed")


if __name__ == '__main__':
    print("Running Analytics Module Tests...")
    print("=" * 60)
    
    try:
        test_workload_calculation()
        test_lab_usage()
        test_free_slots()
        test_bottleneck_detection()
        test_quality_score()
        test_full_analytics()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
