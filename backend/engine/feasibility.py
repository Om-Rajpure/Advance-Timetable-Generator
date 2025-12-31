"""
Feasibility Verifier

Checks if the given constraints and data are feasible for timetable generation
before attempting the expensive backtracking process.
"""

class FeasibilityVerifier:
    def __init__(self, context):
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
        self.subjects = self.smart_input.get('subjects', [])
        self.teachers = self.smart_input.get('teachers', [])
        
        # Extract basic configuration
        self.years = self.branch_data.get('academicYears', [])
        self.divisions = self.branch_data.get('divisions', {}) # { "SE": ["A", "B"] }
        self.slots_per_day = self.branch_data.get('slotsPerDay', 6)
        self.working_days = self.branch_data.get('workingDays', 5)
        # Assuming recess is 1 slot, effective slots = slots_per_day - 1 (simplified)
        # Improve: Get recess configuration if available
        self.effective_slots_per_day = self.slots_per_day 
        
        self.classrooms = self.branch_data.get('classrooms', {}) # { "SE": ["Room1", "Room2"] }
        # Shared labs are in 'sharedLabs' (new structure) or compatibility check
        self.labs = self.branch_data.get('sharedLabs', []) # List of { name: "Lab1", capacity: 30 }
        
        self.lab_batches_per_year = self.branch_data.get('labBatchesPerYear', {}) # { "SE": 3 }

    def verify(self):
        """
        Run all feasibility checks.
        Returns: { "valid": bool, "reason": str, "details": str }
        """
        
        # 1. Subject Validation
        if not self.subjects:
            return {"valid": False, "reason": "No subjects defined", "details": "Please upload subjects."}

        # 2. Time Feasibility (Theory)
        time_check = self._check_time_feasibility()
        if not time_check['valid']:
            return time_check
            
        # 3. Lab Resource Feasibility
        lab_check = self._check_lab_feasibility()
        if not lab_check['valid']:
            return lab_check
            
        # 4. Teacher Workload Feasibility
        teacher_check = self._check_teacher_feasibility()
        if not teacher_check['valid']:
            return teacher_check
            
        return {"valid": True, "message": "Configuration looks feasible"}

    def _check_time_feasibility(self):
        """Check if there are enough slots for theory lectures."""
        total_slots_available = self.working_days * self.effective_slots_per_day
        
        for year in self.years:
            year_divisions = self.divisions.get(year, [])
            for div in year_divisions:
                # Sum required theory lectures for this division
                required_lectures = 0
                for subject in self.subjects:
                    if subject.get('year') == year and not subject.get('isPractical', False):
                         # Assuming subject applies to all divisions
                         required_lectures += int(subject.get('weeklyLectures', 0))
                
                # Check against available slots (minus lab slots roughly)
                # Labs usually take 2 slots * number of lab subjects
                lab_subjects_count = sum(1 for s in self.subjects if s.get('year') == year and s.get('isPractical', False))
                # Lab session = 2 slots. Each division has 'lab_subjects_count' sessions/week (roughly)
                # Rule 8: Each division must complete all lab subjects every week.
                lab_slots_needed = lab_subjects_count * 2
                
                theory_slots_available = total_slots_available - lab_slots_needed
                
                if required_lectures > theory_slots_available:
                     return {
                        "valid": False,
                        "reason": f"Time infeasible for {year}-{div}",
                        "details": f"Requires {required_lectures} theory lectures + {lab_slots_needed} lab slots, but only {total_slots_available} total slots available."
                    }
                    
        return {"valid": True}

    def _check_lab_feasibility(self):
        """Check if there are enough physical labs for parallel batches."""
        total_labs = len(self.labs)
        
        for year in self.years:
            num_batches = int(self.lab_batches_per_year.get(year, 3))
            
            # Rule 10: All sub-batches run simultaneously
            # We need 'num_batches' labs available at the same time
            if num_batches > total_labs:
                return {
                    "valid": False,
                    "reason": f"Insufficient labs for {year}",
                    "details": f"{year} has {num_batches} parallel batches but only {total_labs} shared labs available."
                }
                
        return {"valid": True}

    def _check_teacher_feasibility(self):
        """Check if total teacher load is within limits."""
        total_teaching_load = 0
        total_teacher_capacity = 0
        
        # Calculate Load
        for year in self.years:
            num_divisions = len(self.divisions.get(year, []))
            num_batches = int(self.lab_batches_per_year.get(year, 3))
            
            for subject in self.subjects:
                if subject.get('year') == year:
                    weekly = int(subject.get('weeklyLectures', 0))
                    is_lab = subject.get('isPractical', False)
                    
                    if is_lab:
                        # 1 Lab = 1 Teacher * 2 Slots * num_batches * num_divisions
                        # Wait, load is measured in 'hours/periods'
                        # Lab session = 2 periods. 
                        # Total periods = 2 * num_divisions * num_batches
                        total_teaching_load += (2 * num_divisions * num_batches)
                    else:
                        # Theory
                        total_teaching_load += (weekly * num_divisions)
                        
        # Calculate Capacity
        for teacher in self.teachers:
            # Default to 20 if not specified (soft rule 18 says max weekly load)
            # Using a safe upper bound if not defined
            max_load = int(teacher.get('maxLecturesPerWeek', 25))
            total_teacher_capacity += max_load
            
        if total_teaching_load > total_teacher_capacity:
             return {
                "valid": False,
                "reason": "Teacher Overload",
                "details": f"Total required teaching periods: {total_teaching_load}, but total teacher capacity is {total_teacher_capacity}."
            }
            
        return {"valid": True}
