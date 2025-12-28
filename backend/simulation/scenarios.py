"""
Scenario Handlers

Implements simulation logic for different "what-if" scenarios.
"""

from .state_cloner import clone_timetable, clone_context
from .impact_analyzer import ImpactAnalyzer
from .partial_scheduler import PartialScheduler


def simulate_teacher_unavailable(timetable, context, teacher_name, unavailable_spec):
    """
    Simulate teacher unavailability scenario.
    
    Args:
        timetable: Current timetable
        context: Current context (branchData, smartInputData)
        teacher_name: Name of unavailable teacher
        unavailable_spec: {
            "days": ["Monday", "Wednesday"],  # Optional
            "slots": [0, 1, 2],  # Optional (specific slot indices)
            "fullWeek": bool  # If true, teacher completely unavailable
        }
        
    Returns:
        {
            "success": bool,
            "originalTimetable": [...],
            "simulatedTimetable": [...],
            "affectedSlots": [...],
            "reassignedSlots": [...],
            "conflicts": [...],
            "feasible": bool,
            "summary": str
        }
    """
    # Clone state to avoid modifying original
    cloned_timetable = clone_timetable(timetable)
    cloned_context = clone_context(context)
    
    # Analyze impact
    analyzer = ImpactAnalyzer(cloned_timetable, cloned_context)
    impact = analyzer.analyze_teacher_impact(teacher_name, unavailable_spec)
    
    # Get dependent slots (e.g., practical batches)
    dependencies = analyzer.get_dependent_slots(impact['affected_slot_ids'])
    all_affected_ids = dependencies['expanded_slot_ids']
    
    # Modify context to mark teacher as unavailable
    if unavailable_spec.get('fullWeek', False):
        # Remove teacher from available teachers
        smart_input = cloned_context.get('smartInputData', {})
        teachers = smart_input.get('teachers', [])
        smart_input['teachers'] = [
            t for t in teachers if t.get('name') != teacher_name
        ]
    else:
        # Mark specific time slots as unavailable for this teacher
        # (This would require more sophisticated constraint modification)
        # For now, we'll handle this in the partial scheduler
        pass
    
    # Attempt partial re-schedule
    scheduler = PartialScheduler(cloned_context)
    reschedule_result = scheduler.reschedule_affected_slots(
        cloned_timetable,
        all_affected_ids,
        'teacher_unavailable'
    )
    
    # Build result
    return {
        "success": reschedule_result['success'],
        "originalTimetable": timetable,
        "simulatedTimetable": reschedule_result['newTimetable'],
        "affectedSlots": impact['affected_slots'],
        "reassignedSlots": reschedule_result['reassignedSlots'],
        "conflicts": reschedule_result['unresolvableConflicts'],
        "feasible": reschedule_result['success'],
        "summary": impact['impact_summary'] + ". " + reschedule_result['message'],
        "scenarioType": "TEACHER_UNAVAILABLE",
        "scenarioParams": {
            "teacherName": teacher_name,
            "unavailableSpec": unavailable_spec
        }
    }


def simulate_lab_unavailable(timetable, context, lab_name):
    """
    Simulate lab removal/unavailability scenario.
    
    Args:
        timetable: Current timetable
        context: Current context
        lab_name: Name of unavailable lab
        
    Returns:
        Simulation result dictionary (same structure as teacher scenario)
    """
    # Clone state
    cloned_timetable = clone_timetable(timetable)
    cloned_context = clone_context(context)
    
    # Analyze impact
    analyzer = ImpactAnalyzer(cloned_timetable, cloned_context)
    impact = analyzer.analyze_lab_impact(lab_name)
    
    # Check for resource bottlenecks
    bottlenecks = analyzer.get_resource_bottlenecks('lab', lab_name)
    
    # Get dependent slots
    dependencies = analyzer.get_dependent_slots(impact['affected_slot_ids'])
    all_affected_ids = dependencies['expanded_slot_ids']
    
    # Modify context to remove lab
    branch_data = cloned_context.get('branchData', {})
    labs = branch_data.get('labs', [])
    branch_data['labs'] = [lab for lab in labs if lab != lab_name]
    
    # Check feasibility before attempting
    if bottlenecks['bottlenecks']:
        # Lab removal makes schedule infeasible
        return {
            "success": False,
            "originalTimetable": timetable,
            "simulatedTimetable": cloned_timetable,  # Unchanged
            "affectedSlots": impact['affected_slots'],
            "reassignedSlots": [],
            "conflicts": bottlenecks['bottlenecks'],
            "feasible": False,
            "summary": impact['impact_summary'] + ". " + bottlenecks['warnings'][0] if bottlenecks['warnings'] else "Infeasible",
            "scenarioType": "LAB_UNAVAILABLE",
            "scenarioParams": {
                "labName": lab_name
            }
        }
    
    # Attempt partial re-schedule
    scheduler = PartialScheduler(cloned_context)
    reschedule_result = scheduler.reschedule_affected_slots(
        cloned_timetable,
        all_affected_ids,
        'lab_unavailable'
    )
    
    return {
        "success": reschedule_result['success'],
        "originalTimetable": timetable,
        "simulatedTimetable": reschedule_result['newTimetable'],
        "affectedSlots": impact['affected_slots'],
        "reassignedSlots": reschedule_result['reassignedSlots'],
        "conflicts": reschedule_result['unresolvableConflicts'],
        "feasible": reschedule_result['success'],
        "summary": impact['impact_summary'] + ". " + reschedule_result['message'],
        "scenarioType": "LAB_UNAVAILABLE",
        "scenarioParams": {
            "labName": lab_name
        }
    }


def simulate_days_reduced(timetable, context, new_working_days, new_slots_config=None):
    """
    Simulate working days reduction scenario.
    
    Args:
        timetable: Current timetable
        context: Current context
        new_working_days: List of new working days (e.g., ["Monday", "Tuesday", ...])
        new_slots_config: Optional dict with new slot configuration
        
    Returns:
        Simulation result dictionary
    """
    # Clone state
    cloned_timetable = clone_timetable(timetable)
    cloned_context = clone_context(context)
    
    # Determine removed days
    branch_data = context.get('branchData', {})
    original_days = branch_data.get('workingDays', [])
    removed_days = [day for day in original_days if day not in new_working_days]
    
    # Analyze impact
    analyzer = ImpactAnalyzer(cloned_timetable, cloned_context)
    impact = analyzer.analyze_time_restriction_impact(removed_days=removed_days)
    
    # Get dependent slots
    dependencies = analyzer.get_dependent_slots(impact['affected_slot_ids'])
    all_affected_ids = dependencies['expanded_slot_ids']
    
    # Modify context with new working days
    cloned_branch_data = cloned_context.get('branchData', {})
    cloned_branch_data['workingDays'] = new_working_days
    
    # Apply new slots config if provided
    if new_slots_config:
        cloned_branch_data['slotsPerDay'] = new_slots_config.get(
            'slotsPerDay',
            cloned_branch_data.get('slotsPerDay', 6)
        )
        # Could also update startTime, slotDuration, etc.
    
    # Attempt partial re-schedule
    scheduler = PartialScheduler(cloned_context)
    reschedule_result = scheduler.reschedule_affected_slots(
        cloned_timetable,
        all_affected_ids,
        'days_reduced'
    )
    
    # Calculate additional warnings
    warnings = []
    if len(new_working_days) < len(original_days):
        reduction_pct = ((len(original_days) - len(new_working_days)) / len(original_days)) * 100
        warnings.append(f"Working days reduced by {reduction_pct:.0f}% ({len(original_days)} → {len(new_working_days)} days)")
    
    return {
        "success": reschedule_result['success'],
        "originalTimetable": timetable,
        "simulatedTimetable": reschedule_result['newTimetable'],
        "affectedSlots": impact['affected_slots'],
        "reassignedSlots": reschedule_result['reassignedSlots'],
        "conflicts": reschedule_result['unresolvableConflicts'],
        "feasible": reschedule_result['success'],
        "summary": impact['impact_summary'] + ". " + reschedule_result['message'],
        "warnings": warnings,
        "scenarioType": "DAYS_REDUCED",
        "scenarioParams": {
            "newWorkingDays": new_working_days,
            "removedDays": removed_days,
            "newSlotsConfig": new_slots_config
        }
    }
