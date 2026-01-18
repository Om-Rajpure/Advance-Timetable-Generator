
from datetime import datetime, timedelta

def parse_time(time_str):
    """Parse time string (e.g., '9:00 AM') into datetime object."""
    if not time_str:
        return None
    time_str = time_str.strip().upper()
    formats = ["%I:%M %p", "%H:%M", "%I %p", "%H"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return None

def generate_day_structure(branch_data):
    """
    Generates the strict time-interval based day structure.
    Returns:
        {
            'layout': [ {type, start, end, label, is_recess}, ... ],
            'teaching_slots_count': int,
            'recess_index': int (in the layout list) or None
        }
    """
    start_str = branch_data.get('startTime', '9:00 AM')
    end_str = branch_data.get('endTime', '5:00 PM')
    slot_dur = int(branch_data.get('lectureDuration', 60))
    
    start_time = parse_time(start_str)
    end_time = parse_time(end_str)
    
    # Recess Config - STRICT
    recess_enabled = branch_data.get('recessEnabled') or False
    recess_start = None
    recess_dur = 0
    
    if recess_enabled:
        recess_str = branch_data.get('recessStart')
        if not recess_str:
            raise ValueError("Recess Enabled but no 'recessStart'.")
        recess_start = parse_time(recess_str)
        # Strict duration key?
        recess_dur = int(branch_data.get('recessDuration', 60)) # Default to 60 if missing? Or strict? 
        # Prompt says "Recess duration (e.g. 45 minutes) does not match slot duration". 
        # implying it comes from somewhere. 'breakDuration' legacy? 
        # "Batch Inputs are the ONLY authority... RecessConfig {start, duration...}"
        # I'll enable 'recessDuration' key.

    layout = []
    current_time = start_time
    teaching_count = 0
    recess_idx = None
    
    # Tolerance for float math? using timedeltas so usually safe.
    # Loop while we have room for at least one slot OR we hit recess
    
    while current_time < end_time:
        # Check Recess Alignment
        # If we are exactly at recess start
        if recess_enabled and recess_start and abs((current_time - recess_start).total_seconds()) < 60:
            # Insert Recess
            r_end = current_time + timedelta(minutes=recess_dur)
            layout.append({
                'type': 'recess',
                'start': current_time,
                'end': r_end,
                'label': 'Recess',
                'is_recess': True
            })
            recess_idx = len(layout) - 1
            current_time = r_end
            continue
            
        # Ensure we fit a full slot before end_time?
        # If remaining time < slot_dur, stop?
        if (end_time - current_time).total_seconds() / 60 < slot_dur:
            break
            
        # Create Slot
        s_end = current_time + timedelta(minutes=slot_dur)
        label = f"{current_time.strftime('%I:%M %p')} - {s_end.strftime('%I:%M %p')}"
        layout.append({
            'type': 'lecture',
            'start': current_time,
            'end': s_end,
            'label': label,
            'is_recess': False,
            'slot_index': teaching_count # internal index 0..N
        })
        teaching_count += 1
        current_time = s_end
        
    return {
        'layout': layout,
        'teaching_slots_count': teaching_count,
        'recess_index': recess_idx
    }

def calculate_time_slots(branch_data):
    """
    Wrap new structure generator for legacy compatibility.
    """
    try:
        struct = generate_day_structure(branch_data)
        return {
            'total_slots': struct['teaching_slots_count'], # Only teaching slots!
            'recess_slot': None, # We don't want StateManager to block valid indices
            'slots_per_day': struct['teaching_slots_count'],
            'layout_debug': struct['layout'] # For debug if needed
        }
    except Exception as e:
        # Fallback? Strict -> Raise
        raise e

def get_slot_time(slot_index, branch_data):
    """
    Get start time for a teaching slot index (skipping recess).
    """
    # Use structure
    struct = generate_day_structure(branch_data)
    # Find item with slot_index == index
    for item in struct['layout']:
        if not item['is_recess'] and item.get('slot_index') == slot_index:
            return item['start']
    return None

def is_time_in_window(slot_start_time, login_time_str, working_hours=8, slot_duration_minutes=60):
    if not login_time_str or not slot_start_time: return True
    login_time = parse_time(login_time_str)
    if not login_time: return True
    
    slot_start_mins = slot_start_time.hour * 60 + slot_start_time.minute
    login_mins = login_time.hour * 60 + login_time.minute
    window_end_mins = login_mins + (working_hours * 60)
    slot_end_mins = slot_start_mins + slot_duration_minutes
    
    return (slot_start_mins >= login_mins) and (slot_end_mins <= window_end_mins)
