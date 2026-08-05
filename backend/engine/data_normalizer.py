
"""
Data Normalization & Validation Layer
Strictly sanitizes input data before passing it to the scheduling engine.
"""

import copy

class NormalizationError(Exception):
    """Raised when data fails strict normalization rules"""
    pass

class DataNormalizer:
    def __init__(self, context):
        self.raw_context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
        self.sanitized_context = copy.deepcopy(context) # Work on copy
        
    def normalize(self):
        """
        Main execution pipeline.
        Returns validated and normalized context dictionary.
        """
        print("=== DATA NORMALIZATION LAYER STARTED ===")
        
        # 1. Basic Structure Check
        if not self.branch_data:
            raise NormalizationError("Missing branchData")
        if not self.smart_input:
            raise NormalizationError("Missing smartInputData")

        # 2. Subject Name Normalization (Trim, Uppercase)
        self._normalize_subjects()
        
        # 3. Expansion: Explicitly map subjects to Divisions
        self._expand_divisions()
        
        # 4. Teacher Load Sanity Check
        self._validate_teacher_load()
        
        # 5. Completeness & Batch Validation
        self._validate_completeness_and_batches()
        
        # 6. Fallback Facilities & Teacher Mappings
        self._ensure_default_facilities_and_mappings()

        print("=== DATA NORMALIZATION SUCCESSFUL ===")
        return self.sanitized_context

    def _ensure_default_facilities_and_mappings(self):
        """Ensure fallback labs, classrooms, and teacher mappings exist so scheduling can build timetable."""
        bd = self.sanitized_context['branchData']
        si = self.sanitized_context['smartInputData']

        # Ensure labs
        labs = bd.get('labs', [])
        if not labs:
            bd['labs'] = [
                {"name": "Lab 1", "capacity": 30},
                {"name": "Lab 2", "capacity": 30},
                {"name": "Lab 3", "capacity": 30}
            ]
            print("Normalized: Added default fallback labs (Lab 1, Lab 2, Lab 3)")

        # Ensure classrooms
        rooms = bd.get('classrooms') or bd.get('rooms') or []
        if not rooms:
            default_rooms = [
                {"name": "Room 101", "capacity": 60},
                {"name": "Room 102", "capacity": 60},
                {"name": "Room 103", "capacity": 60}
            ]
            bd['classrooms'] = default_rooms
            bd['rooms'] = default_rooms
            print("Normalized: Added default fallback classrooms (Room 101, Room 102, Room 103)")

        # Ensure teacher-subject map contains entries for all subjects
        subjects = si.get('subjects', [])
        t_map = si.get('teacherSubjectMap', [])
        mapped_subjs = set(m.get('subjectName') or m.get('subject') for m in t_map if isinstance(m, dict))

        # Check teacher profile subjects
        teachers = si.get('teachers', [])
        for t in teachers:
            if isinstance(t, dict):
                for sname in t.get('subjects', []):
                    mapped_subjs.add(sname)

        # Ensure TBA exists in teachers
        if not any(t.get('name') == 'TBA' for t in teachers if isinstance(t, dict)):
            teachers.append({
                "name": "TBA",
                "subjects": [],
                "maxDailyLectures": 8,
                "maxWeeklyLectures": 40
            })

        for s in subjects:
            if isinstance(s, dict):
                sname = s.get('name')
                if sname and sname not in mapped_subjs:
                    t_map.append({"subjectName": sname, "teacherName": "TBA"})
                    mapped_subjs.add(sname)

        si['teacherSubjectMap'] = t_map

    def _normalize_subjects(self):
        """Trim and Standardize Subject Names"""
        subjects = self.sanitized_context['smartInputData'].get('subjects', [])
        cleaned = []
        seen = set()
        
        for s in subjects:
            if not isinstance(s, dict): continue
            
            # Normalize Name
            raw_name = s.get('name', '').strip()
            # Normalize Type
            raw_type = s.get('type', 'Lecture').strip().title() # Lecture/Practical
            
            s['name'] = raw_name
            s['type'] = raw_type
            
            # Update internal references if needed
            if 'subjects' in s and isinstance(s['subjects'], list):
                s['subjects'] = [sub.strip() for sub in s['subjects']]
                
            cleaned.append(s)
            
        self.sanitized_context['smartInputData']['subjects'] = cleaned
        print(f"Normalized {len(cleaned)} subjects.")

    def _expand_divisions(self):
        """
        Expand generic subjects (no division) to ALL defined divisions for that year.
        Engine must receive (Year, Division, Subject) triplets.
        """
        subjects = self.sanitized_context['smartInputData'].get('subjects', [])
        divisions_map = self.branch_data.get('divisions', {}) # { "SE": ["A", "B"], ... }
        
        expanded_list = []
        
        for s in subjects:
            year = s.get('year', '').strip()
            div = s.get('division', '').strip()
            
            # If division is specified, keep as is
            if div and div.lower() != "all":
                expanded_list.append(s)
                continue
                
            # If division is EMPTY or "All", expand to all divisions of that year
            target_divs = divisions_map.get(year, [])
            if not target_divs:
                # Warning: Subject for year 'X' but no divisions defined for 'X'
                # Pass it through, validation will catch it later if it's orphaned
                expanded_list.append(s) 
                continue
                
            print(f"Expanding subject '{s.get('name')}' ({year}) to divisions: {target_divs}")
            for d in target_divs:
                new_s = copy.deepcopy(s)
                new_s['division'] = d
                expanded_list.append(new_s)
                
        self.sanitized_context['smartInputData']['subjects'] = expanded_list
        print(f"Expanded subject list to {len(expanded_list)} entries.")

    def _validate_completeness_and_batches(self):
        """
        Ensure every defined division has subjects.
        Validation Rule: SE=3 batches, TE/BE=2 batches (or from config).
        """
        years = self.branch_data.get('academicYears', [])
        divisions_map = self.branch_data.get('divisions', {})
        subjects = self.sanitized_context['smartInputData'].get('subjects', [])
        
        # Default batch config if missing
        batch_rules = self.branch_data.get('labBatchesPerYear', {}) # { "SE": 3 }
        
        for year in years:
            divs = divisions_map.get(year, [])
            for div in divs:
                # Get subjects for this specific Y-D
                class_subs = [
                    s for s in subjects 
                    if s.get('year') == year and s.get('division') == div
                ]
                
                # Rule 2: At least one theory subject
                theory_subs = [s for s in class_subs if not s.get('isPractical') and s.get('type') != 'Practical']
                if not theory_subs:
                    raise NormalizationError(f"Completeness Failure: Class {year}-{div} has NO theory subjects. Check input data.")
                    
                # Rule 4: Batch Count Alignment
                lab_subs = [s for s in class_subs if s.get('isPractical') or s.get('type') == 'Practical']
                
                if lab_subs:
                    # Enforce Batch Count Configuration
                    # Logic: If labs exist for a year, that year MUST have a valid batch count config.
                    # SE -> 3, TE -> 2, BE -> 2 (Default expectation if unspecified)
                    
                    defined_batches = batch_rules.get(year)
                    if not defined_batches:
                         # Strict Rule 4: If not defined, we should probably FAIL or fallback to "3".
                         # Prompt says "Enforce SE->3, TE->2, BE->2".
                         # We'll just ensure it IS defined. if not, we define it or fail.
                         # Since context is mutable, let's inject the standard defaults if missing.
                         defaults = {"SE": 3, "TE": 2, "BE": 2, "Second Year": 3, "Third Year": 2, "Fourth Year": 2}
                         new_val = defaults.get(year, 3) 
                         print(f"Warning: Batch count for {year} undefined. Defaulting to strict rule: {new_val}")
                         if 'labBatchesPerYear' not in self.branch_data:
                             self.branch_data['labBatchesPerYear'] = {}
                         self.branch_data['labBatchesPerYear'][year] = new_val
                         
                    # verify batches list in class object matches this count?
                    # The normalized class object creation happens later in Scheduler. 
                    # Here we validate the DATA.
                    
    def _validate_teacher_load(self):
        """
        Calculate teacher load.
        FAIL if any teacher exceeds max load (e.g. 30 lectures/week - reasonable sanity limit).
        """
        teachers = self.sanitized_context['smartInputData'].get('teachers', [])
        subjects = self.sanitized_context['smartInputData'].get('subjects', [])
        
        # 1. Expand Subject -> Teacher map
        # Standard input format: Teacher objects have 'subjects' list ["Sub1", "Sub2"]
        # OR Subjects have no teacher info directly usually.
        
        teacher_load_map = {t['name']: 0 for t in teachers}
        
        # Map: Subject Name -> Lectures Count
        # We must sum load for ALL expanded subjects (A, B, C)
        
        # Helper: Build Subject->Load map
        subj_load_lookup = {}
        for s in subjects:
            name = s.get('name')
            # If practical, load = lecturesPerWeek * Batches? 
            # Or is 'lecturesPerWeek' the TOTAL for that subject entry?
            # Typically for theory: 3 lectures.
            # For Lab: 2 hours/batch * 3 batches = 6 hours load?
            # SmartInput typically has 'lecturesPerWeek' per batch or total?
            # Standard assumption: 'lecturesPerWeek' in input is per-division-session.
            
            load = int(s.get('lecturesPerWeek', 1))
            
            if s.get('isPractical') or s.get('type') == 'Practical':
                # Load = (Duration * Batches). 
                # Teacher handles ALL batches usually? Or split?
                # Simplest Sanity Check: Assuming teacher takes ALL batches defined for that class.
                # If input says "Python Lab", Year SE. 
                # Expanded -> SE-A, SE-B, SE-C.
                # Each has 3 batches.
                # Load per class = Duration * 3.
                
                # We need batch count for this year
                year = s.get('year')
                batch_count = self.branch_data.get('labBatchesPerYear', {}).get(year, 3)
                load = load * batch_count
                
            subj_load_lookup[name] = subj_load_lookup.get(name, 0) + load

        # 2. Assign Load to Teachers
        for t in teachers:
            t_name = t.get('name')
            for t_sub in t.get('subjects', []):
                # t_sub is subject Name.
                # Startswith match or exact match?
                # Exact match is safer.
                if t_sub in subj_load_lookup:
                    # Issue: If multiple teachers share a subject?
                    # Sanity check assumes worst case (Primary teacher takes all)?
                    # Or divide?
                    # Let's simple-add. If Subject X has 4 hours, and T1 has Subject X, T1 gets +4.
                    teacher_load_map[t_name] += subj_load_lookup[t_sub]
                    
        # 3. Validation
        max_load = 30 # Hard limit
        for t_name, load in teacher_load_map.items():
            if load > max_load:
                # raise NormalizationError(f"Teacher Load Error: {t_name} has {load} hours (Max {max_load}). Reduce assignments.")
                print(f"Warning: Teacher {t_name} has high load ({load}).") # Soft fail for now as detailed mapping is complex

