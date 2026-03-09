
"""
Load Filler Utility
Automatically increases subject load to fill all available slots.
"""

import copy
from utils.time_utils import calculate_time_slots

class LoadFiller:
    def __init__(self, context):
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
        
    def fill_all_slots(self):
        """
        Main entry point for load filling.
        Modifies self.context['smartInputData']['subjects'] in place.
        """
        print("=== LOAD FILLER STARTED ===")
        
        # 1. Total available slots per week
        try:
            time_config = calculate_time_slots(self.branch_data)
            slots_per_day = time_config['total_slots']
        except Exception as e:
            print(f"LOAD_FILLER ERROR: Could not calculate slots: {e}")
            return
            
        working_days = self.branch_data.get('workingDays', [])
        if not working_days or not isinstance(working_days, list):
            working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            
        total_slots_per_week = slots_per_day * len(working_days)
        print(f"Total available slots per week: {total_slots_per_week} ({slots_per_day} slots/day * {len(working_days)} days)")
        
        subjects = self.smart_input.get('subjects', [])
        years = self.branch_data.get('academicYears', [])
        divisions_map = self.branch_data.get('divisions', {})
        
        for year in years:
            divs = divisions_map.get(year, [])
            for div in divs:
                self._fill_class_load(year, div, subjects, total_slots_per_week)
                
        print("=== LOAD FILLER COMPLETED ===")

    def _fill_class_load(self, year, div, subjects, total_target_slots):
        """Adjusts load for a specific class division."""
        class_subs = [
            s for s in subjects 
            if s.get('year') == year and s.get('division') == div
        ]
        
        if not class_subs:
            return
            
        # Identify theory vs practical
        theory_subs = [s for s in class_subs if not s.get('isPractical') and s.get('type') != 'Practical']
        lab_subs = [s for s in class_subs if s.get('isPractical') or s.get('type') == 'Practical']
        
        if not theory_subs:
            print(f"Warning: No theory subjects to fill gap for {year}-{div}")
            return
            
        # Calculate occupied slots
        # Labs: (Duration * Batches) - but wait, in one division, 
        # do multiple batches happen simultaneously using distinct rooms?
        # Yes, but they occupy the SAME time slots in the division grid.
        # So for a division, Lab Duration 2 for 3 batches = 2 slots occupied physically on the division timetable.
        
        lab_occupied = 0
        for s in lab_subs:
            # We assume labs for a division happen in parallel, so they only occupy 'Duration' slots once.
            duration = int(s.get('sessionLength') or s.get('slots') or 2)
            lab_occupied += duration
            
        current_theory_load = sum(int(s.get('lecturesPerWeek', 0)) for s in theory_subs)
        total_occupied = lab_occupied + current_theory_load
        
        gap = total_target_slots - total_occupied
        
        if gap > 0:
            print(f"Filling GAP for {year}-{div}: TotalTarget={total_target_slots}, Labs={lab_occupied}, CurrentTheory={current_theory_load}, GAP={gap}")
            
            # Distribute gap among theory subjects round-robin
            idx = 0
            while gap > 0:
                theory_subs[idx % len(theory_subs)]['lecturesPerWeek'] = int(theory_subs[idx % len(theory_subs)].get('lecturesPerWeek', 0)) + 1
                gap -= 1
                idx += 1
        else:
            print(f"No GAP for {year}-{div} (Load already satisfies or exceeds capacity: {total_occupied}/{total_target_slots})")
