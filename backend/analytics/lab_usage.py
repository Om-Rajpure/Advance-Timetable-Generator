"""
Lab/Room Usage Analysis

Analyzes lab and classroom utilization patterns and generates usage heatmaps.
"""

from collections import defaultdict


def compute_room_heatmap(timetable, context, room_type='LAB'):
    """
    Generic function to generate room usage heatmap.
    
    Args:
        timetable: List of slot dictionaries
        context: Dictionary with branchData and smartInputData
        room_type: 'LAB' (Practical) or 'CLASSROOM' (Theory)
        
    Returns:
        Similar structure to original compute_lab_heatmap
    """
    branch_data = context.get('branchData', {})
    working_days = branch_data.get('workingDays', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
    time_slots = branch_data.get('timeSlots', [])
    
    # Identify target rooms
    if room_type == 'LAB':
        target_rooms = branch_data.get('labs', [])
        # Labs might be sharedLabs objects or strings
        room_names = [r if isinstance(r, str) else r.get('name') for r in target_rooms]
    else:
        # For classrooms, check 'classrooms' list, fall back to 'rooms'
        classrooms = branch_data.get('classrooms', [])
        if not classrooms:
            classrooms = branch_data.get('rooms', [])
        room_names = [r if isinstance(r, str) else r.get('name') for r in classrooms]
        
    # If no rooms defined, we can't map utilization accurately
    if not room_names:
        # Try to infer from usage if no config exists?
        # For now, return empty result to avoid crash
        pass

    # If time slots not in branch data, create default
    if not time_slots:
        time_slots = [
            "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00",
            "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
        ]
    
    # Initialize heatmap structure
    room_heatmaps = {}
    room_usage_count = defaultdict(int)
    room_slot_subjects = defaultdict(list)
    
    # Safe init for defined rooms
    for r_name in room_names:
        if r_name:
            room_heatmaps[r_name] = {
                day: {time: 0.0 for time in time_slots}
                for day in working_days
            }
    
    # Populate heatmap from timetable
    for slot in timetable:
        # Determine if this slot matches our target type
        s_type = slot.get('type', 'THEORY').upper()
        is_match = False
        
        if room_type == 'LAB':
            # Match LAB, Practical, PRACTICAL
            if s_type in ['LAB', 'PRACTICAL', 'PRACTICALS']:
                is_match = True
        else:
            # Match THEORY, LECTURE
            if s_type in ['THEORY', 'LECTURE']:
                is_match = True
        
        if is_match:
            # Room can be under 'room' or 'lab' key
            r_name = slot.get('room') or slot.get('lab')
            day = slot.get('day')
            time = slot.get('time')
            
            # FALLBACK: If 'time' string is missing, try to map from 'slot' index
            if not time and 'slot' in slot:
                try:
                    # Scheduler uses 1-based indexing
                    slot_idx = int(slot['slot']) - 1
                    if 0 <= slot_idx < len(time_slots):
                        time = time_slots[slot_idx]
                except (ValueError, TypeError, IndexError):
                    pass
            
            subject = slot.get('subject', 'Unknown')
            
            # If room wasn't pre-defined, add it dynamically (robustness)
            # FILTER: Do not add if it matches an Academic Year (Ghost Room Fix)
            # Robust filtering for "SE", "TE", "BE", "SE-A", etc.
            academic_years = branch_data.get('academicYears', [])
            
            # Normalize for comparison
            bad_names = set([y.upper().strip() for y in academic_years])
            bad_names.update(["YEAR", "PART", "DIV"])
            
            clean_name = str(r_name).strip().upper()
            
            # 1. Exact match with Year (e.g. "SE")
            is_ghost = clean_name in bad_names
            
            # 2. Starts with Year + Hyphen/Space (e.g. "SE-A", "SE A") - heuristic
            # BUT: "SE-Classroom" might be valid? No, usually not.
            # If length is short (< 4), it's likely just "SE" or "SE A"
            if len(clean_name) < 5 and any(clean_name.startswith(y) for y in bad_names):
                is_ghost = True

            if r_name and r_name not in room_heatmaps:
                if not is_ghost:
                    room_names.append(r_name)
                    room_heatmaps[r_name] = {
                        day: {time: 0.0 for time in time_slots}
                        for day in working_days
                    }
            
            if r_name and day and time and r_name in room_heatmaps:
                # Handle time slot matching (exact string match required)
                if day in room_heatmaps[r_name] and time in room_heatmaps[r_name][day]:
                    room_heatmaps[r_name][day][time] = 1.0
                    room_usage_count[r_name] += 1
                    room_slot_subjects[(r_name, day, time)].append(subject)

    # Calculate metrics
    per_room_metrics = {}
    total_slots = len(working_days) * len(time_slots)
    overall_used_slots = 0
    
    for r_name, heatmap in room_heatmaps.items():
        used_slots = room_usage_count.get(r_name, 0)
        overall_used_slots += used_slots
        utilization = (used_slots / total_slots * 100) if total_slots > 0 else 0
        idle_slots = total_slots - used_slots
        
        peak_hours = []
        for day in working_days:
            for time_slot in time_slots:
                if heatmap[day][time_slot] == 1.0:
                    subjects = room_slot_subjects.get((r_name, day, time_slot), [])
                    peak_hours.append({
                        "day": day,
                        "time": time_slot,
                        "subjects": subjects
                    })
        
        per_room_metrics[r_name] = {
            "heatmap": heatmap,
            "utilizationPercent": round(utilization, 1),
            "peakHours": peak_hours[:10],
            "idleSlots": idle_slots
        }
    
    # Overall metrics
    total_capacity = len(room_names) * total_slots if room_names else 1
    overall_utilization = (overall_used_slots / total_capacity * 100) if total_capacity > 0 else 0
    
    most_used = None
    least_used = None
    max_util = -1
    min_util = float('inf')
    
    for r_name, metrics in per_room_metrics.items():
        util = metrics['utilizationPercent']
        if util > max_util:
            max_util = util
            most_used = {"room": r_name, "percent": util}
        if util < min_util:
            min_util = util
            least_used = {"room": r_name, "percent": util}
            
    return {
        "perLab": per_room_metrics, # Keeping key 'perLab' for frontend compat if needed, or we can change
        "perRoom": per_room_metrics, # New generic key
        "overallUtilization": round(overall_utilization, 1),
        "mostUsed": most_used,
        "leastUsed": least_used
    }

def compute_lab_heatmap(timetable, context):
    """Wrapper for Lab Analytics"""
    result = compute_room_heatmap(timetable, context, room_type='LAB')
    # Map generic keys to specific 'Lab' keys for backward compatibility
    return {
        "perLab": result['perRoom'],
        "overallUtilization": result['overallUtilization'],
        "mostUsedLab": result['mostUsed'] and {"lab": result['mostUsed']['room'], "percent": result['mostUsed']['percent']},
        "leastUsedLab": result['leastUsed'] and {"lab": result['leastUsed']['room'], "percent": result['leastUsed']['percent']}
    }

def compute_classroom_heatmap(timetable, context):
    """Wrapper for Classroom Analytics"""
    result = compute_room_heatmap(timetable, context, room_type='CLASSROOM')
    return {
        "perClassroom": result['perRoom'],
        "overallUtilization": result['overallUtilization'],
        "mostUsedClassroom": result['mostUsed'] and {"classroom": result['mostUsed']['room'], "percent": result['mostUsed']['percent']},
        "leastUsedClassroom": result['leastUsed'] and {"classroom": result['leastUsed']['room'], "percent": result['leastUsed']['percent']}
    }

def analyze_lab_efficiency(lab_metrics):
    """Analyze lab efficiency."""
    insights = []
    per_lab = lab_metrics.get('perLab', {})
    overall_util = lab_metrics.get('overallUtilization', 0)
    
    for lab_name, metrics in per_lab.items():
        util = metrics.get('utilizationPercent', 0)
        if util > 80:
            insights.append(f"🔴 {lab_name} is heavily utilized ({util}% - bottleneck risk)")
        elif util < 20:
            insights.append(f"🟢 {lab_name} is underutilized ({util}% - available capacity)")
            
    if overall_util > 70:
        insights.append(f"📊 Labs are heavily utilized overall ({overall_util}% - consider adding capacity)")
    elif overall_util < 30:
        insights.append(f"📊 Labs have significant free capacity ({overall_util}% utilization)")
        
    if not insights:
        insights.append("✅ Lab utilization is balanced and efficient")
        
    return insights

def analyze_classroom_efficiency(classroom_metrics):
    """Analyze classroom efficiency."""
    insights = []
    per_room = classroom_metrics.get('perClassroom', {})
    overall_util = classroom_metrics.get('overallUtilization', 0)
    
    for r_name, metrics in per_room.items():
        util = metrics.get('utilizationPercent', 0)
        if util > 90:
            insights.append(f"🔴 {r_name} is critical ({util}% utilized)")
        elif util < 30:
            insights.append(f"🟢 {r_name} usually empty ({util}% utilized)")

    if overall_util > 85:
         insights.append(f"📊 Classrooms are very busy ({overall_util}% utilization)")
    
    if not insights:
        insights.append("✅ Classroom usage looks good")
        
    return insights
