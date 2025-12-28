"""
Simulation Report Generator

Generates detailed before/after comparison reports for simulations.
"""

from validation.scorer import QualityScorer
from constraints.constraint_engine import ConstraintEngine


def generate_simulation_report(original_timetable, simulated_timetable, context, simulation_result):
    """
    Generate comprehensive simulation comparison report.
    
    Args:
        original_timetable: Original timetable before simulation
        simulated_timetable: Simulated timetable after changes
        context: Context dictionary
        simulation_result: Base result from scenario handler
        
    Returns:
        {
            "feasible": bool,
            "affectedSlots": [...],
            "newAssignments": [...],
            "conflicts": {
                "hardViolations": [...],
                "softViolations": [...]
            },
            "qualityComparison": {
                "before": {...},
                "after": {...},
                "delta": float
            },
            "resourceComparison": {
                "teacherUtilization": {...},
                "labUtilization": {...}
            },
            "summary": str,
            "recommendations": [...]
        }
    """
    # Initialize engines
    constraint_engine = ConstraintEngine()
    scorer = QualityScorer(context)
    
    # Validate both timetables
    original_validation = constraint_engine.validate_timetable(original_timetable, context)
    simulated_validation = constraint_engine.validate_timetable(simulated_timetable, context)
    
    # Compute quality scores
    original_score_result = scorer.compute_score(original_timetable)
    simulated_score_result = scorer.compute_score(simulated_timetable)
    
    # Calculate delta
    score_delta = simulated_score_result['score'] - original_score_result['score']
    
    # Build quality comparison
    quality_comparison = {
        "before": {
            "score": original_score_result['score'],
            "grade": original_score_result['grade'],
            "breakdown": original_score_result['breakdown']
        },
        "after": {
            "score": simulated_score_result['score'],
            "grade": simulated_score_result['grade'],
            "breakdown": simulated_score_result['breakdown']
        },
        "delta": score_delta,
        "deltaPercent": (score_delta / original_score_result['score'] * 100) if original_score_result['score'] > 0 else 0
    }
    
    # Build conflict summary
    conflicts = {
        "hardViolations": simulated_validation.get('hardViolations', []),
        "softViolations": simulated_validation.get('softViolations', []),
        "newHardViolations": [
            v for v in simulated_validation.get('hardViolations', [])
            if v not in original_validation.get('hardViolations', [])
        ],
        "newSoftViolations": [
            v for v in simulated_validation.get('softViolations', [])
            if v not in original_validation.get('softViolations', [])
        ]
    }
    
    # Resource utilization comparison
    resource_comparison = _compute_resource_comparison(
        original_timetable,
        simulated_timetable,
        context
    )
    
    # Generate recommendations
    recommendations = _generate_recommendations(
        quality_comparison,
        conflicts,
        resource_comparison,
        simulation_result
    )
    
    # Build comprehensive report
    report = {
        "feasible": simulation_result.get('feasible', True) and simulated_validation['valid'],
        "affectedSlots": simulation_result.get('affectedSlots', []),
        "newAssignments": simulation_result.get('reassignedSlots', []),
        "conflicts": conflicts,
        "qualityComparison": quality_comparison,
        "resourceComparison": resource_comparison,
        "summary": simulation_result.get('summary', 'Simulation completed'),
        "recommendations": recommendations,
        "scenarioType": simulation_result.get('scenarioType'),
        "scenarioParams": simulation_result.get('scenarioParams'),
        "timestamp": None  # Could add timestamp if needed
    }
    
    return report


def _compute_resource_comparison(original_timetable, simulated_timetable, context):
    """
    Compare resource utilization between original and simulated timetables.
    """
    # Teacher utilization
    original_teacher_util = _calculate_teacher_utilization(original_timetable, context)
    simulated_teacher_util = _calculate_teacher_utilization(simulated_timetable, context)
    
    # Lab utilization
    original_lab_util = _calculate_lab_utilization(original_timetable, context)
    simulated_lab_util = _calculate_lab_utilization(simulated_timetable, context)
    
    return {
        "teacherUtilization": {
            "before": f"{original_teacher_util:.1f}%",
            "after": f"{simulated_teacher_util:.1f}%",
            "delta": simulated_teacher_util - original_teacher_util
        },
        "labUtilization": {
            "before": f"{original_lab_util:.1f}%",
            "after": f"{simulated_lab_util:.1f}%",
            "delta": simulated_lab_util - original_lab_util
        }
    }


def _calculate_teacher_utilization(timetable, context):
    """Calculate average teacher utilization percentage."""
    if not timetable:
        return 0.0
    
    smart_input = context.get('smartInputData', {})
    teachers = smart_input.get('teachers', [])
    
    if not teachers:
        return 0.0
    
    # Count slots per teacher
    teacher_slots = {}
    for slot in timetable:
        teacher = slot.get('teacher')
        if teacher and teacher != 'TBA':
            teacher_slots[teacher] = teacher_slots.get(teacher, 0) + 1
    
    # Calculate average
    branch_data = context.get('branchData', {})
    working_days = branch_data.get('workingDays', [])
    slots_per_day = branch_data.get('slotsPerDay', 6)
    total_slots_available = len(working_days) * slots_per_day
    
    utilization_percentages = [
        (count / total_slots_available * 100) for count in teacher_slots.values()
    ]
    
    return sum(utilization_percentages) / len(teachers) if teachers else 0.0


def _calculate_lab_utilization(timetable, context):
    """Calculate lab utilization percentage."""
    if not timetable:
        return 0.0
    
    branch_data = context.get('branchData', {})
    labs = branch_data.get('labs', [])
    
    if not labs:
        return 0.0
    
    # Count practical slots using labs
    lab_slots = {}
    for slot in timetable:
        if slot.get('type') == 'Practical':
            lab = slot.get('room')
            if lab and lab != 'TBA':
                lab_slots[lab] = lab_slots.get(lab, 0) + 1
    
    # Calculate average
    working_days = branch_data.get('workingDays', [])
    slots_per_day = branch_data.get('slotsPerDay', 6)
    total_slots_available = len(working_days) * slots_per_day
    
    utilization_percentages = [
        (count / total_slots_available * 100) for count in lab_slots.values()
    ]
    
    return sum(utilization_percentages) / len(labs) if labs else 0.0


def _generate_recommendations(quality_comparison, conflicts, resource_comparison, simulation_result):
    """
    Generate actionable recommendations based on simulation results.
    """
    recommendations = []
    
    # Quality score recommendations
    delta = quality_comparison['delta']
    if delta < -10:
        recommendations.append({
            "type": "warning",
            "message": f"Quality score dropped significantly ({delta:.1f} points). Consider alternative approaches.",
            "priority": "high"
        })
    elif delta < -5:
        recommendations.append({
            "type": "caution",
            "message": f"Quality score decreased slightly ({delta:.1f} points). Review before applying.",
            "priority": "medium"
        })
    elif delta > 0:
        recommendations.append({
            "type": "positive",
            "message": f"Quality score improved ({delta:+.1f} points).",
            "priority": "low"
        })
    
    # Hard violation recommendations
    if conflicts['newHardViolations']:
        recommendations.append({
            "type": "error",
            "message": f"{len(conflicts['newHardViolations'])} new hard constraint violation(s) detected. This simulation is NOT VALID.",
            "priority": "critical"
        })
    
    # Resource utilization recommendations
    teacher_util_delta = resource_comparison['teacherUtilization']['delta']
    if teacher_util_delta > 20:
        recommendations.append({
            "type": "warning",
            "message": f"Teacher utilization increased by {teacher_util_delta:.1f}%. Teachers may be overloaded.",
            "priority": "high"
        })
    
    lab_util_delta = resource_comparison['labUtilization']['delta']
    if lab_util_delta > 20:
        recommendations.append({
            "type": "warning",
            "message": f"Lab utilization increased by {lab_util_delta:.1f}%. Labs may be overcrowded.",
            "priority": "high"
        })
    
    # Scenario-specific recommendations
    scenario_type = simulation_result.get('scenarioType')
    if scenario_type == 'TEACHER_UNAVAILABLE':
        if simulation_result.get('feasible'):
            recommendations.append({
                "type": "info",
                "message": "Teacher reassignment successful. Review affected slots for quality.",
                "priority": "medium"
            })
    
    elif scenario_type == 'LAB_UNAVAILABLE':
        if not simulation_result.get('feasible'):
            recommendations.append({
                "type": "error",
                "message": "Lab removal is NOT FEASIBLE with current resources. Add more labs or reduce practicals.",
                "priority": "critical"
            })
    
    elif scenario_type == 'DAYS_REDUCED':
        warnings = simulation_result.get('warnings', [])
        if warnings:
            recommendations.append({
                "type": "warning",
                "message": warnings[0],
                "priority": "high"
            })
    
    # Fallback recommendation
    if not recommendations:
        recommendations.append({
            "type": "info",
            "message": "Simulation completed successfully. Review changes before applying.",
            "priority": "low"
        })
    
    return recommendations
