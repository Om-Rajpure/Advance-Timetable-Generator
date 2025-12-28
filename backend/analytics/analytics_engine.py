"""
Analytics Engine

Main orchestrator for all analytics modules and quality scoring.
"""

from .workload_analysis import compute_teacher_workload, generate_workload_insights
from .lab_usage import compute_lab_heatmap, analyze_lab_efficiency
from .free_slots import find_free_slots, analyze_free_capacity
from .bottleneck_detector import detect_bottlenecks, prioritize_bottlenecks


def generate_full_analytics(timetable, context):
    """
    Generate complete analytics report for a timetable.
    
    Args:
        timetable: List of slot dictionaries
        context: Dictionary with branchData and smartInputData
    
    Returns:
        {
            "workload": {...},
            "labUsage": {...},
            "freeSlots": {...},
            "bottlenecks": {...},
            "summary": {
                "qualityScore": int,
                "grade": str,
                "topIssues": [str],
                "topStrengths": [str]
            }
        }
    """
    # Compute all metrics
    workload = compute_teacher_workload(timetable, context)
    lab_usage = compute_lab_heatmap(timetable, context)
    free_slots = find_free_slots(timetable, context)
    bottlenecks = detect_bottlenecks(timetable, context)
    
    # Generate insights
    workload_insights = generate_workload_insights(workload)
    lab_insights = analyze_lab_efficiency(lab_usage)
    free_insights = analyze_free_capacity(free_slots)
    prioritized_bottlenecks = prioritize_bottlenecks(bottlenecks)
    
    # Compute quality score
    quality_score = compute_quality_score({
        "workload": workload,
        "labUsage": lab_usage,
        "freeSlots": free_slots,
        "bottlenecks": bottlenecks
    })
    
    # Extract top insights
    top_issues, top_strengths = extract_top_insights({
        "workload_insights": workload_insights,
        "lab_insights": lab_insights,
        "free_insights": free_insights,
        "bottlenecks": prioritized_bottlenecks,
        "quality_score": quality_score
    })
    
    return {
        "workload": {
            "metrics": workload,
            "insights": workload_insights
        },
        "labUsage": {
            "metrics": lab_usage,
            "insights": lab_insights
        },
        "freeSlots": {
            "metrics": free_slots,
            "insights": free_insights
        },
        "bottlenecks": {
            "issues": prioritized_bottlenecks,
            "counts": {
                "critical": bottlenecks.get('criticalCount', 0),
                "warning": bottlenecks.get('warningCount', 0),
                "info": bottlenecks.get('infoCount', 0)
            }
        },
        "summary": {
            "qualityScore": quality_score['score'],
            "grade": quality_score['grade'],
            "stars": quality_score['stars'],
            "topIssues": top_issues,
            "topStrengths": top_strengths
        }
    }


def compute_quality_score(analytics):
    """
    Compute overall timetable quality score (0-100).
    
    Formula:
        Score = (load_balance × 0.4) + (resource_efficiency × 0.3) + (bottleneck_penalty × 0.3)
    
    Args:
        analytics: Dictionary with workload, labUsage, freeSlots, bottlenecks
    
    Returns:
        {
            "score": int (0-100),
            "grade": str ("EXCELLENT" | "GOOD" | "FAIR" | "POOR" | "CRITICAL"),
            "stars": int (1-5),
            "breakdown": {
                "loadBalance": int,
                "resourceEfficiency": int,
                "bottleneckPenalty": int
            }
        }
    """
    workload = analytics.get('workload', {})
    lab_usage = analytics.get('labUsage', {})
    free_slots = analytics.get('freeSlots', {})
    bottlenecks = analytics.get('bottlenecks', {})
    
    # 1. Load Balance Score (0-100)
    # Based on evenness of distribution
    per_teacher = workload.get('perTeacher', {})
    
    if per_teacher:
        balanced_count = sum(1 for m in per_teacher.values() if m.get('classification') == 'balanced')
        total_teachers = len(per_teacher)
        load_balance = (balanced_count / total_teachers * 100) if total_teachers > 0 else 50
    else:
        load_balance = 50
    
    # 2. Resource Efficiency Score (0-100)
    # Ideal utilization: 60-80%
    lab_util = lab_usage.get('overallUtilization', 0)
    free_pct = free_slots.get('freePercentage', 50)
    occupied_pct = 100 - free_pct
    
    # Penalize both over and under utilization
    if 60 <= occupied_pct <= 80:
        resource_efficiency = 100
    elif occupied_pct < 60:
        resource_efficiency = max(0, occupied_pct / 60 * 100)
    else:
        resource_efficiency = max(0, 100 - (occupied_pct - 80) * 2)
    
    # 3. Bottleneck Penalty (0-100)
    critical_count = bottlenecks.get('criticalCount', 0)
    warning_count = bottlenecks.get('warningCount', 0)
    
    bottleneck_penalty = 100 - (critical_count * 20 + warning_count * 5)
    bottleneck_penalty = max(0, min(100, bottleneck_penalty))
    
    # Weighted final score
    final_score = int(
        load_balance * 0.4 +
        resource_efficiency * 0.3 +
        bottleneck_penalty * 0.3
    )
    
    # Determine grade and stars
    if final_score >= 90:
        grade = "EXCELLENT"
        stars = 5
    elif final_score >= 75:
        grade = "GOOD"
        stars = 4
    elif final_score >= 60:
        grade = "FAIR"
        stars = 3
    elif final_score >= 40:
        grade = "POOR"
        stars = 2
    else:
        grade = "CRITICAL"
        stars = 1
    
    return {
        "score": final_score,
        "grade": grade,
        "stars": stars,
        "breakdown": {
            "loadBalance": int(load_balance),
            "resourceEfficiency": int(resource_efficiency),
            "bottleneckPenalty": int(bottleneck_penalty)
        }
    }


def extract_top_insights(analytics_insights):
    """
    Extract top 3 issues and top 3 strengths.
    
    Args:
        analytics_insights: Dictionary with all insights and bottlenecks
    
    Returns:
        (top_issues: [str], top_strengths: [str])
    """
    issues = []
    strengths = []
    
    bottlenecks = analytics_insights.get('bottlenecks', [])
    workload_insights = analytics_insights.get('workload_insights', [])
    lab_insights = analytics_insights.get('lab_insights', [])
    free_insights = analytics_insights.get('free_insights', [])
    quality_score = analytics_insights.get('quality_score', {})
    
    # Issues: prioritize critical bottlenecks
    for bottleneck in bottlenecks[:3]:  # Top 3 bottlenecks
        if bottleneck.get('severity') in ['critical', 'warning']:
            issues.append(bottleneck.get('title', 'Unknown issue'))
    
    # Add other issues from insights if less than 3
    if len(issues) < 3:
        for insight in workload_insights + lab_insights + free_insights:
            if insight.startswith(('⚠️', '⚡', '🔴')):
                if insight not in issues:
                    issues.append(insight)
                if len(issues) >= 3:
                    break
    
    # Strengths: positive indicators
    if quality_score.get('score', 0) >= 75:
        load_balance = quality_score.get('breakdown', {}).get('loadBalance', 0)
        resource_eff = quality_score.get('breakdown', {}).get('resourceEfficiency', 0)
        
        if load_balance >= 80:
            strengths.append("✅ Workload is well-balanced across teachers")
        
        if resource_eff >= 80:
            strengths.append("✅ Resource utilization is efficient")
    
    # Look for positive insights
    for insight in workload_insights + lab_insights + free_insights:
        if insight.startswith(('✅', '🟢', '📊')) and 'well' in insight.lower() or 'balanced' in insight.lower():
            if insight not in strengths:
                strengths.append(insight)
            if len(strengths) >= 3:
                break
    
    # If no critical issues, add this as strength
    if bottlenecks and all(b.get('severity') == 'info' for b in bottlenecks):
        strengths.append("✅ No critical scheduling conflicts detected")
    
    return issues[:3], strengths[:3]
