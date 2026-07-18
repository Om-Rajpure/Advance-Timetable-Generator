"""
Quality Scorer

Multi-factor weighted scoring system for timetable quality.

FIX 2A: Import and use gap_utils.count_gaps_in_day / count_teacher_gaps_in_day.
FIX 2B: _score_student_gaps() and _score_teacher_gaps() added as new scoring factors.
FIX 2C: SCORING_WEIGHTS updated to include gap penalty dimensions.
FIX 2D: compute_score() wires the two new gap factors into the weighted total.
FIX A:  _score_student_gaps() now calls count_batch_gaps() instead of the
         division-level count_gaps_in_day(), evaluating gaps per individual
         student batch rather than the whole division.
         get_gap_report() added with worst_batch field.
"""

import statistics
from utils.gap_utils import (  # FIX 2A + FIX A
    count_gaps_in_day,
    count_teacher_gaps_in_day,
    build_batch_daily_schedule,
    count_batch_gaps,
)


# FIX 2C: Updated scoring weights — gaps now explicitly penalized
# Weights must sum to ≤ 1.0 (normalised inside compute_score anyway)
SCORING_WEIGHTS = {
    "teacher_balance":    0.25,   # reduced from 0.30 to make room for gap dimensions
    "student_balance":    0.20,   # reduced from 0.25
    "repetition":         0.15,   # reduced from 0.20
    "utilization":        0.10,   # unchanged
    "preferences":        0.05,   # unchanged
    # FIX 2C: two new gap-penalty dimensions
    "student_gaps":       0.15,   # penalty per division-day with internal gaps
    "teacher_gaps":       0.10,   # penalty per teacher-day with idle gaps
}


class QualityScorer:
    """Computes quality scores for timetables"""

    def __init__(self, context, weights=None):
        """
        Initialize scorer.

        Args:
            context: Dictionary with branchData and smartInputData
            weights: Optional custom weights dictionary
        """
        self.context = context
        self.weights = weights or SCORING_WEIGHTS

    def compute_score(self, timetable, resource_metrics=None):
        """
        Compute comprehensive quality score.

        Args:
            timetable: List of slot dictionaries
            resource_metrics: Optional pre-computed resource metrics

        Returns:
            {
                "score": float (0-100),
                "grade": str,
                "breakdown": {...},
                "penalties": [...]
            }
        """
        penalties = []

        # Factor 1: Teacher load balance
        teacher_balance_score, teacher_penalties = self._score_teacher_balance(timetable)
        penalties.extend(teacher_penalties)

        # Factor 2: Student daily balance
        student_balance_score, student_penalties = self._score_student_balance(timetable)
        penalties.extend(student_penalties)

        # Factor 3: Subject repetition
        repetition_score, repetition_penalties = self._score_repetition(timetable)
        penalties.extend(repetition_penalties)

        # Factor 4: Resource utilization
        utilization_score, util_penalties = self._score_utilization(timetable, resource_metrics)
        penalties.extend(util_penalties)

        # Factor 5: Preference satisfaction
        preference_score, pref_penalties = self._score_preferences(timetable)
        penalties.extend(pref_penalties)

        # FIX 2D: Factor 6 — Student-side gap penalty
        student_gap_score, sg_penalties = self._score_student_gaps(timetable)
        penalties.extend(sg_penalties)

        # FIX 2D: Factor 7 — Teacher-side gap penalty
        teacher_gap_score, tg_penalties = self._score_teacher_gaps(timetable)
        penalties.extend(tg_penalties)

        # Compute weighted score
        breakdown = {
            "teacherBalance": teacher_balance_score,
            "studentBalance": student_balance_score,
            "repetition": repetition_score,
            "utilization": utilization_score,
            "preferences": preference_score,
            "studentGaps": student_gap_score,   # FIX 2D
            "teacherGaps": teacher_gap_score,   # FIX 2D
        }

        # FIX 2D: Include all 7 factors in the weighted total
        total_score = (
            teacher_balance_score * self.weights["teacher_balance"] +
            student_balance_score * self.weights["student_balance"] +
            repetition_score      * self.weights["repetition"] +
            utilization_score     * self.weights["utilization"] +
            preference_score      * self.weights["preferences"] +
            student_gap_score     * self.weights.get("student_gaps", 0.15) +
            teacher_gap_score     * self.weights.get("teacher_gaps", 0.10)
        ) / sum(self.weights.values()) * 100

        grade = self._get_grade(total_score)

        return {
            "score": round(total_score, 1),
            "grade": grade,
            "breakdown": breakdown,
            "penalties": penalties
        }

    # ------------------------------------------------------------------
    # Existing scoring factors
    # ------------------------------------------------------------------

    def _score_teacher_balance(self, timetable):
        """Score teacher daily load balance"""
        teacher_daily_loads = {}

        for slot in timetable:
            teacher = slot.get('teacher')
            day = slot.get('day')
            if teacher and teacher != 'TBA':
                key = (teacher, day)
                teacher_daily_loads[key] = teacher_daily_loads.get(key, 0) + 1

        if not teacher_daily_loads:
            return 1.0, []

        loads = list(teacher_daily_loads.values())
        mean_load = statistics.mean(loads)
        std_dev = statistics.stdev(loads) if len(loads) > 1 else 0

        # Perfect score if std_dev = 0, lower as it increases
        max_acceptable_std_dev = 3.0
        score = max(0, 1 - (std_dev / max_acceptable_std_dev))

        # Generate penalties for high-load days
        penalties = []
        for (teacher, day), load in teacher_daily_loads.items():
            if load > mean_load + std_dev and load >= 4:
                penalties.append({
                    "type": "teacher_load",
                    "points": min(10, (load - mean_load) * 2),
                    "reason": f"Teacher '{teacher}' has {load} slots on {day}"
                })

        return score, penalties

    def _score_student_balance(self, timetable):
        """Score daily student load balance"""
        division_daily_loads = {}

        for slot in timetable:
            year = slot.get('year')
            division = slot.get('division')
            day = slot.get('day')
            key = (year, division, day)
            division_daily_loads[key] = division_daily_loads.get(key, 0) + 1

        if not division_daily_loads:
            return 1.0, []

        loads = list(division_daily_loads.values())
        mean_load = statistics.mean(loads)
        std_dev = statistics.stdev(loads) if len(loads) > 1 else 0

        max_acceptable_std_dev = 2.0
        score = max(0, 1 - (std_dev / max_acceptable_std_dev))

        penalties = []
        for (year, division, day), load in division_daily_loads.items():
            if load > mean_load + std_dev and load >= 6:
                penalties.append({
                    "type": "student_load",
                    "points": min(8, (load - mean_load) * 2),
                    "reason": f"{year}-{division} has {load} slots on {day}"
                })

        return score, penalties

    def _score_repetition(self, timetable):
        """Score subject repetition avoidance"""
        daily_subject_count = {}

        for slot in timetable:
            if slot.get('type') == 'Practical':
                continue

            key = (slot.get('day'), slot.get('year'), slot.get('division'), slot.get('subject'))
            daily_subject_count[key] = daily_subject_count.get(key, 0) + 1

        repetitions = 0
        penalties = []

        for (day, year, division, subject), count in daily_subject_count.items():
            if count > 1:
                repetitions += (count - 1)
                penalties.append({
                    "type": "subject_repetition",
                    "points": (count - 1) * 3,
                    "reason": f"{subject} appears {count} times on {day} for {year}-{division}"
                })

        total_days_subjects = len(daily_subject_count)
        if total_days_subjects == 0:
            score = 1.0
        else:
            penalty_ratio = repetitions / max(total_days_subjects, 1)
            score = max(0, 1 - penalty_ratio)

        return score, penalties

    def _score_utilization(self, timetable, resource_metrics):
        """Score resource utilization efficiency"""
        if not resource_metrics:
            # Compute if not provided
            from .resource_analysis import ResourceAnalyzer
            analyzer = ResourceAnalyzer(self.context)
            resource_metrics = analyzer.analyze(timetable)

        teacher_util = resource_metrics.get('teacherUtilization', {}).get('overall', 0)
        lab_util = resource_metrics.get('labUtilization', 0)
        room_util = resource_metrics.get('roomUtilization', 0)

        # Target utilization: 60-80% is ideal
        def util_score(util):
            if 60 <= util <= 80:
                return 1.0
            elif util < 60:
                return util / 60
            else:
                return max(0, 1 - (util - 80) / 20)

        avg_score = (util_score(teacher_util) + util_score(lab_util) + util_score(room_util)) / 3

        penalties = []
        if teacher_util < 50:
            penalties.append({
                "type": "underutilization",
                "points": 5,
                "reason": f"Teacher utilization is low ({teacher_util}%)"
            })

        return avg_score, penalties

    def _score_preferences(self, timetable):
        """Score preference satisfaction (placeholder)"""
        # TODO: Implement if preferences are provided
        return 1.0, []

    # ------------------------------------------------------------------
    # FIX 2B: NEW — Gap penalty scoring factors
    # ------------------------------------------------------------------

    def _score_student_gaps(self, timetable):
        """
        FIX A (was FIX 2B): Penalize internal gap slots for each student batch
        on each day.  A gap for B3 is just as bad as a gap for the whole division.

        Uses count_batch_gaps() which evaluates per-batch daily schedules:
          - Theory slots: all batches attend.
          - Lab slots: only the assigned batch attends.
        A "gap" is an empty slot between a student's first and last activity.

        Falls back to division-level count_gaps_in_day() when no batches are
        configured for a year (e.g. no labs).

        Penalty weight: -20 per gap (as spec'd).
        Returns score in [0, 1] where 1.0 = zero gaps.
        """
        STUDENT_GAP_PENALTY = 20   # FIX A: raised from 5 → 20 per spec

        from collections import defaultdict

        # We need the state object to call count_batch_gaps / get_batches_for_division.
        # scorer.py receives timetable (list), not state.  Build a lightweight state-
        # compatible proxy from what we have in the timetable list only when a real
        # state is not available.  When called from the optimizer the state IS passed
        # via context; fall back gracefully when it is not.
        state = getattr(self, '_state', None)  # injected by optimizer when available

        # Build division-day slot grids (needed for fallback path and for state proxy)
        grid = defaultdict(dict)  # {(year, div, day): {slot_index: slot_dict}}
        for slot in timetable:
            year = slot.get('year')
            div = slot.get('division')
            day = slot.get('day')
            idx = slot.get('slot', 0)
            if year is not None and div is not None and day is not None:
                grid[(year, div, day)][idx] = slot

        total_gap_slots = 0
        total_days = 0
        penalties = []
        worst_batch_gaps = 0
        worst_batch_label = None

        for (year, div, day), slot_map in grid.items():
            if not slot_map:
                continue
            total_days += 1

            if state is not None:
                # FIX A: use batch-aware counter from gap_utils
                gaps = count_batch_gaps(state, year, div, day)

                # Also track worst batch for get_gap_report()
                batches = state.get_batches_for_division(year, div)
                for batch_name in (batches or []):
                    b_sched = build_batch_daily_schedule(state, year, div, batch_name, day)
                    b_gaps = count_gaps_in_day(b_sched)
                    if b_gaps > worst_batch_gaps:
                        worst_batch_gaps = b_gaps
                        worst_batch_label = f"{year}-{div}-{batch_name}"
            else:
                # Fallback: division-level (no state object available)
                max_idx = max(slot_map.keys()) + 1
                day_list = [slot_map.get(i) for i in range(max_idx)]
                gaps = count_gaps_in_day(day_list)

            total_gap_slots += gaps

            if gaps > 0:
                penalty_points = min(10, gaps * STUDENT_GAP_PENALTY)
                penalties.append({
                    "type": "student_gap",
                    "points": penalty_points,
                    "reason": (
                        f"{year}-{div} has {gaps} batch gap(s) on {day}"
                    )
                })

        # Persist worst batch for get_gap_report()
        self._worst_batch_label = worst_batch_label

        # Score: 1 - (fraction of days with gaps) weighted by gap count
        if total_days == 0:
            return 1.0, []

        # Normalise: max expected gap-slots per day = 3 (anything worse is 0)
        max_tolerable_gap_ratio = 3.0
        raw_ratio = total_gap_slots / max(total_days, 1)
        score = max(0.0, 1.0 - (raw_ratio / max_tolerable_gap_ratio))

        return score, penalties

    def _score_teacher_gaps(self, timetable):
        """
        FIX 2B: Penalize idle slots that fall between teaching assignments for
        the same teacher on the same day.

        Returns a score in [0, 1] where 1.0 = no teacher waits in between.
        """
        TEACHER_GAP_PENALTY = 4  # points per idle slot

        from collections import defaultdict

        teacher_grid = defaultdict(dict)  # {(teacher, day): {slot_index: slot_dict}}
        for slot in timetable:
            teacher = slot.get('teacher')
            day = slot.get('day')
            idx = slot.get('slot', 0)
            if teacher and teacher != 'TBA' and day is not None:
                teacher_grid[(teacher, day)][idx] = slot

        total_idle_slots = 0
        total_teacher_days = 0
        penalties = []

        for (teacher, day), slot_map in teacher_grid.items():
            if not slot_map:
                continue
            total_teacher_days += 1
            max_idx = max(slot_map.keys()) + 1
            day_list = [slot_map.get(i) for i in range(max_idx)]
            idle = count_teacher_gaps_in_day(day_list)  # FIX 2A: use gap_utils
            total_idle_slots += idle

            if idle > 0:
                penalty_points = min(10, idle * TEACHER_GAP_PENALTY)
                penalties.append({
                    "type": "teacher_gap",
                    "points": penalty_points,
                    "reason": (
                        f"Teacher '{teacher}' has {idle} idle gap(s) on {day}"
                    )
                })

        if total_teacher_days == 0:
            return 1.0, []

        max_tolerable_idle_ratio = 2.0
        raw_ratio = total_idle_slots / max(total_teacher_days, 1)
        score = max(0.0, 1.0 - (raw_ratio / max_tolerable_idle_ratio))

        return score, penalties

    # ------------------------------------------------------------------
    # Grade helper
    # ------------------------------------------------------------------

    def _get_grade(self, score):
        """Convert score to grade"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Acceptable"
        else:
            return "Needs Improvement"

    # ------------------------------------------------------------------
    # FIX A: Gap report with worst_batch
    # ------------------------------------------------------------------

    def get_gap_report(self, timetable, state=None):
        """
        FIX A: Return a summary of gap statistics including the worst batch.

        Args:
            timetable: list of slot dicts
            state:     TimetableState (needed for batch-level reporting)

        Returns:
            dict with keys:
                'total_batch_gaps':  int   – sum of all gaps across all batches/days
                'worst_division':    str   – e.g. "BE-A" (div with most gap-days)
                'worst_batch':       str   – e.g. "BE-A-B3" (batch with most gaps)
                'gap_details':       list  – one entry per (year, div, day) with gaps
        """
        from collections import defaultdict

        if state is not None:
            self._state = state

        grid = defaultdict(dict)
        for slot in timetable:
            year = slot.get('year')
            div = slot.get('division')
            day = slot.get('day')
            idx = slot.get('slot', 0)
            if year is not None and div is not None and day is not None:
                grid[(year, div, day)][idx] = slot

        total_batch_gaps = 0
        div_gap_count = defaultdict(int)
        worst_batch_gaps = 0
        worst_batch_label = getattr(self, '_worst_batch_label', None)
        gap_details = []

        for (year, div, day), slot_map in grid.items():
            if not slot_map:
                continue

            if state is not None:
                day_gaps = count_batch_gaps(state, year, div, day)
                # Per-batch breakdown
                batches = state.get_batches_for_division(year, div)
                for batch_name in (batches or []):
                    b_sched = build_batch_daily_schedule(state, year, div, batch_name, day)
                    b_gaps = count_gaps_in_day(b_sched)
                    if b_gaps > worst_batch_gaps:
                        worst_batch_gaps = b_gaps
                        worst_batch_label = f"{year}-{div}-{batch_name}"
            else:
                max_idx = max(slot_map.keys()) + 1
                day_list = [slot_map.get(i) for i in range(max_idx)]
                day_gaps = count_gaps_in_day(day_list)

            total_batch_gaps += day_gaps
            div_gap_count[f"{year}-{div}"] += day_gaps

            if day_gaps > 0:
                gap_details.append({
                    'year': year, 'division': div, 'day': day, 'gaps': day_gaps
                })

        worst_division = max(div_gap_count, key=div_gap_count.get) if div_gap_count else None

        return {
            'total_batch_gaps': total_batch_gaps,
            'worst_division': worst_division,
            'worst_batch': worst_batch_label,
            'gap_details': sorted(gap_details, key=lambda x: x['gaps'], reverse=True),
        }
