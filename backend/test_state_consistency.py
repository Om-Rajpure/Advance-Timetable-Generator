
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.state_manager import TimetableState

def run_test():
    print("TESTING TimetableState Consistency...")
    context = {"branchData": {"slotsPerDay": 8}, "smartInputData": {}}
    state = TimetableState(context)
    
    # 1. Assign Room 101 at Mon, Slot 1
    assign1 = {
        "day": "Monday", "slot": 1, "year": "SE", "division": "A",
        "subject": "Sub1", "teacher": "T1", "type": "THEORY",
        "room": "Room_101", "id": "TEST_1"
    }
    
    print("Assigning TEST_1...")
    state.assign_slot(assign1)
    
    # Check if Room 101 is available
    is_free = state.is_room_available("Room_101", "Monday", 1)
    print(f"Room_101 Free? {is_free} (Expected: False)")
    
    # Check is_slot_free for SE-A
    slot_free = state.is_slot_free("Monday", 1, "SE", "A")
    print(f"SE-A Slot 1 Free? {slot_free} (Expected: False)")
    
    # 2. Try to assign Room 101 again (collision scenario)
    assign2 = {
        "day": "Monday", "slot": 1, "year": "TE", "division": "A",
        "subject": "Sub2", "teacher": "T2", "type": "THEORY",
        "room": "Room_101", "id": "TEST_2"
    }
    
    # Should not prevent assignment (assign_slot is dumb), but is_room_available should have warned prior
    print("Checking Room 101 for TEST_2...")
    is_free_2 = state.is_room_available("Room_101", "Monday", 1)
    print(f"Room_101 Free for TEST_2? {is_free_2} (Expected: False)")

    state.assign_slot(assign2)
    
    # Check if Room 101 has 2 assignments
    room_key = ("Room_101", "Monday", 1)
    assignments = state.room_assignments.get(room_key)
    print(f"Assignments for Room_101: {len(assignments) if assignments else 0}")
    if assignments:
        print([a['id'] for a in assignments])

if __name__ == "__main__":
    run_test()
