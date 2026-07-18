"""
Teacher Timetable Generator

Derives a per-teacher weekly schedule from the completed state.slot_grid.
This is a pure data pivot — it contains no scheduling logic.

Usage (called from scheduler.py after all slots are placed):

    from engine.teacher_timetable import TeacherTimetableGenerator

    gen = TeacherTimetableGenerator(state, context)
    teacher_timetables = gen.generate()
    response["teacher_timetables"] = teacher_timetables

Output format — one entry per teacher:
    {
        teacher_name: {
            "name":         str,
            "weekly_load":  int,
            "schedule":     {day: [ {slot, time, subject, division, room, type}, ... ]},
            "gaps":         int,
            "busiest_day":  str,
            "free_days":    [str, ...],
        }
    }
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class TeacherTimetableGenerator:

    def __init__(self, state, context):
        """
        Args:
            state:   TimetableState — fully populated after generation.
            context: Dict with 'branchData' and 'smartInputData'.
        """
        self.state = state
        self.context = context
        branch = context.get("branchData", {})
        self.days = branch.get("workingDays", [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
        ])
        self.recess = branch.get("_computed_recess_slot", -1)
        if self.recess is None:
            self.recess = -1

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate(self):
        """
        Returns:
            dict[str, dict] — teacher_name → individual weekly schedule.
        """
        result = {}

        all_teachers = sorted({
            t.get("name", "")
            for t in self.context.get("smartInputData", {}).get("teachers", [])
            if t.get("name")
        })

        for teacher in all_teachers:
            weekly_load = 0
            schedule = {day: [] for day in self.days}
            gaps = 0

            for slot_key, assignment in self.state.slot_grid.items():
                # slot_key = (day, slot_index, year, division)
                try:
                    a_day, a_slot, a_year, a_div = slot_key
                except (TypeError, ValueError):
                    continue

                if a_day not in schedule:
                    continue

                # slot_grid values may be a single dict or a list of dicts
                asgns = assignment if isinstance(assignment, list) else [assignment]

                for asgn in asgns:
                    if not isinstance(asgn, dict):
                        continue
                    if asgn.get("teacher") != teacher:
                        continue

                    schedule[a_day].append({
                        "slot":     a_slot,
                        "time":     self._slot_to_time(a_slot),
                        "subject":  asgn.get("subject", ""),
                        "division": f"{a_year}-{a_div}",
                        "room":     asgn.get("room", ""),
                        "type":     asgn.get("type", "THEORY"),
                    })
                    weekly_load += 1

            # Sort each day's entries by slot index
            for day in self.days:
                schedule[day].sort(key=lambda s: s["slot"])

                idxs = [s["slot"] for s in schedule[day]]
                if len(idxs) >= 2:
                    for i in range(min(idxs), max(idxs) + 1):
                        if i != self.recess and i not in idxs:
                            gaps += 1

            day_loads = {day: len(schedule[day]) for day in self.days}
            busiest_day = max(day_loads, key=day_loads.get) if day_loads else self.days[0]
            free_days = [d for d, load in day_loads.items() if load == 0]

            result[teacher] = {
                "name":        teacher,
                "weekly_load": weekly_load,
                "schedule":    schedule,
                "gaps":        gaps,
                "busiest_day": busiest_day,
                "free_days":   free_days,
            }

        logger.info(
            f"[TeacherTimetable] Generated schedules for {len(result)} teachers."
        )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _slot_to_time(self, slot_idx):
        """Convert a 0-based slot index to a human-readable time range string."""
        branch = self.context.get("branchData", {})
        start = self._parse(branch.get("startTime", "9:00 AM"))
        dur = int(branch.get("lectureDuration", 60))
        recess_dur = int(branch.get("recessDuration", 60))

        # Add recess duration for slots after the recess
        extra = (
            recess_dur
            if self.recess >= 0 and slot_idx > self.recess
            else 0
        )

        s = start + slot_idx * dur + extra
        e = s + dur
        return f"{self._fmt(s)} \u2013 {self._fmt(e)}"

    def _fmt(self, minutes):
        """Format minute-offset as 'H:MM AM/PM'."""
        h, mn = divmod(int(minutes), 60)
        p = "AM" if h < 12 else "PM"
        if h > 12:
            h -= 12
        if h == 0:
            h = 12
        return f"{h}:{mn:02d} {p}"

    def _parse(self, ts):
        """Parse a time string to minutes since midnight."""
        try:
            try:
                from backend.utils.time_utils import parse_time
            except ImportError:
                from utils.time_utils import parse_time
            t = parse_time(str(ts))
            if t is not None:
                return t.hour * 60 + t.minute
        except Exception:
            pass
        return 9 * 60  # 9:00 AM fallback
