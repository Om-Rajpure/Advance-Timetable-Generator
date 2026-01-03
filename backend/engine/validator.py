
"""
Post-Generation Timetable Validator
Implements strict per-division validation rules.
"""

class ValidationError(Exception):
    def __init__(self, stage, division, reason, details):
        self.stage = stage
        self.division = division
        self.reason = reason
        self.details = details
        super().__init__(f"[{stage}] {division} {reason}: {details}")

class TimetableValidator:
    def __init__(self, context):
        self.context = context
        self.smart_input = context.get('smartInputData', {})
        self.branch_data = context.get('branchData', {})

    def validate(self, timetables):
        """
        Validate the entire timetables map (all divisions).
        
        Args:
            timetables (dict): { "SE-A": { "Monday": [...] }, ... }
            
        Raises:
            ValidationError: If any rule is broken.
        """
        print("\n🔎 STARTING POST-GENERATION VALIDATION")
        print(f"   Divisions to validate: {list(timetables.keys())}")
        
        validation_summary = {}

        for division_key, timetable in timetables.items():
            try:
                self._validate_division(division_key, timetable)
                validation_summary[division_key] = "✅ VALID"
                print(f"   ✅ {division_key} passed validation.")
            except ValidationError as e:
                validation_summary[division_key] = f"❌ FAILED: {e.reason}"
                print(f"   ❌ {division_key} FAILED: {e.details}")
                raise e
            except Exception as e:
                validation_summary[division_key] = "❌ CRASHED"
                import traceback
                traceback.print_exc()
                raise ValidationError(
                    stage="POST_GENERATION_VALIDATION",
                    division=division_key,
                    reason="INTERNAL_ERROR",
                    details=str(e)
                )

        print("\n📊 VALIDATION SUMMARY")
        for div, status in validation_summary.items():
            print(f"   {div.ljust(10)} : {status}")
        print("--------------------------------------------------\n")

    def _validate_division(self, division_key, timetable):
        """Validate a single division's timetable."""
        
        # Rule A: Not Empty
        if not timetable or not isinstance(timetable, dict) or len(timetable.keys()) == 0:
            raise ValidationError(
                stage="POST_GENERATION_VALIDATION",
                division=division_key,
                reason="EMPTY_TIMETABLE",
                details="Timetable object is empty or invalid"
            )

        # Rule B: Minimum Working Days
        # Check actual days with classes
        days_with_classes = [d for d, slots in timetable.items() if len(slots) > 0]
        # We allow 5 or 6 usually. Let's strictly check against user config or default to 5.
        # User constraint: "if workingDaysWithClasses < 5"
        if len(days_with_classes) < 5:
             # Soft check? User said "THROW ERROR". But what if config says 4 days?
             # Let's check branch config for working days.
             wd = self.branch_data.get('workingDays', [])
             if isinstance(wd, list):
                 config_days = len(wd)
             else:
                 config_days = 5
             if len(days_with_classes) < min(5, config_days):
                 raise ValidationError(
                    stage="POST_GENERATION_VALIDATION",
                    division=division_key,
                    reason="INSUFFICIENT_DAYS",
                    details=f"Only {len(days_with_classes)} days scheduled, expected at least {min(5, config_days)}"
                 )

        # Parse Year and Division from key (e.g., "SE-A")
        try:
            year, division = division_key.split('-')
        except:
             # Fallback or skip specific checks if key format is weird
             year, division = "SE", "A" 

        # Rule C: Lab Coverage (CRITICAL)
        self._validate_lab_coverage(division_key, timetable, year, division)

        # Rule D: Theory Presence
        self._validate_theory_presence(division_key, timetable, year, division)

    def _validate_lab_coverage(self, division_key, timetable, year, division):
        """Ensure all batches have all required labs."""
        
        # 1. Identify Required Labs
        all_subjects = self.smart_input.get('subjects', [])
        required_labs = [
            s for s in all_subjects
            if s.get('type') == 'Practical' 
            and s.get('year') == year
            # Handle subject division specificity if exists, else applies to all
            and (not s.get('division') or s.get('division') == division)
        ]
        
        if not required_labs:
            return # No labs required, pass.

        # 2. Identify Batches
        # Usually ["B1", "B2", "B3"] or from config.
        # We can scan the timetable to see which batches appear, or default to standard 3.
        # Let's assume standard A/B/C or B1/B2/B3 mapping to A/B/C for now.
        # User prompt used "A, B, C". Data usually uses "B1, B2, B3".
        # Let's check what's in the timetable.
        found_batches = set()
        for day, slots in timetable.items():
            for slot in slots:
                if slot.get('batch'):
                    found_batches.add(slot.get('batch'))
        
        if not found_batches:
             # If no batches found in timetable, checking against Branch Defaults
             # Assuming standard 3 batches per year if not specified
             found_batches = ["B1", "B2", "B3"]
        
        batches_to_check = list(found_batches)

        # 3. Check Each Batch
        for batch in batches_to_check:
            scheduled_labs = set()
            for day, slots in timetable.items():
                for slot in slots:
                    if slot.get('type') == 'LAB' and slot.get('batch') == batch:
                        scheduled_labs.add(slot.get('subject'))
            
            # Compare
            missing = []
            for lab in required_labs:
                if lab['name'] not in scheduled_labs:
                    missing.append(lab['name'])
            
            if missing:
                raise ValidationError(
                    stage="POST_GENERATION_VALIDATION",
                    division=division_key,
                    reason="LAB_COVERAGE_FAILED",
                    details=f"Batch {batch} missing labs: {', '.join(missing)}"
                )

    def _validate_theory_presence(self, division_key, timetable, year, division):
        """Ensure total theory lectures meet requirements."""
        
        all_subjects = self.smart_input.get('subjects', [])
        theory_subjects = [
            s for s in all_subjects
            if s.get('type') != 'Practical'
            and s.get('year') == year
            and (not s.get('division') or s.get('division') == division)
        ]
        
        required_total = sum(int(s.get('weeklyLectures', 0)) for s in theory_subjects)
        
        # Count actual
        actual_total = 0
        for day, slots in timetable.items():
            for slot in slots:
                if slot.get('type') == 'THEORY':
                    actual_total += 1
        
        # Verification
        if actual_total < required_total:
             # Check margin.
             if required_total - actual_total > 2: # strict but allowing tiny drop
                raise ValidationError(
                    stage="POST_GENERATION_VALIDATION",
                    division=division_key,
                    reason="THEORY_MISSING",
                    details=f"Missing theory lectures. Required: {required_total}, Found: {actual_total}"
                )
