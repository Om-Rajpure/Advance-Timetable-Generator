"""
Timetable Validator

Final authoritative validation of timetables using the Constraint Engine.
"""

from constraints.constraint_engine import ConstraintEngine


class TimetableValidator:
    """Performs final validation on timetables before allowing edits"""
    
    def __init__(self):
        """Initialize validator with constraint engine"""
        self.constraint_engine = ConstraintEngine()
    
    def validate(self, timetable, context):
        """
        Perform comprehensive validation on a timetable.
        
        Args:
            timetable: List of slot dictionaries
            context: Dictionary with branchData and smartInputData
        
        Returns:
            {
                "valid": bool,
                "canProceed": bool,
                "hardViolations": [...],
                "softViolations": [...],
                "summary": {...},
                "message": str
            }
        """
        # Use constraint engine for comprehensive validation
        result = self.constraint_engine.validate_timetable(timetable, context)
        
        # Determine if user can proceed
        can_proceed = result['valid']  # Only proceed if no hard violations
        
        # Generate summary
        summary = {
            "totalSlots": len(timetable),
            "hardConstraintsPassed": 5 - len([v for v in result.get('hardViolations', []) 
                                               if v.get('severity') == 'HARD']),
            "hardViolationsCount": len([v for v in result.get('hardViolations', []) 
                                        if v.get('severity') == 'HARD']),
            "softViolationsCount": len([v for v in result.get('softViolations', []) 
                                        if v.get('severity') == 'SOFT'])
        }
        
        # Generate message
        if not can_proceed:
            message = f"Timetable has {summary['hardViolationsCount']} hard constraint violation(s). Please fix these before proceeding."
        else:
            message = "Timetable is valid and ready for use."
        
        return {
            "valid": result['valid'],
            "canProceed": can_proceed,
            "hardViolations": result.get('hardViolations', []),
            "softViolations": result.get('softViolations', []),
            "summary": summary,
            "message": message
        }
    
    def quick_validate(self, timetable, context):
        """
        Quick validation checking only hard constraints.
        
        Returns:
            {
                "valid": bool,
                "violationCount": int
            }
        """
        result = self.constraint_engine.validate_timetable(timetable, context)
        hard_violations = [v for v in result.get('hardViolations', []) 
                          if v.get('severity') == 'HARD']
        
        return {
            "valid": result['valid'],
            "violationCount": len(hard_violations)
        }
