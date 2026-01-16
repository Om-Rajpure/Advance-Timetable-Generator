from datetime import datetime, timedelta

def parse_time(time_str):
    """Parse time string (e.g., '9:00 AM') into datetime object."""
    if not time_str:
        return None
    
    time_str = time_str.strip().upper()
    formats = [
        "%I:%M %p", # 09:00 AM
        "%H:%M",    # 14:00
        "%I %p",    # 9 AM
        "%H"        # 14
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
            
    return None

def calculate_time_slots(branch_data):
    """
    Calculate the total number of slots and the recess slot index.
    
    Returns:
        dict: {
            'total_slots': int,
            'recess_slot': int or None (0-indexed index of the recess),
            'slots_per_day': int
        }
    """
    start_str = branch_data.get('startTime', '9:00 AM')
    end_str = branch_data.get('endTime', '5:00 PM')
    duration = int(branch_data.get('lectureDuration', 60))
    
    recess_enabled = branch_data.get('recessEnabled', False)
    recess_start_str = branch_data.get('recessStart', '1:00 PM')
    
    start_time = parse_time(start_str)
    end_time = parse_time(end_str)
    recess_start = parse_time(recess_start_str)
    
    if not start_time or not end_time or duration <= 0:
        return {'total_slots': 8, 'recess_slot': None, 'slots_per_day': 8}
    
    # Calculate total minutes
    day_minutes = (end_time - start_time).seconds // 60
    
    # Approximate slots (including recess)
    total_slots = day_minutes // duration
    
    recess_slot = None
    if recess_enabled and recess_start:
        # Calculate which slot index corresponds to recess start
        minutes_to_recess = (recess_start - start_time).seconds // 60
        recess_slot = minutes_to_recess // duration
    
    return {
        'total_slots': total_slots,
        'recess_slot': recess_slot,
        'slots_per_day': total_slots
    }

def get_slot_time(slot_index, branch_data):
    """
    Get the start time of a specific slot index.
    
    Args:
        slot_index: 0-based index of the slot
        branch_data: Dict with 'startTime', 'lectureDuration', 'recessEnabled', 'recessStart'
        
    Returns:
        datetime object representing start of the slot
    """
    start_str = branch_data.get('startTime', '9:00 AM')
    duration = int(branch_data.get('lectureDuration', 60))
    start_time = parse_time(start_str)
    
    # Recess handling
    recess_enabled = branch_data.get('recessEnabled', False)
    if recess_enabled:
        recess_start_str = branch_data.get('recessStart', '1:00 PM')
        recess_start = parse_time(recess_start_str)
        
        # Calculate recess slot index
        minutes_to_recess = (recess_start - start_time).seconds // 60
        recess_slot_idx = minutes_to_recess // duration
        
        # If the requested slot is AFTER recess, add recess duration (usually 1 slot or custom?)
        # For simplicity, assuming recess is ONE slot duration gap
        if slot_index > recess_slot_idx:
            # We skip the recess slot visually, so effectively we add 1 * duration
            # But wait, slot_index IS the visual index. 
            # If slot_index 4 is post-recess, its time is start + 4*dur + recess_dur.
            # Assuming recess takes 1 slot width.
            start_time += timedelta(minutes=duration) 
            
    # Calculate offset
    slot_offset = slot_index * duration
    return start_time + timedelta(minutes=slot_offset)

def is_time_in_window(slot_start_time, login_time_str, working_hours=8, slot_duration_minutes=60):
    """
    Check if a slot (start to start+duration) falls STRICTLY within [login_time, login_time + working_hours].
    
    Args:
        slot_start_time: datetime object
        login_time_str: string "HH:MM" or "HH:MM AM/PM"
        working_hours: int, default 8
        slot_duration_minutes: int, duration of the slot/lecture in minutes
        
    Returns:
        bool: True if inside window
    """
    if not login_time_str or not slot_start_time:
        return True # Fail open if data missing
        
    login_time = parse_time(login_time_str)
    if not login_time:
        return True # Fail open
        
    # Normalize to Minutes from Midnight for robust comparison
    slot_start_mins = slot_start_time.hour * 60 + slot_start_time.minute
    
    # Login Time Minutes
    login_mins = login_time.hour * 60 + login_time.minute
    
    # Window End Minutes
    window_end_mins = login_mins + (working_hours * 60)
    
    # Slot End Minutes
    slot_end_mins = slot_start_mins + slot_duration_minutes
    
    # STRICT CHECK:
    # 1. Slot Start >= Login Time
    # 2. Slot End <= Window End
    
    in_window = (slot_start_mins >= login_mins) and (slot_end_mins <= window_end_mins)
    
    return in_window

