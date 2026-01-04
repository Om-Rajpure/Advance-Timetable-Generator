
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from analytics.analytics_engine import generate_full_analytics

# 1. Mock Context based on User's likely state
mock_branch_data = {
    "academicYears": ["SE", "TE", "BE"],
    "divisions": { "SE": ["A", "B"], "TE": ["A"], "BE": ["A"] },
    "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "timeSlots": ["9:00-10:00", "10:00-11:00"]
}

mock_smart_input = {
    "teachers": [{"name": "Teacher 1"}, {"name": "Teacher 14"}],
    "subjects": []
}

context = {
    "branchData": mock_branch_data,
    "smartInputData": mock_smart_input
}

# 2. Mock Timetable based on 'debug_rooms.txt'
# "Unique Rooms: ['BE-1', 'Computer Lab 1', ... 'SE-1', 'TE-1']"
# "Sample Slot": type="THEORY", room="BE-1", year="BE"

mock_timetable = [
    # Slot 1: BE-1 (Ghost-like name)
    {
        "day": "Monday",
        "division": "A",
        "room": "BE-1", 
        "slot": 1,
        "time": "9:00-10:00",
        "subject": "Theory Sub",
        "teacher": "Teacher 14",
        "type": "THEORY",
        "year": "BE"
    },
    # Slot 2: SE-1 (Ghost-like name)
    {
        "day": "Monday",
        "division": "A",
        "room": "SE-1",
        "slot": 2,
        "time": "10:00-11:00",
        "subject": "Theory Sub 2",
        "teacher": "Teacher 1",
        "type": "THEORY",
        "year": "SE"
    },
    # Slot 3: Computer Lab 1 (Valid Lab)
    {
        "day": "Tuesday",
        "division": "A",
        "room": "Computer Lab 1",
        "slot": 1,
        "time": "9:00-10:00",
        "subject": "Lab Sub",
        "teacher": "Teacher 2",
        "type": "LAB",
        "year": "SE"
    }
]

print("--- Running Analytics Verification ---")
try:
    results = generate_full_analytics(mock_timetable, context)
    
    print("\n[Classroom Usage Metrics]")
    c_metrics = results.get('classroomUsage', {}).get('metrics', {})
    per_room = c_metrics.get('perClassroom', {})
    
    # Check if we have data
    if not per_room:
        print("\n❌ FAILURE: perClassroom is EMPTY.")
    else:
        print(f"\n✅ SUCCESS: Found {len(per_room)} classrooms.")
        for name in per_room:
            print(f"   - Room Name: '{name}'")
            
            # Check if it was renamed
            if "Room" not in name and name in ["SE-1", "TE-1", "BE-1"]:
                print(f"     ⚠️ WARNING: Room '{name}' was NOT renamed!")
            elif "Room" in name:
                print(f"     ✅ Verified: Room '{name}' was renamed correctly.")

    print("\n[Free Slots Metrics]")
    fs_metrics = results.get('freeSlots', {}).get('metrics', {})
    room_util = fs_metrics.get('roomUtilization', {})
    print("Room Utilization:", json.dumps(room_util, indent=2))
    
    # Verify free rooms per day
    print("Free Rooms Per Day:", json.dumps(fs_metrics.get('freeRoomsPerDay', {}), indent=2))

except Exception as e:
    print(f"\n❌ CRASH: {e}")
    import traceback
    traceback.print_exc()
