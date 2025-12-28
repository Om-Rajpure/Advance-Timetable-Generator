"""
Auto-Fix Suggestions

Generates intelligent fix suggestions for conflicts.
"""

from constraints.constraint_engine import ConstraintEngine


def suggest_fix(slot, conflicts, timetable, context):
    """
    Suggest fixes for slot conflicts.
    
    Args:
        slot: The problematic slot
        conflicts: List of conflicts
        timetable: Full timetable
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "fix": {...} or None,
            "explanation": str,
            "strategy": str
        }
    """
    if not conflicts:
        return {"fix": None, "explanation": "No conflicts to fix", "strategy": None}
    
    # Analyze conflict type
    primary_conflict = conflicts[0]
    constraint_name = primary_conflict.get('constraint', '')
    
    # Try different strategies based on conflict type
    if 'TEACHER' in constraint_name.upper():
        return _try_alternate_teacher(slot, timetable, context)
    
    elif 'ROOM' in constraint_name.upper():
        return _try_alternate_room(slot, timetable, context)
    
    elif 'PRACTICAL' in constraint_name.upper():
        return {
            "fix": None,
            "explanation": "Practical slots require manual adjustment",
            "strategy": None
        }
    
    else:
        return {
            "fix": None,
            "explanation": "No automatic fix available for this conflict type",
            "strategy": None
        }


def find_alternate_teacher(slot, timetable, context):
    """
    Find an available alternate teacher for this slot.
    
    Returns:
        List of available teacher names
    """
    smart_input = context.get('smartInputData', {})
    teachers = smart_input.get('teachers', [])
    subject = slot.get('subject')
    day = slot.get('day')
    slot_index = slot.get('slot')
    
    # Find teachers who can teach this subject
    qualified_teachers = []
    
    for teacher_data in teachers:
        teacher_name = teacher_data.get('name')
        teacher_subjects = teacher_data.get('subjects', [])
        
        # Check if teacher can teach subject
        if not teacher_subjects or subject in teacher_subjects:
            # Check if teacher is available at this time
            if _is_teacher_available(teacher_name, day, slot_index, timetable):
                qualified_teachers.append(teacher_name)
    
    return qualified_teachers


def find_alternate_room(slot, timetable, context):
    """
    Find an available alternate room for this slot.
    
    Returns:
        List of available room names
    """
    branch_data = context.get('branchData', {})
    slot_type = slot.get('type', 'Lecture')
    day = slot.get('day')
    slot_index = slot.get('slot')
    
    # Get appropriate room list
    if slot_type == 'Practical':
        rooms = branch_data.get('labs', [])
    else:
        rooms = branch_data.get('rooms', [])
    
    # Find available rooms
    available_rooms = []
    
    for room in rooms:
        if _is_room_available(room, day, slot_index, timetable):
            available_rooms.append(room)
    
    return available_rooms


def _try_alternate_teacher(slot, timetable, context):
    """Try to find an alternate teacher"""
    alternates = find_alternate_teacher(slot, timetable, context)
    
    if alternates:
        # Suggest first available teacher
        new_teacher = alternates[0]
        fixed_slot = {**slot, 'teacher': new_teacher}
        
        # Validate the fix
        engine = ConstraintEngine()
        temp_timetable = [
            fixed_slot if s.get('id') == slot.get('id') else s
            for s in timetable
        ]
        
        validation = engine.validate_timetable(temp_timetable, context)
        
        if validation['valid']:
            return {
                "fix": fixed_slot,
                "explanation": f"Changed teacher to '{new_teacher}' (available at this time)",
                "strategy": "alternate_teacher"
            }
    
    return {
        "fix": None,
        "explanation": "No available teachers found for this subject and time",
        "strategy": "alternate_teacher"
    }


def _try_alternate_room(slot, timetable, context):
    """Try to find an alternate room"""
    alternates = find_alternate_room(slot, timetable, context)
    
    if alternates:
        # Suggest first available room
        new_room = alternates[0]
        fixed_slot = {**slot, 'room': new_room}
        
        # Validate the fix
        engine = ConstraintEngine()
        temp_timetable = [
            fixed_slot if s.get('id') == slot.get('id') else s
            for s in timetable
        ]
        
        validation = engine.validate_timetable(temp_timetable, context)
        
        if validation['valid']:
            return {
                "fix": fixed_slot,
                "explanation": f"Changed room to '{new_room}' (available at this time)",
                "strategy": "alternate_room"
            }
    
    return {
        "fix": None,
        "explanation": "No available rooms found for this time",
        "strategy": "alternate_room"
    }


def _is_teacher_available(teacher, day, slot_index, timetable):
    """Check if teacher is free at given time"""
    for slot in timetable:
        if (slot.get('teacher') == teacher and
            slot.get('day') == day and
            slot.get('slot') == slot_index):
            return False
    return True


def _is_room_available(room, day, slot_index, timetable):
    """Check if room is free at given time"""
    for slot in timetable:
        if (slot.get('room') == room and
            slot.get('day') == day and
            slot.get('slot') == slot_index):
            return False
    return True
