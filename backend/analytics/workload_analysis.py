"""
Teacher Workload Analysis

Analyzes teacher workload distribution and identifies overload/underutilization.
"""

from collections import defaultdict


def compute_teacher_workload(timetable, context):
    """
    Calculate teacher workload metrics.
    
    Args:
        timetable: List of slot dictionaries
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "perTeacher": {
                "teacherName": {
                    "totalLectures": int,
                    "lecturesPerDay": {"Monday": int, ...},
                    "peakDay": {"day": str, "count": int},
                    "idleDays": [str],
                    "classification": "balanced" | "slight_overload" | "heavy_overload"
                }
            },
            "averageLectures": float,
            "mostOverloaded": {"teacher": str, "count": int},
            "leastUtilized": {"teacher": str, "count": int}
        }
    """
    smart_input = context.get('smartInputData', {})
    branch_data = context.get('branchData', {})
    teachers = smart_input.get('teachers', [])
    working_days = branch_data.get('workingDays', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
    
    # Track lectures per teacher per day
    # Key: Normalized Name (lowercase, stripped) -> Day -> Count
    teacher_daily_lectures_norm = defaultdict(lambda: defaultdict(int))
    teacher_total_lectures_norm = defaultdict(int)
    
    # Also track original name for display if needed, but we rely on 'teachers' list for display names
    
    print(f"DEBUG: Computing Workload for {len(timetable)} slots")
    
    for slot in timetable:
        raw_teacher = slot.get('teacher')
        day = slot.get('day')
        
        # Normalize: Strip & Lowercase
        if raw_teacher and raw_teacher != 'TBA' and day:
            norm_name = raw_teacher.strip().lower()
            teacher_daily_lectures_norm[norm_name][day] += 1
            teacher_total_lectures_norm[norm_name] += 1
            
    # Calculate metrics for each teacher
    per_teacher_metrics = {}
    total_lectures_all = 0
    teacher_count = len(teachers)
    
    print(f"DEBUG: Found {len(teacher_total_lectures_norm)} teachers in timetable.")
    
    for teacher_data in teachers:
        raw_name = teacher_data.get('name')
        if not raw_name: continue
        
        # Display Name (Original)
        display_name = raw_name.strip()
        teacher_name = display_name # Alias for compatibility
        
        # Lookup Key (Normalized)
        norm_key = display_name.lower()
        
        total = teacher_total_lectures_norm.get(norm_key, 0)
        
        if total == 0 and teacher_total_lectures_norm:
             # Debugging mismatch - check if this teacher exists in map with slightly different chars?
             # For now just log
             # print(f"DEBUG: Teacher {display_name} has 0 lectures. (Key: {norm_key})")
             pass
             
        total_lectures_all += total
        
        daily_lectures = dict(teacher_daily_lectures_norm.get(norm_key, {}))
        
        # Re-map daily lectures to Capitalized Days if needed? 
        # The days come from timetable, so they should be "Monday", etc.
        # But let's trust the keys from timetable.
        
        # Find peak day
        peak_day = None
        peak_count = 0
        for day in working_days:
            count = daily_lectures.get(day, 0)
            if count > peak_count:
                peak_count = count
                peak_day = day
        
        # Find idle days
        idle_days = [day for day in working_days if daily_lectures.get(day, 0) == 0]
        
        # Classify workload
        classification = classify_workload(peak_count, total, len(working_days))
        
        per_teacher_metrics[teacher_name] = {
            "totalLectures": total,
            "lecturesPerDay": {day: daily_lectures.get(day, 0) for day in working_days},
            "peakDay": {"day": peak_day, "count": peak_count} if peak_day else None,
            "idleDays": idle_days,
            "classification": classification
        }
    
    # Calculate average
    avg_lectures = total_lectures_all / teacher_count if teacher_count > 0 else 0
    
    # Find most overloaded and least utilized
    most_overloaded = None
    least_utilized = None
    max_load = -1
    min_load = float('inf')
    
    for teacher_name, metrics in per_teacher_metrics.items():
        total = metrics['totalLectures']
        if total > max_load:
            max_load = total
            most_overloaded = {"teacher": teacher_name, "count": total}
        if total < min_load:
            min_load = total
            least_utilized = {"teacher": teacher_name, "count": total}
    
    return {
        "perTeacher": per_teacher_metrics,
        "averageLectures": round(avg_lectures, 1),
        "mostOverloaded": most_overloaded,
        "leastUtilized": least_utilized
    }


def classify_workload(peak_day_count, total_lectures, num_days):
    """
    Classify teacher workload based on peak day and total weekly load.
    
    Args:
        peak_day_count: Maximum lectures in any single day
        total_lectures: Total weekly lectures
        num_days: Number of working days
    
    Returns:
        "balanced" | "slight_overload" | "heavy_overload"
    """
    avg_per_day = total_lectures / num_days if num_days > 0 else 0
    
    # Heavy overload: peak day > 7 lectures OR 40% above average
    if peak_day_count > 7 or (avg_per_day > 0 and peak_day_count > avg_per_day * 1.4):
        return "heavy_overload"
    
    # Slight overload: peak day > 5 lectures OR 20% above average
    if peak_day_count > 5 or (avg_per_day > 0 and peak_day_count > avg_per_day * 1.2):
        return "slight_overload"
    
    return "balanced"


def generate_workload_insights(workload_metrics):
    """
    Generate human-readable insights from workload metrics.
    
    Args:
        workload_metrics: Output from compute_teacher_workload
    
    Returns:
        List of insight strings
    """
    insights = []
    per_teacher = workload_metrics.get('perTeacher', {})
    
    # Check for overloaded teachers
    for teacher_name, metrics in per_teacher.items():
        classification = metrics.get('classification')
        peak = metrics.get('peakDay')
        
        if classification == 'heavy_overload' and peak:
            insights.append(f"⚠️ Teacher {teacher_name} has {peak['count']} lectures on {peak['day']} (heavy overload)")
        elif classification == 'slight_overload' and peak:
            insights.append(f"⚡ Teacher {teacher_name} has {peak['count']} lectures on {peak['day']} (slight overload)")
    
    # Check for underutilized teachers
    for teacher_name, metrics in per_teacher.items():
        total = metrics.get('totalLectures', 0)
        idle_days = metrics.get('idleDays', [])
        
        if total == 0:
            insights.append(f"ℹ️ Teacher {teacher_name} has no assigned lectures (completely unused)")
        elif len(idle_days) >= 3:
            insights.append(f"ℹ️ Teacher {teacher_name} has {len(idle_days)} idle days (under-utilized)")
    
    # Overall distribution
    most_overloaded = workload_metrics.get('mostOverloaded')
    least_utilized = workload_metrics.get('leastUtilized')
    avg = workload_metrics.get('averageLectures', 0)
    
    if most_overloaded and least_utilized:
        if most_overloaded['count'] - least_utilized['count'] > avg * 0.5:
            insights.append(f"📊 Workload distribution is uneven (range: {least_utilized['count']} to {most_overloaded['count']} lectures)")
    
    if not insights:
        insights.append("✅ Teacher workload is well-balanced across all faculty")
    
    return insights
