"""
Free Slot Analysis

Identifies unused capacity in the timetable for future planning.
"""

from collections import defaultdict


def find_free_slots(timetable, context):
    """
    Identify all free slots in the timetable.
    
    Args:
        timetable: List of slot dictionaries
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "freeSlotsPerDay": {"Monday": int, ...},
            "freeSlotsPerDivision": {"FE-A": int, ...},
            "availableLabs": {day: {time: [lab_names]}},
            "availableRooms": {day: {time: [room_names]}},
            "totalFreeSlots": int,
            "totalOccupiedSlots": int,
            "freePercentage": float,
            "bestDaysForAdditions": [{"day": str, "freeSlots": int}]
        }
    """
    branch_data = context.get('branchData', {})
    working_days = branch_data.get('workingDays', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
    time_slots = branch_data.get('timeSlots', [])
    divisions = branch_data.get('divisions', {})
    labs = branch_data.get('labs', [])
    rooms = branch_data.get('rooms', [])
    
    if not time_slots:
        time_slots = [
            "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00",
            "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
        ]
    
    # Flatten divisions into list
    all_divisions = []
    for year, divs in divisions.items():
        for div in divs:
            all_divisions.append(f"{year}-{div}")
    
    # Track occupied slots
    occupied_division_slots = set()
    occupied_labs = defaultdict(set)
    occupied_rooms = defaultdict(set)
    
    for slot in timetable:
        year = slot.get('year')
        division = slot.get('division')
        day = slot.get('day')
        time = slot.get('time')
        slot_type = slot.get('type')
        room = slot.get('room')
        lab = slot.get('lab')
        
        if year and division and day and time:
            div_key = f"{year}-{division}"
            occupied_division_slots.add((div_key, day, time))
        
        if day and time:
            if slot_type == 'Practical' and (lab or room):
                occupied_labs[(day, time)].add(lab or room)
            elif slot_type == 'Lecture' and room:
                occupied_rooms[(day, time)].add(room)
    
    # Calculate free slots per day
    free_slots_per_day = {}
    for day in working_days:
        free_count = 0
        for time_slot in time_slots:
            for div in all_divisions:
                if (div, day, time_slot) not in occupied_division_slots:
                    free_count += 1
        free_slots_per_day[day] = free_count
    
    # Calculate free slots per division
    free_slots_per_division = {}
    for div in all_divisions:
        free_count = 0
        for day in working_days:
            for time_slot in time_slots:
                if (div, day, time_slot) not in occupied_division_slots:
                    free_count += 1
        free_slots_per_division[div] = free_count
    
    # Find available labs and rooms
    available_labs = defaultdict(lambda: defaultdict(list))
    available_rooms = defaultdict(lambda: defaultdict(list))
    
    for day in working_days:
        for time_slot in time_slots:
            # Available labs
            used_labs = occupied_labs.get((day, time_slot), set())
            for lab in labs:
                lab_name = lab if isinstance(lab, str) else lab.get('name', lab)
                if lab_name not in used_labs:
                    available_labs[day][time_slot].append(lab_name)
            
            # Available rooms
            used_rooms = occupied_rooms.get((day, time_slot), set())
            for room in rooms:
                room_name = room if isinstance(room, str) else room.get('name', room)
                if room_name not in used_rooms:
                    available_rooms[day][time_slot].append(room_name)
    
    # Calculate totals
    total_possible_slots = len(all_divisions) * len(working_days) * len(time_slots) if all_divisions else 0
    total_occupied = len(occupied_division_slots)
    total_free = total_possible_slots - total_occupied
    free_percentage = (total_free / total_possible_slots * 100) if total_possible_slots > 0 else 0
    
    # Best days for additions (sorted by free slots)
    best_days = sorted(
        [{"day": day, "freeSlots": count} for day, count in free_slots_per_day.items()],
        key=lambda x: x['freeSlots'],
        reverse=True
    )
    
    return {
        "freeSlotsPerDay": free_slots_per_day,
        "freeSlotsPerDivision": free_slots_per_division,
        "availableLabs": {day: dict(times) for day, times in available_labs.items()},
        "availableRooms": {day: dict(times) for day, times in available_rooms.items()},
        "totalFreeSlots": total_free,
        "totalOccupiedSlots": total_occupied,
        "freePercentage": round(free_percentage, 1),
        "bestDaysForAdditions": best_days
    }


def analyze_free_capacity(free_slot_metrics):
    """
    Analyze free capacity and generate insights.
    
    Args:
        free_slot_metrics: Output from find_free_slots
    
    Returns:
        List of insight strings
    """
    insights = []
    
    free_per_day = free_slot_metrics.get('freeSlotsPerDay', {})
    free_per_div = free_slot_metrics.get('freeSlotsPerDivision', {})
    free_percentage = free_slot_metrics.get('freePercentage', 0)
    best_days = free_slot_metrics.get('bestDaysForAdditions', [])
    
    # Overall capacity
    if free_percentage > 50:
        insights.append(f"📊 Significant free capacity available ({free_percentage}% of slots unused)")
    elif free_percentage < 10:
        insights.append(f"⚠️ Very limited free capacity ({free_percentage}% - timetable is dense)")
    
    # Best days for additions
    if best_days:
        top_day = best_days[0]
        insights.append(f"📅 {top_day['day']} has the most free capacity ({top_day['freeSlots']} slots available)")
    
    # Divisions with most flexibility
    if free_per_div:
        sorted_divisions = sorted(free_per_div.items(), key=lambda x: x[1], reverse=True)
        if sorted_divisions:
            top_div, free_count = sorted_divisions[0]
            insights.append(f"🎓 {top_div} has maximum flexibility ({free_count} free slots for additional lectures)")
    
    # Check for days with very low capacity
    for day, free_count in free_per_day.items():
        if free_count < 5:
            insights.append(f"⚠️ {day} has very limited free capacity ({free_count} slots - difficult to add classes)")
    
    if not insights:
        insights.append("✅ Free capacity is reasonably distributed across the week")
    
    return insights
