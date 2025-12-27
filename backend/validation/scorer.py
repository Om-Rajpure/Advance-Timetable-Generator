"""
Quality Scorer

Multi-factor weighted scoring system for timetable quality.
"""

import statistics


# Configurable scoring weights
SCORING_WEIGHTS = {
    "teacher_balance": 0.30,
    "student_balance": 0.25,
    "repetition": 0.20,
    "utilization": 0.15,
    "preferences": 0.10
}


class QualityScorer:
    """Computes quality scores for timetables"""
    
    def __init__(self, context, weights=None):
        """
        Initialize scorer.
        
        Args:
            context: Dictionary with branchData and smartInputData
            weights: Optional custom weights dictionary
        """
        self.context = context
        self.weights = weights or SCORING_WEIGHTS
    
    def compute_score(self, timetable, resource_metrics=None):
        """
        Compute comprehensive quality score.
        
        Args:
            timetable: List of slot dictionaries
            resource_metrics: Optional pre-computed resource metrics
        
        Returns:
            {
                "score": float (0-100),
                "grade": str,
                "breakdown": {...},
                "penalties": [...]
            }
        """
        penalties = []
        
        # Factor 1: Teacher load balance
        teacher_balance_score,teacher_penalties = self._score_teacher_balance(timetable)
        penalties.extend(teacher_penalties)
        
        # Factor 2: Student daily balance
        student_balance_score, student_penalties = self._score_student_balance(timetable)
        penalties.extend(student_penalties)
        
        # Factor 3: Subject repetition
        repetition_score, repetition_penalties = self._score_repetition(timetable)
        penalties.extend(repetition_penalties)
        
        # Factor 4: Resource utilization
        utilization_score, util_penalties = self._score_utilization(timetable, resource_metrics)
        penalties.extend(util_penalties)
        
        # Factor 5: Preference satisfaction
        preference_score, pref_penalties = self._score_preferences(timetable)
        penalties.extend(pref_penalties)
        
        # Compute weighted score
        breakdown = {
            "teacherBalance": teacher_balance_score,
            "studentBalance": student_balance_score,
            "repetition": repetition_score,
            "utilization": utilization_score,
            "preferences": preference_score
        }
        
        total_score = (
            teacher_balance_score * self.weights["teacher_balance"] +
            student_balance_score * self.weights["student_balance"] +
            repetition_score * self.weights["repetition"] +
            utilization_score * self.weights["utilization"] +
            preference_score * self.weights["preferences"]
        ) / sum(self.weights.values()) * 100
        
        grade = self._get_grade(total_score)
        
        return {
            "score": round(total_score, 1),
            "grade": grade,
            "breakdown": breakdown,
            "penalties": penalties
        }
    
    def _score_teacher_balance(self, timetable):
        """Score teacher daily load balance"""
        teacher_daily_loads = {}
        
        for slot in timetable:
            teacher = slot.get('teacher')
            day = slot.get('day')
            if teacher and teacher != 'TBA':
                key = (teacher, day)
                teacher_daily_loads[key] = teacher_daily_loads.get(key, 0) + 1
        
        if not teacher_daily_loads:
            return 1.0, []
        
        loads = list(teacher_daily_loads.values())
        mean_load = statistics.mean(loads)
        std_dev = statistics.stdev(loads) if len(loads) > 1 else 0
        
        # Perfect score if std_dev = 0, lower as it increases
        max_acceptable_std_dev = 3.0
        score = max(0, 1 - (std_dev / max_acceptable_std_dev))
        
        # Generate penalties for high-load days
        penalties = []
        for (teacher, day), load in teacher_daily_loads.items():
            if load > mean_load + std_dev and load >= 4:
                penalties.append({
                    "type": "teacher_load",
                    "points": min(10, (load - mean_load) * 2),
                    "reason": f"Teacher '{teacher}' has {load} slots on {day}"
                })
        
        return score, penalties
    
    def _score_student_balance(self, timetable):
        """Score daily student load balance"""
        division_daily_loads = {}
        
        for slot in timetable:
            year = slot.get('year')
            division = slot.get('division')
            day = slot.get('day')
            key = (year, division, day)
            division_daily_loads[key] = division_daily_loads.get(key, 0) + 1
        
        if not division_daily_loads:
            return 1.0, []
        
        loads = list(division_daily_loads.values())
        mean_load = statistics.mean(loads)
        std_dev = statistics.stdev(loads) if len(loads) > 1 else 0
        
        max_acceptable_std_dev = 2.0
        score = max(0, 1 - (std_dev / max_acceptable_std_dev))
        
        penalties = []
        for (year, division, day), load in division_daily_loads.items():
            if load > mean_load + std_dev and load >= 6:
                penalties.append({
                    "type": "student_load",
                    "points": min(8, (load - mean_load) * 2),
                    "reason": f"{year}-{division} has {load} slots on {day}"
                })
        
        return score, penalties
    
    def _score_repetition(self, timetable):
        """Score subject repetition avoidance"""
        daily_subject_count = {}
        
        for slot in timetable:
            if slot.get('type') == 'Practical':
                continue
            
            key = (slot.get('day'), slot.get('year'), slot.get('division'), slot.get('subject'))
            daily_subject_count[key] = daily_subject_count.get(key, 0) + 1
        
        repetitions = 0
        penalties = []
        
        for (day, year, division, subject), count in daily_subject_count.items():
            if count > 1:
                repetitions += (count - 1)
                penalties.append({
                    "type": "subject_repetition",
                    "points": (count - 1) * 3,
                    "reason": f"{subject} appears {count} times on {day} for {year}-{division}"
                })
        
        total_days_subjects = len(daily_subject_count)
        if total_days_subjects == 0:
            score = 1.0
        else:
            penalty_ratio = repetitions / max(total_days_subjects, 1)
            score = max(0, 1 - penalty_ratio)
        
        return score, penalties
    
    def _score_utilization(self, timetable, resource_metrics):
        """Score resource utilization efficiency"""
        if not resource_metrics:
            # Compute if not provided
            from .resource_analysis import ResourceAnalyzer
            analyzer = ResourceAnalyzer(self.context)
            resource_metrics = analyzer.analyze(timetable)
        
        teacher_util = resource_metrics.get('teacherUtilization', {}).get('overall', 0)
        lab_util = resource_metrics.get('labUtilization', 0)
        room_util = resource_metrics.get('roomUtilization', 0)
        
        # Target utilization: 60-80% is ideal
        def util_score(util):
            if 60 <= util <= 80:
                return 1.0
            elif util < 60:
                return util / 60
            else:
                return max(0, 1 - (util - 80) / 20)
        
        avg_score = (util_score(teacher_util) + util_score(lab_util) + util_score(room_util)) / 3
        
        penalties = []
        if teacher_util < 50:
            penalties.append({
                "type": "underutilization",
                "points": 5,
                "reason": f"Teacher utilization is low ({teacher_util}%)"
            })
        
        return avg_score, penalties
    
    def _score_preferences(self, timetable):
        """Score preference satisfaction (placeholder)"""
        # TODO: Implement if preferences are provided
        return 1.0, []
    
    def _get_grade(self, score):
        """Convert score to grade"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Acceptable"
        else:
            return "Needs Improvement"
