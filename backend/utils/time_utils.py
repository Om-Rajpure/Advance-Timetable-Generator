
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


def _compute_recess_slot_index(start_time_str, recess_start_str, lecture_duration_minutes):
    """
    Return the zero-based teaching-slot index that corresponds to the recess period.

    The recess begins immediately after a whole number of teaching slots have
    elapsed since the day start, so we simply count how many full
    lecture_duration_minutes fit between start_time and recess_start.

    Args:
        start_time_str:          e.g. "9:00 AM"
        recess_start_str:        e.g. "1:00 PM"
        lecture_duration_minutes: e.g. 60

    Returns:
        int: zero-based slot index of the recess slot
             e.g. start=9am, recess=1pm, dur=60 → (240/60) = 4

    Raises:
        ValueError: if the times cannot be parsed or duration <= 0
    """
    def to_minutes(time_str):
        t = parse_time(time_str)
        if t is None:
            raise ValueError(f"Cannot parse time string: '{time_str}'")
        return t.hour * 60 + t.minute

    duration = int(lecture_duration_minutes)
    if duration <= 0:
        raise ValueError("lecture_duration_minutes must be positive")

    start_min = to_minutes(start_time_str)
    recess_min = to_minutes(recess_start_str)

    if recess_min <= start_min:
        raise ValueError(
            f"Recess start ({recess_start_str}) must be after day start ({start_time_str})"
        )

    return (recess_min - start_min) // duration


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
        recess_dur = int(branch_data.get('recessDuration', 60))

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
            'slot_index': teaching_count  # internal index 0..N
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

    FIX 3: recess_slot now returns the actual integer teaching-slot index
    (not None) when recessEnabled=True.  When recessEnabled=False it stays
    None so all existing `if recess_slot is not None` guards work unchanged.
    """
    try:
        struct = generate_day_structure(branch_data)

        # --- FIX 3: Compute real recess slot index ---
        recess_enabled = branch_data.get('recessEnabled') or False
        recess_slot = None

        if recess_enabled:
            recess_start_str = branch_data.get('recessStart')
            start_str = branch_data.get('startTime', '9:00 AM')
            lecture_dur = int(branch_data.get('lectureDuration', 60))

            if recess_start_str:
                try:
                    recess_slot = _compute_recess_slot_index(
                        start_str,
                        recess_start_str,
                        lecture_dur
                    )
                except (ValueError, Exception) as e:
                    print(f"WARNING: Could not compute recess_slot index: {e}. Defaulting to None.")
                    recess_slot = None
        # --- END FIX 3 ---

        # Store computed index back into branch_data so CP-SAT TheoryScheduler
        # (and any other module) can read it via context["branchData"]["_computed_recess_slot"]
        # without recomputing.  Only write when we have a valid integer.
        if isinstance(recess_slot, int):
            branch_data["_computed_recess_slot"] = recess_slot

        return {
            'total_slots': struct['teaching_slots_count'],  # Only teaching slots!
            'recess_slot': recess_slot,                     # FIX 3: real index or None
            'slots_per_day': struct['teaching_slots_count'],
            'layout_debug': struct['layout']                # For debug if needed
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
    if not login_time_str or not slot_start_time:
        return True
    login_time = parse_time(login_time_str)
    if not login_time:
        return True

    slot_start_mins = slot_start_time.hour * 60 + slot_start_time.minute
    login_mins = login_time.hour * 60 + login_time.minute
    window_end_mins = login_mins + (working_hours * 60)
    slot_end_mins = slot_start_mins + slot_duration_minutes

    return (slot_start_mins >= login_mins) and (slot_end_mins <= window_end_mins)
