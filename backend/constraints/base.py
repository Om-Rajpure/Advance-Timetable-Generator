"""
Base Constraint Classes

Defines the interface that all constraints must implement.
"""


class ConstraintViolation:
    """Represents a single constraint violation"""
    
    def __init__(self, message, entities=None, slot=None, severity="HARD"):
        self.message = message
        self.entities = entities or {}
        self.slot = slot
        self.severity = severity
    
    def to_dict(self):
        """Convert violation to dictionary format"""
        return {
            "message": self.message,
            "entities": self.entities,
            "slot": self.slot,
            "severity": self.severity
        }


class Constraint:
    """Base class for all constraints"""
    
    def __init__(self, name, description, severity="HARD"):
        """
        Args:
            name: Unique constraint identifier (e.g., "TEACHER_NON_OVERLAP")
            description: Human-readable description
            severity: "HARD" (must never be violated) or "SOFT" (optimization goal)
        """
        self.name = name
        self.description = description
        self.severity = severity
        self.enabled = True
    
    def check(self, timetable, context):
        """
        Validate the constraint against the timetable state.
        
        Args:
            timetable: List of slot dictionaries with structure:
                {
                    "id": str,
                    "day": str,
                    "slot": int,
                    "year": str,
                    "division": str,
                    "batch": str (optional),
                    "subject": str,
                    "teacher": str,
                    "room": str,
                    "type": str ("Lecture" or "Practical")
                }
            context: Dictionary containing:
                {
                    "branchData": {...},
                    "smartInputData": {...}
                }
        
        Returns:
            Dictionary:
            {
                "valid": bool,
                "violations": [ConstraintViolation],
                "score": float (0-100, only for soft constraints)
            }
        """
        raise NotImplementedError(f"Constraint {self.name} must implement check() method")
    
    def explain(self):
        """Return a human-readable explanation of this constraint"""
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "enabled": self.enabled
        }
