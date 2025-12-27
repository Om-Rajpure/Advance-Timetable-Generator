"""
Constraint Engine

Main orchestrator that manages all constraints, runs validation,
and generates comprehensive reports.
"""

from .hard_constraints import (
    TeacherNonOverlapConstraint,
    RoomNonOverlapConstraint,
    PracticalBatchSyncConstraint,
    WeeklyLectureCompletionConstraint,
    StructuralValidityConstraint
)
from .soft_constraints import (
    BalancedTeacherLoadConstraint,
    BalancedDailyLoadConstraint,
    SubjectRepetitionConstraint,
    PreferenceConstraint
)


class ConstraintEngine:
    """
    Main constraint validation engine.
    
    Manages all hard and soft constraints, runs validations,
    and generates comprehensive reports.
    """
    
    def __init__(self):
        # Register all hard constraints
        self.hard_constraints = [
            TeacherNonOverlapConstraint(),
            RoomNonOverlapConstraint(),
            PracticalBatchSyncConstraint(),
            WeeklyLectureCompletionConstraint(),
            StructuralValidityConstraint()
        ]
        
        # Register all soft constraints
        self.soft_constraints = [
            BalancedTeacherLoadConstraint(),
            BalancedDailyLoadConstraint(),
            SubjectRepetitionConstraint(),
            PreferenceConstraint()
        ]
    
    def validate_timetable(self, timetable, context):
        """
        Validate a complete timetable against all constraints.
        
        Args:
            timetable: List of slot dictionaries
            context: Dictionary with branchData and smartInputData
        
        Returns:
            {
                "valid": bool (True if all hard constraints pass),
                "hardViolations": [...],
                "softViolations": [...],
                "qualityScore": float (0-100),
                "summary": {...}
            }
        """
        hard_violations = []
        soft_violations = []
        soft_scores = []
        
        # Run all hard constraints
        for constraint in self.hard_constraints:
            if not constraint.enabled:
                continue
            
            result = constraint.check(timetable, context)
            if not result['valid']:
                for violation in result['violations']:
                    violation['constraint'] = constraint.name
                    hard_violations.append(violation)
        
        # Run all soft constraints
        for constraint in self.soft_constraints:
            if not constraint.enabled:
                continue
            
            result = constraint.check(timetable, context)
            soft_scores.append(result['score'])
            
            for violation in result['violations']:
                violation['constraint'] = constraint.name
                soft_violations.append(violation)
        
        # Calculate overall quality score (average of soft constraint scores)
        quality_score = sum(soft_scores) / len(soft_scores) if soft_scores else 100
        
        # Generate summary
        summary = {
            "totalSlots": len(timetable),
            "hardViolations": len(hard_violations),
            "softViolations": len(soft_violations),
            "qualityScore": round(quality_score, 2),
            "constraintsChecked": {
                "hard": len(self.hard_constraints),
                "soft": len(self.soft_constraints)
            }
        }
        
        return {
            "valid": len(hard_violations) == 0,
            "hardViolations": hard_violations,
            "softViolations": soft_violations,
            "qualityScore": round(quality_score, 2),
            "summary": summary
        }
    
    def validate_slot(self, new_slot, existing_timetable, context):
        """
        Validate adding a single slot to an existing timetable.
        
        This is useful for incremental timetable building, allowing
        the generation engine to check validity before committing a slot.
        
        Args:
            new_slot: The slot to be added
            existing_timetable: Current timetable state
            context: Dictionary with branchData and smartInputData
        
        Returns:
            {
                "valid": bool,
                "violations": [...],
                "conflicts": [...]  # Immediate conflicts with existing slots
            }
        """
        # Create temporary timetable with new slot
        temp_timetable = existing_timetable + [new_slot]
        
        violations = []
        conflicts = []
        
        # Run subset of hard constraints (only those that can be checked incrementally)
        incremental_constraints = [
            TeacherNonOverlapConstraint(),
            RoomNonOverlapConstraint(),
            StructuralValidityConstraint()
        ]
        
        for constraint in incremental_constraints:
            if not constraint.enabled:
                continue
            
            result = constraint.check(temp_timetable, context)
            if not result['valid']:
                for violation in result['violations']:
                    violation['constraint'] = constraint.name
                    violations.append(violation)
                    
                    # Check if violation involves the new slot
                    if self._involves_new_slot(violation, new_slot):
                        conflicts.append(violation)
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "conflicts": conflicts
        }
    
    def _involves_new_slot(self, violation, new_slot):
        """Check if a violation involves the new slot"""
        # Simple heuristic: check if day and time match
        day = new_slot.get('day')
        slot_index = new_slot.get('slot')
        
        entities = violation.get('entities', {})
        return (entities.get('day') == day and 
                entities.get('time_slot') == slot_index)
    
    def list_constraints(self):
        """
        Get a list of all registered constraints with their descriptions.
        
        Returns:
            {
                "hard": [...],
                "soft": [...]
            }
        """
        return {
            "hard": [c.explain() for c in self.hard_constraints],
            "soft": [c.explain() for c in self.soft_constraints]
        }
    
    def enable_constraint(self, constraint_name):
        """Enable a specific constraint by name"""
        for constraint in self.hard_constraints + self.soft_constraints:
            if constraint.name == constraint_name:
                constraint.enabled = True
                return True
        return False
    
    def disable_constraint(self, constraint_name):
        """Disable a specific constraint by name"""
        for constraint in self.hard_constraints + self.soft_constraints:
            if constraint.name == constraint_name:
                constraint.enabled = False
                return True
        return False
    
    def compute_quality_score(self, timetable, context):
        """
        Compute only the quality score without full validation.
        
        Useful for optimization algorithms that need quick scoring.
        
        Returns:
            float: Quality score (0-100)
        """
        soft_scores = []
        
        for constraint in self.soft_constraints:
            if not constraint.enabled:
                continue
            
            result = constraint.check(timetable, context)
            soft_scores.append(result['score'])
        
        return sum(soft_scores) / len(soft_scores) if soft_scores else 100
