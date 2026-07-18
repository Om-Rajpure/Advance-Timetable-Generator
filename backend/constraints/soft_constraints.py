"""
Soft Constraints

These constraints represent optimization goals. They don't invalidate a timetable,
but affect its quality score. Higher scores indicate better timetables.

FIX 2C+2D: StudentGapConstraint and TeacherGapConstraint added to penalise
           idle/gap slots in daily division and teacher schedules.
"""

from .base import Constraint, ConstraintViolation
import statistics

# FIX 2C: import shared gap utilities
try:
    from utils.gap_utils import count_gaps_in_day, count_teacher_gaps_in_day
except ImportError:
    try:
        from backend.utils.gap_utils import count_gaps_in_day, count_teacher_gaps_in_day
    except ImportError:
        def count_gaps_in_day(day_slot_list):
            occupied = [i for i, s in enumerate(day_slot_list) if s is not None]
            if len(occupied) < 2: return 0
            return sum(1 for i in range(occupied[0] + 1, occupied[-1]) if day_slot_list[i] is None)
        def count_teacher_gaps_in_day(day_slot_list):
            return count_gaps_in_day(day_slot_list)



class ConsecutiveLectureConstraint(Constraint):
    """SC_New1: A teacher should not have more than 2 consecutive lectures."""
    def __init__(self):
        super().__init__(
            name="TEACHER_CONSECUTIVE_LIMIT",
            description="A teacher should not have more than 2 consecutive lectures",
            severity="SOFT"
        )
    
    def check(self, timetable, context):
        violations = []
        teacher_slots = {}
        for slot in timetable:
            t = slot.get('teacher')
            if not t or t == 'TBA': continue
            if t not in teacher_slots: teacher_slots[t] = []
            teacher_slots[t].append(slot)
            
        for teacher, slots in teacher_slots.items():
            slots.sort(key=lambda x: (x['day'], x['slot']))
            consecutive = 0
            last_day = None
            last_slot = -2
            
            for s in slots:
                if s['day'] == last_day and s['slot'] == last_slot + 1:
                    consecutive += 1
                else:
                    consecutive = 1
                
                last_day = s['day']
                last_slot = s['slot']
                
                if consecutive > 2:
                     violations.append(ConstraintViolation(
                        message=f"Teacher '{teacher}' has >2 consecutive lectures",
                        entities={"teacher": teacher},
                        slot=f"{s['day']} Slot {s['slot']}",
                        severity="SOFT"
                    ))
        
        return {
            "valid": True, 
            "violations": [v.to_dict() for v in violations],
            "score": max(0, 100 - (5 * len(violations))) # Simple score logic
        }

class StudentConsecutiveConstraint(Constraint):
    """SC_New2: A division should not have more than 3 continuous lectures."""
    def __init__(self):
        super().__init__(
            name="STUDENT_CONSECUTIVE_LIMIT",
            description="A division should not have more than 3 continuous lectures",
            severity="SOFT"
        )
    
    def check(self, timetable, context):
        violations = []
        div_slots = {}
        for slot in timetable:
            key = (slot['year'], slot['division'])
            if key not in div_slots: div_slots[key] = []
            div_slots[key].append(slot)
            
        for (year, div), slots in div_slots.items():
            slots.sort(key=lambda x: (x['day'], x['slot']))
            consecutive = 0
            last_day = None
            last_slot = -2
            
            for s in slots:
                if s['day'] == last_day and s['slot'] == last_slot + 1:
                    consecutive += 1
                else:
                    consecutive = 1
                
                last_day = s['day']
                last_slot = s['slot']
                
                if consecutive > 3:
                     violations.append(ConstraintViolation(
                        message=f"{year}-{div} has >3 continuous lectures",
                        entities={"year": year, "division": div},
                        slot=f"{s['day']} Slot {s['slot']}",
                        severity="SOFT"
                    ))
        
        return {
            "valid": True,
            "violations": [v.to_dict() for v in violations],
            "score": max(0, 100 - (2 * len(violations)))
        }

class BalancedTeacherLoadConstraint(Constraint):
    """SC1: Distribute lectures evenly across teachers"""
    
    def __init__(self):
        super().__init__(
            name="BALANCED_TEACHER_LOAD",
            description="Distribute lectures evenly across teachers to avoid overload",
            severity="SOFT"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Count lectures per teacher per day
        teacher_daily_load = {}
        for slot in timetable:
            if slot.get('type') == 'Practical':
                continue  # Don't count practicals
            
            teacher = slot.get('teacher')
            day = slot.get('day')
            
            if not teacher or teacher == 'TBA':
                continue
            
            key = (teacher, day)
            if key not in teacher_daily_load:
                teacher_daily_load[key] = 0
            teacher_daily_load[key] += 1
        
        # Calculate variance
        if len(teacher_daily_load) == 0:
            return {"valid": True, "violations": [], "score": 100}
        
        loads = list(teacher_daily_load.values())
        mean_load = statistics.mean(loads)
        
        if len(loads) > 1:
            variance = statistics.variance(loads)
            std_dev = statistics.stdev(loads)
        else:
            variance = 0
            std_dev = 0
        
        # Score based on standard deviation (lower is better)
        # Normalize: perfect score if std_dev = 0, lower score as std_dev increases
        max_acceptable_std_dev = 3.0
        score = max(0, 100 - (std_dev / max_acceptable_std_dev) * 100)
        
        # Report violations for teachers with significantly high load
        for (teacher, day), load in teacher_daily_load.items():
            if load > mean_load + std_dev:
                violations.append(ConstraintViolation(
                    message=f"Teacher '{teacher}' has {load} lectures on {day} (above average: {mean_load:.1f})",
                    entities={"teacher": teacher, "day": day, "load": load, "average": mean_load},
                    slot=day,
                    severity="SOFT"
                ))
        
        return {
            "valid": True,  # Soft constraints don't invalidate
            "violations": [v.to_dict() for v in violations],
            "score": round(score, 2)
        }


class BalancedDailyLoadConstraint(Constraint):
    """SC2: Avoid overloading students on particular days"""
    
    def __init__(self):
        super().__init__(
            name="BALANCED_DAILY_LOAD",
            description="Distribute lectures evenly across days to avoid student overload",
            severity="SOFT"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Count lectures per day per division
        division_daily_load = {}
        for slot in timetable:
            key = (slot.get('year'), slot.get('division'), slot.get('day'))
            if key not in division_daily_load:
                division_daily_load[key] = 0
            division_daily_load[key] += 1
        
        if len(division_daily_load) == 0:
            return {"valid": True, "violations": [], "score": 100}
        
        # Group by division, analyze distribution
        division_loads = {}
        for (year, division, day), count in division_daily_load.items():
            div_key = (year, division)
            if div_key not in division_loads:
                division_loads[div_key] = []
            division_loads[div_key].append(count)
        
        total_score = 0
        num_divisions = len(division_loads)
        
        for (year, division), daily_counts in division_loads.items():
            if len(daily_counts) <= 1:
                total_score += 100
                continue
            
            mean_load = statistics.mean(daily_counts)
            std_dev = statistics.stdev(daily_counts)
            
            # Score based on std deviation
            max_acceptable_std_dev = 2.0
            div_score = max(0, 100 - (std_dev / max_acceptable_std_dev) * 100)
            total_score += div_score
            
            # Report days with high load
            for (y, d, day), count in division_daily_load.items():
                if y == year and d == division and count > mean_load + std_dev:
                    violations.append(ConstraintViolation(
                        message=f"{year}-{division} has {count} lectures on {day} (above average: {mean_load:.1f})",
                        entities={"year": year, "division": division, "day": day, "load": count, "average": mean_load},
                        slot=day,
                        severity="SOFT"
                    ))
        
        score = total_score / num_divisions if num_divisions > 0 else 100
        
        return {
            "valid": True,
            "violations": [v.to_dict() for v in violations],
            "score": round(score, 2)
        }


class SubjectRepetitionConstraint(Constraint):
    """SC3: Avoid same subject appearing multiple times on the same day"""
    
    def __init__(self):
        super().__init__(
            name="SUBJECT_REPETITION_AVOIDANCE",
            description="Avoid scheduling the same subject multiple times in a single day",
            severity="SOFT"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Group by (day, year, division, subject)
        daily_subject_count = {}
        for slot in timetable:
            if slot.get('type') == 'Practical':
                continue  # Don't penalize practical repetitions
            
            key = (slot.get('day'), slot.get('year'), slot.get('division'), slot.get('subject'))
            if key not in daily_subject_count:
                daily_subject_count[key] = 0
            daily_subject_count[key] += 1
        
        # Find repetitions
        repetitions = 0
        total_days_subjects = len(daily_subject_count)
        
        for (day, year, division, subject), count in daily_subject_count.items():
            if count > 1:
                repetitions += count - 1  # Each extra occurrence is a penalty
                violations.append(ConstraintViolation(
                    message=f"{subject} appears {count} times on {day} for {year}-{division}",
                    entities={"subject": subject, "day": day, "year": year, "division": division, "count": count},
                    slot=day,
                    severity="SOFT"
                ))
        
        # Score: penalize each repetition
        if total_days_subjects == 0:
            score = 100
        else:
            # Each repetition reduces score
            penalty_per_repetition = 100 / max(total_days_subjects, 1)
            score = max(0, 100 - (repetitions * penalty_per_repetition))
        
        return {
            "valid": True,
            "violations": [v.to_dict() for v in violations],
            "score": round(score, 2)
        }



class PreferenceConstraint(Constraint):
    """SC4: Respect teacher and subject preferences (optional)"""

    def __init__(self):
        super().__init__(
            name="PREFERENCE_HANDLING",
            description="Respect teacher time preferences and subject scheduling preferences",
            severity="SOFT"
        )

    def check(self, timetable, context):
        violations = []

        # Get preferences from context (if available)
        smart_input = context.get('smartInputData', {})
        teacher_preferences = smart_input.get('teacherPreferences', {})
        subject_preferences = smart_input.get('subjectPreferences', {})

        if not teacher_preferences and not subject_preferences:
            # No preferences defined, perfect score
            return {"valid": True, "violations": [], "score": 100}

        satisfied_preferences = 0
        total_preferences = 0

        # Check teacher preferences
        for slot in timetable:
            teacher = slot.get('teacher')
            slot_time = slot.get('slot')  # 0-based slot index

            if teacher in teacher_preferences:
                pref = teacher_preferences[teacher]
                total_preferences += 1

                # Example preference structure: {"preferredSlots": [0, 1, 2], "avoidSlots": [6, 7]}
                if 'preferredSlots' in pref and slot_time in pref['preferredSlots']:
                    satisfied_preferences += 1
                elif 'avoidSlots' in pref and slot_time in pref['avoidSlots']:
                    violations.append(ConstraintViolation(
                        message=f"Teacher '{teacher}' prefers to avoid slot {slot_time}",
                        entities={"teacher": teacher, "slot": slot_time},
                        slot=f"{slot.get('day')} Slot {slot_time}",
                        severity="SOFT"
                    ))
                else:
                    satisfied_preferences += 0.5  # Neutral

        # Score based on satisfied preferences
        if total_preferences == 0:
            score = 100
        else:
            score = (satisfied_preferences / total_preferences) * 100

        return {
            "valid": True,
            "violations": [v.to_dict() for v in violations],
            "score": round(score, 2)
        }


class StudentGapConstraint(Constraint):
    """
    FIX 2C+2D: SC_Gap1 — Penalise empty slots that fall between lectures
    for the same division on the same day.

    A gap is defined as a slot at position i where first_occupied < i < last_occupied
    and the slot is unoccupied.  The constraint is SOFT: it lowers the score but
    never invalidates the timetable.
    """

    def __init__(self):
        super().__init__(
            name="STUDENT_GAP_MINIMISATION",
            description="Minimise idle/gap slots between lectures for each division",
            severity="SOFT"
        )

    def check(self, timetable, context):
        from collections import defaultdict
        violations = []

        # Build per-division-day slot grids
        grid = defaultdict(dict)  # {(year, div, day): {slot_index: slot}}
        for slot in timetable:
            year = slot.get('year')
            div  = slot.get('division')
            day  = slot.get('day')
            idx  = slot.get('slot', 0)
            if year and div and day:
                grid[(year, div, day)][idx] = slot

        total_gap_slots = 0
        total_days = len(grid)

        for (year, div, day), slot_map in grid.items():
            if not slot_map:
                continue
            max_idx  = max(slot_map.keys()) + 1
            day_list = [slot_map.get(i) for i in range(max_idx)]
            gaps = count_gaps_in_day(day_list)  # FIX 2C
            total_gap_slots += gaps

            if gaps > 0:
                violations.append(ConstraintViolation(
                    message=f"{year}-{div} has {gaps} gap slot(s) on {day}",
                    entities={"year": year, "division": div, "day": day, "gaps": gaps},
                    slot=day,
                    severity="SOFT"
                ))

        # Score: 1 gap / day -> -10 points; 0 gaps -> 100
        if total_days == 0:
            score = 100.0
        else:
            avg_gaps = total_gap_slots / total_days
            # Each average gap slot costs 20 points, floor at 0
            score = max(0.0, 100.0 - avg_gaps * 20.0)

        return {
            "valid": True,
            "violations": [v.to_dict() for v in violations],
            "score": round(score, 2)
        }


class TeacherGapConstraint(Constraint):
    """
    FIX 2C+2D: SC_Gap2 — Penalise idle slots that fall between teaching
    assignments for the same teacher on the same day.

    Same gap definition as StudentGapConstraint but applied to per-teacher
    daily schedules so the optimizer can also reduce teacher idle time.
    """

    def __init__(self):
        super().__init__(
            name="TEACHER_GAP_MINIMISATION",
            description="Minimise idle gaps between teaching slots for each teacher",
            severity="SOFT"
        )

    def check(self, timetable, context):
        from collections import defaultdict
        violations = []

        teacher_grid = defaultdict(dict)  # {(teacher, day): {slot_index: slot}}
        for slot in timetable:
            teacher = slot.get('teacher')
            day     = slot.get('day')
            idx     = slot.get('slot', 0)
            if teacher and teacher != 'TBA' and day:
                teacher_grid[(teacher, day)][idx] = slot

        total_idle_slots = 0
        total_teacher_days = len(teacher_grid)

        for (teacher, day), slot_map in teacher_grid.items():
            if not slot_map:
                continue
            max_idx  = max(slot_map.keys()) + 1
            day_list = [slot_map.get(i) for i in range(max_idx)]
            idle = count_teacher_gaps_in_day(day_list)  # FIX 2C
            total_idle_slots += idle

            if idle > 0:
                violations.append(ConstraintViolation(
                    message=f"Teacher '{teacher}' has {idle} idle gap(s) on {day}",
                    entities={"teacher": teacher, "day": day, "idle": idle},
                    slot=day,
                    severity="SOFT"
                ))

        if total_teacher_days == 0:
            score = 100.0
        else:
            avg_idle = total_idle_slots / total_teacher_days
            score = max(0.0, 100.0 - avg_idle * 15.0)

        return {
            "valid": True,
            "violations": [v.to_dict() for v in violations],
            "score": round(score, 2)
        }
