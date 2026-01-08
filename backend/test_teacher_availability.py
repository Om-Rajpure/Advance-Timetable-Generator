
import pytest
from datetime import datetime
from engine.state_manager import TimetableState
from utils.time_utils import parse_time

# Mock Context
def get_mock_context():
    return {
        "branchData": {
            "startTime": "09:00 AM",
            "lectureDuration": 60,
            "recessEnabled": False,
            "academicYears": ["SE"],
            "divisions": {"SE": ["A"]}
        },
        "smartInputData": {
            "teachers": [
                {
                    "name": "EarlyBird",
                    "loginTime": "09:00"
                },
                {
                    "name": "LateRiver",
                    "loginTime": "11:00" 
                },
                {
                    "name": "NoConstraint",
                    # No loginTime
                }
            ],
            "subjects": []
        }
    }

def test_teacher_availability_window():
    context = get_mock_context()
    state = TimetableState(context)
    
    # CASE 1: No Constraint Teacher
    # Should be available everywhere (unless assigned)
    assert state.is_teacher_available("NoConstraint", "Monday", 0) == True
    assert state.is_teacher_available("NoConstraint", "Monday", 10) == True
    
    # CASE 2: EarlyBird (9:00 - 17:00)
    # Slot 0 (9:00) -> OK
    assert state.is_teacher_available("EarlyBird", "Monday", 0) == True
    
    # Slot 7 (16:00-17:00) -> OK (Start 16:00 < 17:00)
    assert state.is_teacher_available("EarlyBird", "Monday", 7) == True
    
    # Slot 8 (17:00-18:00) -> INVALID (Start 17:00 >= 17:00?? Wait. 9+8=17:00 end?
    # Logic: Start + 8 hours = End Time.
    # 09:00 + 8 = 17:00.
    # Slot 8 starts at 17:00.
    # is_time_in_window checks: login <= start < end
    # 17:00 < 17:00 is False.
    # So Slot 8 should be unavailable.
    assert state.is_teacher_available("EarlyBird", "Monday", 8) == False
    
    # CASE 3: LateRiver (11:00 - 19:00)
    # Slot 0 (9:00) -> INVALID
    assert state.is_teacher_available("LateRiver", "Monday", 0) == False
    
    # Slot 1 (10:00) -> INVALID
    assert state.is_teacher_available("LateRiver", "Monday", 1) == False
    
    # Slot 2 (11:00) -> VALID
    assert state.is_teacher_available("LateRiver", "Monday", 2) == True
    
    # Slot 9 (18:00) -> VALID (11+8=19:00. 18:00 < 19:00)
    assert state.is_teacher_available("LateRiver", "Monday", 9) == True
    
if __name__ == "__main__":
    test_teacher_availability_window()
    print("✅ All teacher availability tests passed!")
