
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from analytics.analytics_engine import generate_full_analytics

# Mock Data
mock_branch_data = {
    "rooms": ["R101", "R102"], # Standard key for classrooms in this app seems to be 'rooms'
    "classrooms": [{"name": "R101", "capacity": 60}, {"name": "R102", "capacity": 60}], # Potential alternative
    "workingDays": ["Monday", "Tuesday"],
    "timeSlots": ["9:00-10:00", "10:00-11:00"]
}

mock_smart_input = {}

# Mock Timetable (List of slots)
# We need to simulate how the scheduler actually outputs data.
# Based on typical observation: 'room' key holds the classroom for theory.
mock_timetable = [
    {
        "day": "Monday",
        "time": "9:00-10:00",
        "type": "THEORY",
        "room": "R101",
        "subject": "Math",
        "teacher": "T1"
    },
    {
        "day": "Monday",
        "time": "10:00-11:00", 
        "type": "LECTURE", # Alternative type check
        "room": "R102",
        "subject": "Physics",
        "teacher": "T2"
    },
    {
        "day": "Monday", 
        "time": "9:00-10:00",
        "type": "LAB",
        "room": "Lab1", # Should be ignored by classroom analytics
        "subject": "CS Lab",
        "teacher": "T3"
    }
]

context = {
    "branchData": mock_branch_data,
    "smartInputData": mock_smart_input
}

print("--- Running Analytics ---")
try:
    results = generate_full_analytics(mock_timetable, context)
    
    print("\n[Classroom Usage Metrics]")
    c_metrics = results.get('classroomUsage', {}).get('metrics', {})
    print(json.dumps(c_metrics, indent=2))
    
    per_room = c_metrics.get('perClassroom', {})
    if not per_room:
        print("\n❌ FAIL: perClassroom is empty!")
    else:
        print(f"\n✅ SUCCESS: Found {len(per_room)} classrooms.")
        for name, data in per_room.items():
            occupied = sum(1 for d in data['heatmap'].values() for v in d.values() if v > 0)
            print(f"   - {name}: {occupied} slots occupied")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
