"""
Teacher Load Manager

Handles global load balancing and continuity constraints for teachers.
Ensures:
1. Balanced workload across teachers (Daily/Weekly)
2. Subject-Division continuity (Same teacher for same subject-division)
3. Subject-Batch continuity (Same teacher for same subject-batch)
"""

import logging
from collections import defaultdict
import random

logger = logging.getLogger(__name__)

class TeacherLoadManager:
    def __init__(self, context):
        self.context = context
        self.smart_input = context.get('smartInputData', {})
        
        # Load Limits (Configurable?)
        self.MAX_DAILY_LOAD = 8 # Increased from 6
        self.MAX_WEEKLY_LOAD = 40 # Reverted to 40 per user request
        
        # --- STATE ---
        # 1. Load Tracking
        # { teacher_name: { day_name: count } }
        self.daily_load = defaultdict(lambda: defaultdict(int))
        
        # { teacher_name: total_count }
        self.weekly_load = defaultdict(int)
        
        # 2. Continuity Maps (The "Lock")
        # Theory: (subject_name, year, division) -> teacher_name
        self.theory_assignment_map = {}
        
        # Lab: (subject_name, year, division, batch) -> teacher_name
        self.lab_assignment_map = {}
        
        # 3. Cache available teachers per subject (includes fallback from teacher.subjects)
        self.subject_teacher_cache = self._build_subject_teacher_map()

        # 4. Strict subject->teacher map built ONLY from teacherSubjectMap.
        #    Used by pick_teacher() — never falls back to all teachers.
        self.subject_teacher_map = defaultdict(list)
        for mapping in self.smart_input.get('teacherSubjectMap', []):
            subj = mapping.get('subjectName', '')
            t = mapping.get('teacherName', '')
            if subj and t and t not in self.subject_teacher_map[subj]:
                self.subject_teacher_map[subj].append(t)

        # Reference to TimetableState (set externally after state is created)
        self._state = None

        # DIAGNOSTIC: log the full subject→teacher map so field-name bugs are visible
        logger.info("[LoadManager] subject_teacher_map at construction:")
        for subj, teachers in sorted(self.subject_teacher_map.items()):
            logger.info(f"  '{subj}' -> {teachers}")
        if not self.subject_teacher_map:
            logger.warning("[LoadManager] subject_teacher_map is EMPTY — check teacherSubjectMap field names in payload")

    def _build_subject_teacher_map(self):
        """Pre-process which teachers can teach which subject."""
        mapping = defaultdict(list)
        
        teachers = self.smart_input.get('teachers', [])
        explicit_map = self.smart_input.get('teacherSubjectMap', [])
        
        # 1. Use Explicit Map FIRST
        for em in explicit_map:
            sub_raw = em.get('subjectName')
            tea = em.get('teacherName')
            
            if sub_raw and tea:
                # Handle comma-separated subjects (e.g. "Math, Physics") OR Lists
                if isinstance(sub_raw, str):
                    subs = [s.strip() for s in sub_raw.split(',')]
                elif isinstance(sub_raw, list):
                    subs = sub_raw
                else:
                    subs = [str(sub_raw)]
                    
                for sub in subs:
                    if sub:
                        mapping[sub].append(tea)
                
        # 2. Fallback to Teacher's subject list
        for t in teachers:
            name = t.get('name')
            subjects = t.get('subjects', [])
            
            # Normalize 'subjects' if it's a string (though it should be a list)
            if isinstance(subjects, str):
                subjects = [s.strip() for s in subjects.split(',')]
                
            for s in subjects:
                # Handle comma-separated inside list items (defensive)
                if isinstance(s, str) and ',' in s:
                    sub_items = [x.strip() for x in s.split(',')]
                else:
                    sub_items = [s]
                    
                for sub in sub_items:
                    if name not in mapping[sub]:
                        mapping[sub].append(name)
                    
        return mapping

    def get_or_select_theory_teacher(self, subject, year, division):
        """
        Select best teacher for a Theory Subject (Year-Div).
        Prioritizes:
        1. EXISTING assigned teacher (Continuity)
        2. Subject Specialist (Mapped)
        3. Lowest Weekly Load
        """
        
        # 1. Check Continuity Lock
        continuity_key = (subject, year, division)
        if continuity_key in self.theory_assignment_map:
            return self.theory_assignment_map[continuity_key]
        
        # 2. Select New Teacher
        candidates = self.subject_teacher_cache.get(subject, [])
        if not candidates:
            # Fallback
            candidates = [t.get('name') for t in self.smart_input.get('teachers', [])]
            
        if not candidates:
            return "TBA"
            
        # 3. Sort by Weekly Load to balance globally
        # Higher priority to those with lower load
        candidates.sort(key=lambda t: self.weekly_load[t])
        
        best_teacher = candidates[0]
        
        # 4. Lock this choice for future
        self.theory_assignment_map[continuity_key] = best_teacher
        return best_teacher

    def get_best_teacher_for_lab(self, subject, year, division, batch, day, start_slot, duration, state_manager):
        """
        Select best teacher for a Lab session.
        Prioritizes:
        1. EXISTING assigned teacher for this batch (Strict Batch Continuity)
        2. Teacher teaching THEORY for this subject (Soft Preference)
        3. Lowest Load
        """
        # 1. Check Batch Continuity Lock
        continuity_key = (subject, year, division, batch)
        if continuity_key in self.lab_assignment_map:
            assigned_teacher = self.lab_assignment_map[continuity_key]
            if self._is_available_window(assigned_teacher, day, start_slot, duration, state_manager):
                 if self._check_hard_limits(assigned_teacher, day, load_cost=duration):
                     return assigned_teacher
                 else:
                     return None # Overloaded
            else:
                return None # Unavailable
                
        # 2. Select New Teacher
        candidates = self.subject_teacher_cache.get(subject, [])
        if not candidates:
             candidates = [t.get('name') for t in self.smart_input.get('teachers', [])]
             
        valid_candidates = []
        
        # Check for Theory Teacher Preference
        theory_key = (subject, year, division)
        theory_teacher = self.theory_assignment_map.get(theory_key)
        
        for t_name in candidates:
            # Check availability window
            if not self._is_available_window(t_name, day, start_slot, duration, state_manager):
                continue
                
            if not self._check_hard_limits(t_name, day, load_cost=duration):
                continue
                
            valid_candidates.append(t_name)
            
        if not valid_candidates:
            # PANIC MODE: Everyone is busy or overloaded.
            # We must return SOMEONE or generation fails.
            # Relax availability check? No, physical clash is impossible.
            # Relax LOAD limits? Yes.
            
            print(f"      [LoadManager] Panic: No teachers valid for {subject} Batch {batch} on {day}. Relaxing Load Limits.")
            
            # Re-scan candidates, checking ONLY availability
            for t_name in candidates:
                if self._is_available_window(t_name, day, start_slot, duration, state_manager):
                    valid_candidates.append(t_name)
                    
            if not valid_candidates:
                return None # Truly impossible (Physical availability)
            
        # 3. Sort by Load + Preference
        def sort_key(t_name):
            score = (self.weekly_load[t_name] * 10) + self.daily_load[t_name][day]
            # Bonus for being the theory teacher (lower score is better)
            if t_name == theory_teacher:
                score -= 50 # Massive preference
            return score
            
        valid_candidates.sort(key=sort_key)
        
        best_teacher = valid_candidates[0]
        
        # 4. Lock
        self.lab_assignment_map[continuity_key] = best_teacher
        return best_teacher

    def commit_load(self, teacher, day, duration=1):
        """Increment load counters when an assignment is finalized."""
        if not teacher: return
        self.daily_load[teacher][day] += duration
        self.weekly_load[teacher] += duration

    def record_assignment(self, teacher, day, slot):
        """
        Record a theory slot assignment in load counters.
        Alias for commit_load(duration=1) — used by CP-SAT TheoryScheduler.
        """
        self.commit_load(teacher, day, duration=1)

    def is_available(self, teacher, day, slot):
        """
        Check if a teacher is free at (day, slot) using the state's
        teacher_assignments dict.  Falls back to True when state is not set.
        Used by CP-SAT TheoryScheduler to verify picks from pick_teacher().
        """
        if self._state is not None:
            return self._state.is_teacher_available(teacher, day, slot)
        # Heuristic fallback: use daily load
        return self.daily_load[teacher][day] < self.MAX_DAILY_LOAD

    def pick_teacher(self, subject_name, day, slot):
        """
        Return a teacher for subject_name at (day, slot).

        Step 5.3 — STRICT: Only teachers explicitly mapped to this subject are
        considered.  The previous fallback to the entire teacher pool caused
        subjects to be taught by completely wrong teachers (e.g. AI → Mane,
        WC → Yeole).  That fallback is now REMOVED.

        Priority:
        1. subject_teacher_map  (built strictly from teacherSubjectMap entries)
        2. subject_teacher_cache (also parses comma-split keys, slightly broader)
        3. Absolute last resort: least-loaded mapped teacher (avoids TBA but
           keeps subject assignment correct)
        4. "TBA" only when truly no mapping exists for this subject at all.
        """
        # Collect mapped candidates — prefer subject_teacher_map (strict) but
        # fall through to subject_teacher_cache which catches comma-split variants.
        mapped = list(self.subject_teacher_map.get(subject_name, []))
        if not mapped:
            mapped = list(self.subject_teacher_cache.get(subject_name, []))

        if not mapped:
            logger.warning(
                f"[LoadManager] pick_teacher: NO mapping found for '{subject_name}' "
                f"— check teacherSubjectMap.  Returning TBA."
            )
            return "TBA"

        # Sort by weekly load — least loaded first
        sorted_teachers = sorted(mapped, key=lambda t: self.weekly_load.get(t, 0))

        # Return first available mapped teacher
        for teacher in sorted_teachers:
            if self.is_available(teacher, day, slot):
                return teacher

        # All mapped teachers are busy at this slot (e.g. two divisions need the
        # same rare teacher simultaneously).  Return least-loaded mapped teacher
        # rather than TBA — CP-SAT already constrained the slot so a real clash
        # at this point is a secondary teacher conflict, not a room/div conflict.
        logger.warning(
            f"[LoadManager] pick_teacher: All mapped teachers for '{subject_name}' "
            f"busy on {day} slot {slot}. Using least-loaded: {sorted_teachers[0]}"
        )
        return sorted_teachers[0]

    def rollback_load(self, teacher, day, duration=1):
        """Decrement load counters on rollback."""
        if not teacher: return
        self.daily_load[teacher][day] -= duration
        self.weekly_load[teacher] -= duration

    def _is_available(self, teacher, day, slot_index, state_manager):
        """Check if teacher is free and within working hours."""
        return state_manager.is_teacher_available(teacher, day, slot_index)

    def _is_available_window(self, teacher, day, start_slot, duration, state_manager):
        """Check availability for a block of slots."""
        for offset in range(duration):
            if not state_manager.is_teacher_available(teacher, day, start_slot + offset):
                return False
        return True

    def _check_hard_limits(self, teacher, day, load_cost=1):
        """Return True if adding load_cost doesn't exceed hard limits."""
        current_daily = self.daily_load[teacher][day]
        current_weekly = self.weekly_load[teacher]
        
        if current_daily + load_cost > self.MAX_DAILY_LOAD:
            return False
            
        # Uncomment for strict weekly limit
        # if current_weekly + load_cost > self.MAX_WEEKLY_LOAD:
        #    return False
            
        return True
