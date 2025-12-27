"""
Timetable Explainer

Generates human-readable explanations for timetable quality and issues.
"""


class TimetableExplainer:
    """Generates explanations for timetable quality and scores"""
    
    def __init__(self):
        """Initialize explainer"""
        pass
    
    def explain(self, validation_result, quality_score, resource_metrics):
        """
        Generate comprehensive explanation.
        
        Args:
            validation_result: Output from TimetableValidator
            quality_score: Output from QualityScorer
            resource_metrics: Output from ResourceAnalyzer
        
        Returns:
            {
                "summary": str,
                "scoreExplanation": str,
                "mainIssues": [...],
                "suggestions": [...]
            }
        """
        # Generate summary
        summary = self._generate_summary(validation_result, quality_score)
        
        # Explain score
        score_explanation = self._explain_score(quality_score)
        
        # Identify main issues
        main_issues = self._identify_main_issues(quality_score, validation_result)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(quality_score, main_issues, resource_metrics)
        
        return {
            "summary": summary,
            "scoreExplanation": score_explanation,
            "mainIssues": main_issues,
            "suggestions": suggestions
        }
    
    def _generate_summary(self, validation_result, quality_score):
        """Generate one-line summary"""
        if not validation_result['valid']:
            return f"Timetable has {validation_result['summary']['hardViolationsCount']} constraint violations and cannot be used."
        
        grade = quality_score['grade']
        score = quality_score['score']
        
        if grade == "Excellent":
            return f"Excellent timetable with score {score}/100. Well-balanced and efficient."
        elif grade == "Good":
            return f"Good quality timetable with score {score}/100. Minor improvements possible."
        elif grade == "Acceptable":
            return f"Acceptable timetable with score {score}/100. Some issues present."
        else:
            return f"Timetable needs improvement (score {score}/100). Several quality issues detected."
    
    def _explain_score(self, quality_score):
        """Explain how the score was computed"""
        score = quality_score['score']
        grade = quality_score['grade']
        breakdown = quality_score['breakdown']
        penalties = quality_score['penalties']
        
        explanation = f"Your timetable scored {score:.1f}/100 ({grade}). "
        
        if not penalties:
            explanation += "No quality issues detected - perfect score!"
            return explanation
        
        # Count penalty types
        penalty_types = {}
        total_points = 0
        for p in penalties:
            ptype = p['type']
            points = p.get('points', 0)
            penalty_types[ptype] = penalty_types.get(ptype, 0) + points
            total_points += points
        
        explanation += f"Points were deducted for: "
        
        issues = []
        if 'teacher_load' in penalty_types:
            issues.append(f"teacher load imbalance ({penalty_types['teacher_load']:.0f} points)")
        if 'student_load' in penalty_types:
            issues.append(f"student load imbalance ({penalty_types['student_load']:.0f} points)")
        if 'subject_repetition' in penalty_types:
            issues.append(f"subject repetition ({penalty_types['subject_repetition']:.0f} points)")
        if 'underutilization' in penalty_types:
            issues.append(f"resource underutilization ({penalty_types['underutilization']:.0f} points)")
        
        explanation += ", ".join(issues) + "."
        
        return explanation
    
    def _identify_main_issues(self, quality_score, validation_result):
        """Identify top 3 issues"""
        issues = []
        
        # Hard violations first
        if not validation_result['valid']:
            hard_count = validation_result['summary']['hardViolationsCount']
            issues.append(f"{hard_count} hard constraint violation(s)")
        
        # Soft constraint penalties
        penalties = quality_score['penalties']
        
        # Group and sort by severity
        penalty_types = {}
        for p in penalties:
            ptype = p['type']
            points = p.get('points', 0)
            penalty_types[ptype] = penalty_types.get(ptype, 0) + points
        
        sorted_penalties = sorted(penalty_types.items(), key=lambda x: x[1], reverse=True)
        
        issue_names = {
            'teacher_load': 'Teacher load imbalance',
            'student_load': 'Student daily load imbalance',
            'subject_repetition': 'Subject repetition on same day',
            'underutilization': 'Resource underutilization'
        }
        
        for ptype, points in sorted_penalties[:3]:
            if ptype in issue_names:
                issues.append(issue_names[ptype])
        
        return issues if issues else ["No significant issues"]
    
    def _generate_suggestions(self, quality_score, main_issues, resource_metrics):
        """Generate actionable suggestions"""
        suggestions = []
        penalties = quality_score['penalties']
        
        # Check for teacher load issues
        teacher_load_issues = [p for p in penalties if p['type'] == 'teacher_load']
        if teacher_load_issues:
            suggestions.append("Consider redistributing teacher workload across different days")
        
        # Check for repetition
        repetition_issues = [p for p in penalties if p['type'] == 'subject_repetition']
        if repetition_issues:
            # Get specific subjects
            subjects = set()
            for p in repetition_issues:
                reason = p.get('reason', '')
                if ' appears ' in reason:
                    subject = reason.split(' appears ')[0].split(' ')[-1]
                    subjects.add(subject)
            
            if subjects:
                suggestions.append(f"Spread subjects like {', '.join(list(subjects)[:2])} across different days")
        
        # Check for utilization
        if resource_metrics:
            teacher_util = resource_metrics.get('teacherUtilization', {}).get('overall', 0)
            if teacher_util < 50:
                suggestions.append("Teacher utilization is low - consider reducing number of teachers or adding more subjects")
        
        if not suggestions:
            suggestions.append("Timetable is well-optimized. No major improvements needed.")
        
        return suggestions
