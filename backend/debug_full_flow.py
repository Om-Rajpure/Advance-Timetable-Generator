
import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from analytics.analytics_engine import generate_full_analytics
from engine.scheduler import TimetableScheduler

# 1. MIRROR SMART INPUT DUMMY DATA EXACTLY
mock_branch_data = {
    "rooms": ["Room_101", "Room_102", "Room_103", "Room_104"],
    "classrooms": [
        { "name": "Room_101", "capacity": 60 },
        { "name": "Room_102", "capacity": 60 },
        { "name": "Room_103", "capacity": 60 },
        { "name": "Room_104", "capacity": 60 }
    ],
    "workingDays": ["Monday", "Tuesday"],
    "timeSlots": ["9:00-10:00", "10:00-11:00"],
    "academicYears": ["SE", "TE"],
    "divisions": { "SE": ["A", "B"], "TE": ["A"] }
}

mock_smart_input = {
    "subjects": [],
    "teachers": []
}

# 2. CREATE RAW SLOTS WITHOUT ROOMS (Simulating Scheduler State)
# These represent slots found by the CSP engine but not yet formatted
raw_slots = [
    {
        "year": "SE", "division": "A", "day": "Monday", "slot": 1,
        "type": "THEORY", "subject": "Math", "teacher": "T1",
        "room": None, # Unassigned initially
        "id": "s1", "isPractical": False
    },
    {
        "year": "SE", "division": "B", "day": "Monday", "slot": 1,
        "type": "THEORY", "subject": "Physics", "teacher": "T2",
        "room": "", # Empty string
        "id": "s2", "isPractical": False
    }
]

context = {
    "branchData": mock_branch_data,
    "smartInputData": mock_smart_input
}

print("--- 1. Testing Format to Canonical (Room Assignment) ---")
scheduler = TimetableScheduler(context)

# Inject raw slots into format_to_canonical
try:
    canonical = scheduler.format_to_canonical(raw_slots)
    
    # Extract flattened timetable for analytics
    flat_timetable = []
    for year_data in canonical.values():
        for day_slots in year_data.values():
             flat_timetable.extend(day_slots)
             
    print(f"\n[Normalized Slots]: {len(flat_timetable)}")
    for s in flat_timetable:
        print(f"  - {s['year']}-{s['division']} ({s['type']}): Room='{s.get('room')}'")
        
    if not flat_timetable:
        print("❌ ERROR: No slots returned from canonical format!")
        sys.exit(1)
        
    # Check if rooms assigned
    has_rooms = all(s.get('room') and "Room" in s.get('room') for s in flat_timetable)
    if not has_rooms:
        print("\n❌ FAIL: Rooms were NOT assigned correctly!")
    else:
        print("\n✅ SUCCESS: Rooms assigned from Branch Data.")

    print("\n--- 2. Testing Analytics on Result ---")
    results = generate_full_analytics(flat_timetable, context)
    
    c_metrics = results.get('classroomUsage', {}).get('metrics', {})
    per_room = c_metrics.get('perClassroom', {})
    
    print(json.dumps(c_metrics, indent=2))
    
    if not per_room:
        print("\n❌ ANALYTICS FAIL: perClassroom is empty!")
    else:
        print(f"\n✅ ANALYTICS SUCCESS: Found {len(per_room)} classrooms tracked.")
        for name in per_room:
             print(f"   Tracked: {name}")

except Exception as e:
    print(f"\n❌ CRASH: {e}")
    import traceback
    traceback.print_exc()
