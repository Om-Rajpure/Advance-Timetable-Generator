"""
Edit Validation

Validates individual slot edits and timetable changes.
"""

from constraints.constraint_engine import ConstraintEngine


def validate_slot_edit(modified_slot, full_timetable, context):
    """
    Validate a single slot edit against the full timetable.
    
    Args:
        modified_slot: The edited slot dictionary
        full_timetable: Complete timetable with all slots
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "valid": bool,
            "conflicts": [...],
            "affectedSlots": [...],
            "severity": "HARD" | "SOFT" | "NONE"
        }
    """
    engine = ConstraintEngine()
    
    # Create temporary timetable with modification
    temp_timetable = []
    for slot in full_timetable:
        if slot.get('id') == modified_slot.get('id'):
            temp_timetable.append(modified_slot)
        else:
            temp_timetable.append(slot)
    
    # Validate using constraint engine
    result = engine.validate_timetable(temp_timetable, context)
    
    # Filter conflicts related to edited slot
    relevant_conflicts = _filter_relevant_conflicts(
        result.get('hardViolations', []) + result.get('softViolations', []),
        modified_slot
    )
    
    # Determine severity
    has_hard = any(c.get('severity') == 'HARD' for c in relevant_conflicts)
    has_soft = any(c.get('severity') == 'SOFT' for c in relevant_conflicts)
    
    severity = "HARD" if has_hard else ("SOFT" if has_soft else "NONE")
    
    # Extract affected slots
    affected_slots = _extract_affected_slots(relevant_conflicts, modified_slot)
    
    return {
        "valid": result['valid'],
        "conflicts": relevant_conflicts,
        "affectedSlots": affected_slots,
        "severity": severity
    }


def validate_timetable_changes(timetable, context):
    """
    Validate entire timetable after edits.
    
    Args:
        timetable: Complete timetable
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "valid": bool,
            "hardViolations": [...],
            "softViolations": [...],
            "canSave": bool
        }
    """
    engine = ConstraintEngine()
    result = engine.validate_timetable(timetable, context)
    
    return {
        "valid": result['valid'],
        "hardViolations": result.get('hardViolations', []),
        "softViolations": result.get('softViolations', []),
        "canSave": result['valid']  # Can only save if no hard violations
    }


def _filter_relevant_conflicts(all_conflicts, edited_slot):
    """Filter conflicts that involve the edited slot"""
    relevant = []
    
    for conflict in all_conflicts:
        # Check if conflict involves this slot
        affected_entities = conflict.get('affectedEntities', {})
        
        # Check if day/slot/year/division match
        if (conflict.get('day') == edited_slot.get('day') and
            conflict.get('slot') == edited_slot.get('slot')):
            relevant.append(conflict)
        
        # Check if teacher/room match
        elif (affected_entities.get('teacher') == edited_slot.get('teacher') or
              affected_entities.get('room') == edited_slot.get('room')):
            relevant.append(conflict)
    
    return relevant


def _extract_affected_slots(conflicts, edited_slot):
    """Extract list of affected slot IDs from conflicts"""
    affected = set()
    
    for conflict in conflicts:
        # Add slots mentioned in conflict
        if 'affectedSlots' in conflict:
            for slot_ref in conflict['affectedSlots']:
                if isinstance(slot_ref, str):
                    affected.add(slot_ref)
        
        # Add from affected entities
        affected_entities = conflict.get('affectedEntities', {})
        if 'slots' in affected_entities:
            affected.update(affected_entities['slots'])
    
    # Always include the edited slot
    affected.add(edited_slot.get('id'))
    
    return list(affected)
