from datetime import datetime, timedelta

def parse_time(time_str):
    """Parse time string (e.g., '9:00 AM') into datetime object."""
    try:
        return datetime.strptime(time_str, "%I:%M %p")
    except ValueError:
        # Try simplified formats
        try:
             return datetime.strptime(time_str, "%H:%M")
        except:
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
