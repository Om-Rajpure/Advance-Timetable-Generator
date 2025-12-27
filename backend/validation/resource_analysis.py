"""
Resource Analysis

Computes resource utilization metrics for timetables.
"""

import statistics


class ResourceAnalyzer:
    """Analyzes resource utilization in timetables"""
    
    def __init__(self, context):
        """
        Initialize analyzer with context.
        
        Args:
            context: Dictionary with branchData and smartInputData
        """
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
    
    def analyze(self, timetable):
        """
        Compute comprehensive resource utilization metrics.
        
        Args:
            timetable: List of slot dictionaries
        
        Returns:
            {
                "teacherUtilization": {...},
                "labUtilization": float,
                "roomUtilization": float,
                "loadDistribution": {...}
            }
        """
        return {
            "teacherUtilization": self._compute_teacher_utilization(timetable),
            "labUtilization": self._compute_lab_utilization(timetable),
            "roomUtilization": self._compute_room_utilization(timetable),
            "loadDistribution": self._compute_load_distribution(timetable)
        }
    
    def _compute_teacher_utilization(self, timetable):
        """Calculate teacher utilization metrics"""
        teachers = self.smart_input.get('teachers', [])
        
        if not teachers:
            return {"overall": 0, "perTeacher": {}}
        
        # Count slots per teacher
        teacher_slots = {}
        for slot in timetable:
            teacher = slot.get('teacher')
            if teacher and teacher != 'TBA':
                teacher_slots[teacher] = teacher_slots.get(teacher, 0) + 1
        
        # Calculate total available slots per day
        days = 6  # Monday to Saturday
        slots_per_day = self.branch_data.get('slotsPerDay', 8)
        total_available = days * slots_per_day
        
        # Compute per-teacher utilization
        per_teacher = {}
        total_assigned = 0
        
        for teacher_data in teachers:
            teacher_name = teacher_data.get('name')
            assigned = teacher_slots.get(teacher_name, 0)
            total_assigned += assigned
            
            utilization = (assigned / total_available) * 100 if total_available > 0 else 0
            per_teacher[teacher_name] = round(utilization, 1)
        
        # Overall utilization
        total_teacher_capacity = len(teachers) * total_available
        overall = (total_assigned / total_teacher_capacity) * 100 if total_teacher_capacity > 0 else 0
        
        return {
            "overall": round(overall, 1),
            "perTeacher": per_teacher
        }
    
    def _compute_lab_utilization(self, timetable):
        """Calculate lab utilization percentage"""
        labs = self.branch_data.get('labs', [])
        
        if not labs:
            return 0.0
        
        # Count practical slots using labs
        lab_slots_used = sum(1 for slot in timetable if slot.get('type') == 'Practical')
        
        # Calculate total lab capacity
        days = 6
        slots_per_day = self.branch_data.get('slotsPerDay', 8)
        total_lab_capacity = len(labs) * days * slots_per_day
        
        utilization = (lab_slots_used / total_lab_capacity) * 100 if total_lab_capacity > 0 else 0
        return round(utilization, 1)
    
    def _compute_room_utilization(self, timetable):
        """Calculate room utilization percentage"""
        rooms = self.branch_data.get('rooms', [])
        
        if not rooms:
            return 0.0
        
        # Count lecture slots using rooms
        room_slots_used = sum(1 for slot in timetable if slot.get('type') == 'Lecture')
        
        # Calculate total room capacity
        days = 6
        slots_per_day = self.branch_data.get('slotsPerDay', 8)
        total_room_capacity = len(rooms) * days * slots_per_day
        
        utilization = (room_slots_used / total_room_capacity) * 100 if total_room_capacity > 0 else 0
        return round(utilization, 1)
    
    def _compute_load_distribution(self, timetable):
        """Calculate load distribution variance"""
        # Teacher daily load variance
        teacher_daily_loads = {}
        for slot in timetable:
            teacher = slot.get('teacher')
            day = slot.get('day')
            if teacher and teacher != 'TBA':
                key = (teacher, day)
                teacher_daily_loads[key] = teacher_daily_loads.get(key, 0) + 1
        
        teacher_loads = list(teacher_daily_loads.values())
        teacher_variance = statistics.variance(teacher_loads) if len(teacher_loads) > 1 else 0
        
        # Division daily load variance
        division_daily_loads = {}
        for slot in timetable:
            year = slot.get('year')
            division = slot.get('division')
            day = slot.get('day')
            key = (year, division, day)
            division_daily_loads[key] = division_daily_loads.get(key, 0) + 1
        
        division_loads = list(division_daily_loads.values())
        division_variance = statistics.variance(division_loads) if len(division_loads) > 1 else 0
        
        return {
            "teacherVariance": round(teacher_variance, 2),
            "divisionVariance": round(division_variance, 2)
        }
