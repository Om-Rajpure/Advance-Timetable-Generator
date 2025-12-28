"""
Lab Usage Analysis

Analyzes lab utilization patterns and generates usage heatmaps.
"""

from collections import defaultdict


def compute_lab_heatmap(timetable, context):
    """
    Generate lab usage heatmap data.
    
    Args:
        timetable: List of slot dictionaries
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "perLab": {
                "labName": {
                    "heatmap": {"Monday": {"9:00-10:00": 1.0, ...}, ...},
                    "utilizationPercent": float,
                    "peakHours": [{"day": str, "time": str, "subjects": [str]}],
                    "idleSlots": int
                }
            },
            "overallUtilization": float,
            "mostUsedLab": {"lab": str, "percent": float},
            "leastUsedLab": {"lab": str, "percent": float}
        }
    """
    branch_data = context.get('branchData', {})
    labs = branch_data.get('labs', [])
    working_days = branch_data.get('workingDays', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
    time_slots = branch_data.get('timeSlots', [])
    
    # If time slots not in branch data, create default
    if not time_slots:
        time_slots = [
            "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00",
            "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"
        ]
    
    # Initialize heatmap structure
    lab_heatmaps = {}
    lab_usage_count = defaultdict(int)
    lab_slot_subjects = defaultdict(list)
    
    for lab in labs:
        lab_name = lab if isinstance(lab, str) else lab.get('name', lab)
        lab_heatmaps[lab_name] = {
            day: {time: 0.0 for time in time_slots}
            for day in working_days
        }
    
    # Populate heatmap from timetable
    for slot in timetable:
        if slot.get('type') == 'Practical':
            lab = slot.get('room') or slot.get('lab')
            day = slot.get('day')
            time = slot.get('time')
            subject = slot.get('subject', 'Unknown')
            
            if lab and day and time and lab in lab_heatmaps:
                lab_heatmaps[lab][day][time] = 1.0  # Fully occupied
                lab_usage_count[lab] += 1
                lab_slot_subjects[(lab, day, time)].append(subject)
    
    # Calculate metrics per lab
    per_lab_metrics = {}
    total_slots = len(working_days) * len(time_slots)
    overall_used_slots = 0
    
    for lab_name, heatmap in lab_heatmaps.items():
        used_slots = lab_usage_count.get(lab_name, 0)
        overall_used_slots += used_slots
        utilization = (used_slots / total_slots * 100) if total_slots > 0 else 0
        idle_slots = total_slots - used_slots
        
        # Find peak hours (fully occupied slots)
        peak_hours = []
        for day in working_days:
            for time_slot in time_slots:
                if heatmap[day][time_slot] == 1.0:
                    subjects = lab_slot_subjects.get((lab_name, day, time_slot), [])
                    peak_hours.append({
                        "day": day,
                        "time": time_slot,
                        "subjects": subjects
                    })
        
        per_lab_metrics[lab_name] = {
            "heatmap": heatmap,
            "utilizationPercent": round(utilization, 1),
            "peakHours": peak_hours[:10],  # Limit to top 10
            "idleSlots": idle_slots
        }
    
    # Overall metrics
    total_capacity = len(labs) * total_slots if labs else 1
    overall_utilization = (overall_used_slots / total_capacity * 100) if total_capacity > 0 else 0
    
    # Find most and least used labs
    most_used = None
    least_used = None
    max_util = -1
    min_util = float('inf')
    
    for lab_name, metrics in per_lab_metrics.items():
        util = metrics['utilizationPercent']
        if util > max_util:
            max_util = util
            most_used = {"lab": lab_name, "percent": util}
        if util < min_util:
            min_util = util
            least_used = {"lab": lab_name, "percent": util}
    
    return {
        "perLab": per_lab_metrics,
        "overallUtilization": round(overall_utilization, 1),
        "mostUsedLab": most_used,
        "leastUsedLab": least_used
    }


def analyze_lab_efficiency(lab_metrics):
    """
    Analyze lab efficiency and detect issues.
    
    Args:
        lab_metrics: Output from compute_lab_heatmap
    
    Returns:
        List of insight strings
    """
    insights = []
    per_lab = lab_metrics.get('perLab', {})
    overall_util = lab_metrics.get('overallUtilization', 0)
    
    # Check for lab congestion (>80% utilization = bottleneck risk)
    for lab_name, metrics in per_lab.items():
        util = metrics.get('utilizationPercent', 0)
        
        if util > 80:
            insights.append(f"🔴 {lab_name} is heavily utilized ({util}% - bottleneck risk)")
        elif util < 20:
            insights.append(f"🟢 {lab_name} is underutilized ({util}% - available capacity)")
    
    # Analyze peak concentration
    for lab_name, metrics in per_lab.items():
        peak_hours = metrics.get('peakHours', [])
        
        # Group peak hours by day to detect concentration
        day_counts = {}
        for peak in peak_hours:
            day = peak['day']
            day_counts[day] = day_counts.get(day, 0) + 1
        
        for day, count in day_counts.items():
            if count >= 5:  # More than 5 slots on same day
                insights.append(f"⚠️ {lab_name} is overloaded on {day} ({count} practicals scheduled)")
    
    # Overall insights
    if overall_util > 70:
        insights.append(f"📊 Labs are heavily utilized overall ({overall_util}% - consider adding capacity)")
    elif overall_util < 30:
        insights.append(f"📊 Labs have significant free capacity ({overall_util}% utilization)")
    
    if not insights:
        insights.append("✅ Lab utilization is balanced and efficient")
    
    return insights
