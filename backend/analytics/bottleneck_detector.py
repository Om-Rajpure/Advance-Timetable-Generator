"""
Bottleneck Detection

Identifies structural problems and constraints in timetable scheduling.
"""

from collections import defaultdict


def detect_bottlenecks(timetable, context):
    """
    Detect scheduling bottlenecks and structural issues.
    
    Args:
        timetable: List of slot dictionaries
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "issues": [
                {
                    "type": "teacher_overload" | "lab_shortage" | "student_overload" | "uneven_distribution",
                    "severity": "critical" | "warning" | "info",
                    "title": str,
                    "description": str,
                    "affectedEntities": [str]
                }
            ],
            "criticalCount": int,
            "warningCount": int,
            "infoCount": int
        }
    """
    issues = []
    
    # Detect teacher overload
    teacher_issues = _detect_teacher_overload(timetable, context)
    issues.extend(teacher_issues)
    
    # Detect lab shortages
    lab_issues = _detect_lab_shortage(timetable, context)
    issues.extend(lab_issues)
    
    # Detect student overload
    student_issues = _detect_student_overload(timetable, context)
    issues.extend(student_issues)
    
    # Detect uneven distribution
    distribution_issues = _detect_uneven_distribution(timetable, context)
    issues.extend(distribution_issues)
    
    # Count by severity
    critical_count = sum(1 for issue in issues if issue['severity'] == 'critical')
    warning_count = sum(1 for issue in issues if issue['severity'] == 'warning')
    info_count = sum(1 for issue in issues if issue['severity'] == 'info')
    
    return {
        "issues": issues,
        "criticalCount": critical_count,
        "warningCount": warning_count,
        "infoCount": info_count
    }


def _detect_teacher_overload(timetable, context):
    """Detect teachers with excessive daily workload."""
    issues = []
    teacher_daily_load = defaultdict(lambda: defaultdict(int))
    
    for slot in timetable:
        teacher = slot.get('teacher')
        day = slot.get('day')
        
        if teacher and teacher != 'TBA' and day:
            teacher_daily_load[teacher][day] += 1
    
    for teacher, daily_loads in teacher_daily_load.items():
        for day, count in daily_loads.items():
            if count > 7:
                issues.append({
                    "type": "teacher_overload",
                    "severity": "critical",
                    "title": f"Teacher {teacher} heavily overloaded on {day}",
                    "description": f"{teacher} has {count} lectures scheduled on {day}, which exceeds recommended maximum of 7 lectures per day",
                    "affectedEntities": [teacher]
                })
            elif count > 5:
                issues.append({
                    "type": "teacher_overload",
                    "severity": "warning",
                    "title": f"Teacher {teacher} has high workload on {day}",
                    "description": f"{teacher} has {count} lectures on {day}, approaching the recommended limit",
                    "affectedEntities": [teacher]
                })
    
    return issues


def _detect_lab_shortage(timetable, context):
    """Detect days with too many practicals competing for limited labs."""
    issues = []
    branch_data = context.get('branchData', {})
    labs = branch_data.get('labs', [])
    num_labs = len(labs)
    
    # Count practicals per day/time
    practical_slots = defaultdict(lambda: defaultdict(int))
    
    for slot in timetable:
        if slot.get('type') == 'Practical':
            day = slot.get('day')
            time = slot.get('time')
            if day and time:
                practical_slots[day][time] += 1
    
    # Check if practicals exceed lab capacity
    for day, time_slots in practical_slots.items():
        total_practicals_day = sum(time_slots.values())
        
        for time, count in time_slots.items():
            if count > num_labs:
                issues.append({
                    "type": "lab_shortage",
                    "severity": "critical",
                    "title": f"Lab capacity exceeded on {day} at {time}",
                    "description": f"{count} practicals scheduled but only {num_labs} labs available. This creates an impossible scheduling situation.",
                    "affectedEntities": [f"{day} {time}"]
                })
        
        # Check daily concentration
        if total_practicals_day > num_labs * 4:  # More than 4 slots worth on average
            issues.append({
                "type": "lab_shortage",
                "severity": "warning",
                "title": f"High practical density on {day}",
                "description": f"{total_practicals_day} practical slots scheduled on {day}. Labs may be heavily utilized with limited flexibility.",
                "affectedEntities": [day]
            })
    
    return issues


def _detect_student_overload(timetable, context):
    """Detect divisions with excessive daily lecture load."""
    issues = []
    division_daily_load = defaultdict(lambda: defaultdict(int))
    
    for slot in timetable:
        year = slot.get('year')
        division = slot.get('division')
        day = slot.get('day')
        
        if year and division and day:
            div_key = f"{year}-{division}"
            division_daily_load[div_key][day] += 1
    
    for division, daily_loads in division_daily_load.items():
        for day, count in daily_loads.items():
            if count > 7:
                issues.append({
                    "type": "student_overload",
                    "severity": "critical",
                    "title": f"Division {division} overloaded on {day}",
                    "description": f"{division} has {count} lectures/practicals on {day}, which may cause student fatigue",
                    "affectedEntities": [division]
                })
            elif count > 6:
                issues.append({
                    "type": "student_overload",
                    "severity": "warning",
                    "title": f"Division {division} has dense schedule on {day}",
                    "description": f"{division} has {count} classes on {day}, approaching recommended maximum",
                    "affectedEntities": [division]
                })
    
    return issues


def _detect_uneven_distribution(timetable, context):
    """Detect uneven workload distribution."""
    issues = []
    smart_input = context.get('smartInputData', {})
    teachers = smart_input.get('teachers', [])
    
    # Calculate teacher total loads
    teacher_loads = defaultdict(int)
    for slot in timetable:
        teacher = slot.get('teacher')
        if teacher and teacher != 'TBA':
            teacher_loads[teacher] += 1
    
    if len(teacher_loads) < 2:
        return issues
    
    # Calculate variance
    loads = list(teacher_loads.values())
    avg_load = sum(loads) / len(loads)
    max_load = max(loads)
    min_load = min(loads)
    
    # High variance indicates uneven distribution
    if max_load - min_load > avg_load * 0.6:
        max_teacher = max(teacher_loads.items(), key=lambda x: x[1])
        min_teacher = min(teacher_loads.items(), key=lambda x: x[1])
        
        issues.append({
            "type": "uneven_distribution",
            "severity": "warning",
            "title": "Uneven workload distribution across teachers",
            "description": f"Workload varies significantly: {max_teacher[0]} has {max_teacher[1]} lectures while {min_teacher[0]} has {min_teacher[1]} lectures",
            "affectedEntities": [max_teacher[0], min_teacher[0]]
        })
    
    return issues


def prioritize_bottlenecks(bottleneck_data):
    """
    Sort and prioritize bottlenecks by severity.
    
    Args:
        bottleneck_data: Output from detect_bottlenecks
    
    Returns:
        Sorted list of issues (critical first, then warning, then info)
    """
    issues = bottleneck_data.get('issues', [])
    
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    
    return sorted(issues, key=lambda x: severity_order.get(x['severity'], 3))
