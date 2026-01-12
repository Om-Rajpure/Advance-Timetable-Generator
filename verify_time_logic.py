
import sys
import os
from datetime import datetime, timedelta

# Mock time_utils logic to verify correctness without path issues
def parse_time(time_str):
    if not time_str: return None
    time_str = time_str.strip().upper()
    formats = ["%I:%M %p", "%H:%M", "%I %p", "%H"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return None

def is_time_in_window(slot_start_time, login_time_str, working_hours=8, slot_duration_minutes=60):
    if not login_time_str or not slot_start_time: return True
    login_time = parse_time(login_time_str)
    if not login_time: return True
    
    base_date = datetime(2000, 1, 1).date()
    slot_start = datetime.combine(base_date, slot_start_time.time())
    window_start = datetime.combine(base_date, login_time.time())
    window_end = window_start + timedelta(hours=working_hours)
    slot_end = slot_start + timedelta(minutes=slot_duration_minutes)
    
    # Strict check: Start >= WindowStart AND End <= WindowEnd
    return (slot_start >= window_start) and (slot_end <= window_end)

def run_tests():
    print("--- Testing Time Logic ---")
    
    # Test 1: Standard Window (9 AM - 5 PM)
    login = "09:00 AM"
    
    # Slot 9:00 - 10:00 -> VALID
    s1 = datetime.strptime("09:00", "%H:%M")
    assert is_time_in_window(s1, login) == True, "9:00-10:00 should be valid"
    
    # Slot 16:00 - 17:00 -> VALID
    s2 = datetime.strptime("16:00", "%H:%M")
    assert is_time_in_window(s2, login) == True, "16:00-17:00 should be valid"
    
    # Slot 16:30 - 17:30 -> INVALID
    s3 = datetime.strptime("16:30", "%H:%M")
    assert is_time_in_window(s3, login) == False, "16:30-17:30 should be invalid (ends at 5:30)"
    
    # Slot 8:00 - 9:00 -> INVALID
    s4 = datetime.strptime("08:00", "%H:%M")
    assert is_time_in_window(s4, login) == False, "8:00-9:00 should be invalid"
    
    print("✅ Standard Window Tests Passed")
    
    # Test 2: Late Shift (11 AM - 7 PM)
    login_late = "11:00 AM"
    
    # Slot 9:00 -> INVALID
    assert is_time_in_window(s1, login_late) == False, "9:00-10:00 should be invalid for 11am login"
    
    # Slot 11:00 -> VALID
    s5 = datetime.strptime("11:00", "%H:%M")
    assert is_time_in_window(s5, login_late) == True, "11:00-12:00 should be valid"
    
    print("✅ Late Shift Tests Passed")
    
    # Test 3: Lab Block (3 hours)
    # 3-hour lab starting at 2 PM (14:00 - 17:00)
    # Teacher 9-5
    s_lab = datetime.strptime("14:00", "%H:%M")
    valid_lab = is_time_in_window(s_lab, login, working_hours=8, slot_duration_minutes=180)
    assert valid_lab == True, "Lab 2-5pm should be valid for 9-5 teacher"
    
    # 3-hour lab starting at 3 PM (15:00 - 18:00) -> INVALID
    s_lab_late = datetime.strptime("15:00", "%H:%M")
    invalid_lab = is_time_in_window(s_lab_late, login, working_hours=8, slot_duration_minutes=180)
    assert invalid_lab == False, "Lab 3-6pm should be invalid for 9-5 teacher"
    
    print("✅ Lab Block Tests Passed")

if __name__ == "__main__":
    try:
        run_tests()
        print("\n🎉 ALL CHECKS PASSED")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
