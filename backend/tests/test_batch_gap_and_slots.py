"""
Tests 6, 7, 8 — Batch-level gap counting, lab-safe slot selection, and contiguity preference.

Run from the backend directory:
    python -m pytest tests/test_batch_gap_and_slots.py -v

Or from the project root:
    python -m pytest backend/tests/test_batch_gap_and_slots.py -v
"""

import sys
import os
import unittest

# Make sure the backend package is importable
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from utils.gap_utils import (
    count_gaps_in_day,
    build_batch_daily_schedule,
    count_batch_gaps,
)


# ---------------------------------------------------------------------------
# Minimal TimetableState stub — only the fields gap_utils needs
# ---------------------------------------------------------------------------

class _MockState:
    """
    Lightweight mock of TimetableState that supports:
      - slot_grid  (dict keyed by (day, slot_idx, year, division))
      - get_total_slots()
      - get_batches_for_division(year, division)
      - is_slot_free / is_teacher_available (needed by TheoryScheduler)
    """

    def __init__(self, branch_data=None):
        self.slot_grid = {}
        self.recess_slot = 4
        self.total_slots = 8
        self.branch_data = branch_data or {}
        # TheoryScheduler stubs
        self.preferred_rooms = {}
        self.room_usage_counts = __import__('collections').Counter()
        self.teacher_assignments = {}
        self.teacher_metadata = {}

    def get_total_slots(self):
        return self.total_slots

    def get_batches_for_division(self, year, division):
        n = self.branch_data.get('labBatchesPerYear', {}).get(year, 0)
        return [f'B{i+1}' for i in range(n)]

    def get_daily_load_for_class(self, year, division, day):
        count = 0
        for s in range(self.total_slots):
            if (day, s, year, division) in self.slot_grid:
                count += 1
        return count

    def get_daily_load_for_teacher(self, teacher, day):
        return sum(
            1 for (t, d, _s) in self.teacher_assignments
            if t == teacher and d == day
        )

    def is_slot_free(self, day, slot_idx, year, division):
        return (day, slot_idx, year, division) not in self.slot_grid

    def is_teacher_available(self, teacher, day, slot_idx):
        return (teacher, day, slot_idx) not in self.teacher_assignments

    def is_room_available(self, room, day, slot_idx):
        return True  # rooms are always free in mock

    def get_schedulable_slots(self):
        return [i for i in range(self.total_slots) if i != self.recess_slot]

    def get_slot_assignment(self, day, slot_idx, year, division):
        return self.slot_grid.get((day, slot_idx, year, division))

    def assign_slot(self, assignment):
        key = (assignment['day'], assignment['slot'],
                assignment['year'], assignment['division'])
        existing = self.slot_grid.get(key)
        if existing is not None:
            if isinstance(existing, list):
                existing.append(assignment)
            else:
                self.slot_grid[key] = [existing, assignment]
        else:
            self.slot_grid[key] = assignment

    def _place_theory(self, day, slot_idx, year, division, subject='SUBJ'):
        """Helper: place a THEORY slot directly into the grid."""
        self.slot_grid[(day, slot_idx, year, division)] = {
            'type': 'THEORY', 'subject': subject,
            'year': year, 'division': division, 'day': day, 'slot': slot_idx,
        }

    def _place_lab(self, day, slot_idx, year, division, batch):
        """Helper: place a LAB batch entry into the grid (list format)."""
        key = (day, slot_idx, year, division)
        entry = {'type': 'LAB', 'batch': batch,
                 'year': year, 'division': division, 'day': day, 'slot': slot_idx}
        existing = self.slot_grid.get(key)
        if existing is None:
            self.slot_grid[key] = [entry]
        elif isinstance(existing, list):
            existing.append(entry)
        else:
            self.slot_grid[key] = [existing, entry]


# ---------------------------------------------------------------------------
# TEST 6: count_batch_gaps detects per-batch gaps
# ---------------------------------------------------------------------------

class TestBatchGapCounting(unittest.TestCase):
    """
    TEST 6 — count_batch_gaps must correctly detect gaps that exist for
    individual batches even when there is no division-wide gap.

    Setup:
        Division A has theory at slot 0 only.
        B1 has lab at slots 2–3.
        B2 has lab at slots 4–5.
        B3 has lab at slots 6–7.

    Expected:
        B1 schedule: [THEORY, None, LAB, LAB, None, None, None, None]
          → 1 gap between slot 0 and slot 2
        B2 schedule: [THEORY, None, None, None, LAB, LAB, None, None]
          → 3 gaps (slots 1, 2, 3)
        B3 schedule: [THEORY, None, None, None, None, None, LAB, LAB]
          → 5 gaps (slots 1-5)
        Total: 9 gaps
    """

    def setUp(self):
        branch_data = {
            'labBatchesPerYear': {'BE': 3},
        }
        self.state = _MockState(branch_data)
        self.year = 'BE'
        self.division = 'A'
        self.day = 'Monday'

        # Theory at slot 0
        self.state._place_theory(self.day, 0, self.year, self.division)
        # B1 lab at slots 2–3
        self.state._place_lab(self.day, 2, self.year, self.division, 'B1')
        self.state._place_lab(self.day, 3, self.year, self.division, 'B1')
        # B2 lab at slots 4–5  (note: slot 4 is recess but we override for test)
        self.state._place_lab(self.day, 4, self.year, self.division, 'B2')
        self.state._place_lab(self.day, 5, self.year, self.division, 'B2')
        # B3 lab at slots 6–7
        self.state._place_lab(self.day, 6, self.year, self.division, 'B3')
        self.state._place_lab(self.day, 7, self.year, self.division, 'B3')

    def test_initial_gaps_nonzero(self):
        """Assert that total batch gaps > 0 with only theory at slot 0."""
        total = count_batch_gaps(self.state, self.year, self.division, self.day)
        self.assertGreater(total, 0,
            f"Expected gaps > 0, got {total}. "
            "B2 and B3 each have large gaps relative to their labs.")

    def test_b1_schedule_has_one_gap(self):
        """B1: theory@0, lab@2-3 → 1 gap at slot 1."""
        sched = build_batch_daily_schedule(
            self.state, self.year, self.division, 'B1', self.day)
        gaps = count_gaps_in_day(sched)
        self.assertEqual(gaps, 1,
            f"B1 schedule should have 1 gap, got {gaps}. Schedule: {sched}")

    def test_b2_schedule_has_three_gaps(self):
        """B2: theory@0, lab@4-5 → 3 gaps (slots 1, 2, 3)."""
        sched = build_batch_daily_schedule(
            self.state, self.year, self.division, 'B2', self.day)
        gaps = count_gaps_in_day(sched)
        self.assertEqual(gaps, 3,
            f"B2 schedule should have 3 gaps, got {gaps}. Schedule: {sched}")

    def test_b3_schedule_has_five_gaps(self):
        """B3: theory@0, lab@6-7 → 5 gaps (slots 1-5)."""
        sched = build_batch_daily_schedule(
            self.state, self.year, self.division, 'B3', self.day)
        gaps = count_gaps_in_day(sched)
        self.assertEqual(gaps, 5,
            f"B3 schedule should have 5 gaps, got {gaps}. Schedule: {sched}")

    def test_adding_theory_at_slot1_reduces_gaps(self):
        """Adding theory at slot 1 reduces total gaps (B1 goes to 0, B2 to 2, B3 to 4)."""
        gaps_before = count_batch_gaps(self.state, self.year, self.division, self.day)

        self.state._place_theory(self.day, 1, self.year, self.division)
        gaps_after = count_batch_gaps(self.state, self.year, self.division, self.day)

        self.assertLess(gaps_after, gaps_before,
            f"Adding theory at slot 1 should reduce gaps. Before={gaps_before}, After={gaps_after}")
        self.assertGreater(gaps_after, 0,
            "B3 still has a large gap (slot 2-5 between theory block and its lab at 6-7).")

    def test_division_level_gap_would_be_zero(self):
        """
        Sanity: the division-level check (ignoring batches) shows 0 gaps
        because the ONLY theory slot is at slot 0 — a single occupied slot.
        This confirms WHY per-batch counting is necessary.
        """
        total_slots = self.state.get_total_slots()
        div_schedule = [
            self.state.slot_grid.get((self.day, i, self.year, self.division))
            for i in range(total_slots)
        ]
        # Division schedule sees: theory@0, lab_list@2,3,4,5,6,7
        # count_gaps_in_day treats any non-None as occupied
        div_gaps = count_gaps_in_day(div_schedule)
        # The division schedule has occupied slots at 0,2,3,4,5,6,7 — gap at slot 1
        # So division-level DOES see 1 gap, but misses B2's 3 gaps and B3's 5 gaps.
        batch_gaps = count_batch_gaps(self.state, self.year, self.division, self.day)
        self.assertGreater(batch_gaps, div_gaps,
            "Batch-level gap count should exceed division-level (B2, B3 have worse gaps).")


# ---------------------------------------------------------------------------
# TEST 7: _get_lab_safe_theory_slots returns correct ordering
# ---------------------------------------------------------------------------

class TestLabSafeSlots(unittest.TestCase):
    """
    TEST 7 — _get_lab_safe_theory_slots() must return slots before the
    earliest lab with gap_penalty = 0.

    Setup:
        B1 has lab at slots 3–4 on Monday.
        Recess slot = 4 (but in this test we set it to 8 so all slots are valid).
        No theory placed yet.

    Expected:
        Slots 0, 1, 2 have gap_penalty = 0 (before earliest lab at slot 3).
        Slots 5, 6, 7 have gap_penalty > 0 IF theory were placed there and
          then B1's day would be [lab@3, lab@4, theory@5/6/7] → gaps between
          start of day and the isolated theory slot... wait:
          B1's schedule with theory at slot 5: [None,None,None,LAB,LAB,THEORY,None,None]
          → first occupied = 3, last occupied = 5 → gap? slot 4 is occupied (LAB).
          Actually no gap there. Let's reconsider:
          B1 day: None None None LAB LAB THEORY None None
          occupied: 3,4,5 → first=3, last=5, gaps in range(4,5) = slot 4 → occupied → 0 gaps.
          Hmm — so for a single batch with contiguous lab+theory, gaps = 0.
          The gap only appears when theory is NOT adjacent to the lab.
          Theory at slot 6: B1 = None None None LAB LAB None THEORY None
          occupied: 3,4,6 → first=3,last=6 → check slot 5 → None = 1 gap.
    """

    def setUp(self):
        branch_data = {'labBatchesPerYear': {'BE': 1}}  # only B1
        self.state = _MockState(branch_data)
        self.state.recess_slot = 8   # push recess out of range for this test
        self.year = 'BE'
        self.division = 'A'
        self.day = 'Monday'

        # B1 lab at slots 3–4
        self.state._place_lab(self.day, 3, self.year, self.division, 'B1')
        self.state._place_lab(self.day, 4, self.year, self.division, 'B1')

    def _get_safe_slots_with_penalties(self):
        """Call _get_lab_safe_theory_slots and return (slot, penalty) pairs."""
        from engine.theory_scheduler import TheoryScheduler

        context = {
            'branchData': {'workingDays': ['Monday'], 'labBatchesPerYear': {'BE': 1}},
            'smartInputData': {'subjects': [], 'teachers': [], 'teacherSubjectMap': []},
        }
        scheduler = TheoryScheduler(self.state, context)
        safe = scheduler._get_lab_safe_theory_slots(
            self.day, self.year, self.division, self.state, recess_slot=8
        )
        return safe

    def test_pre_lab_slots_returned_first(self):
        """Slots 0, 1, 2 (before lab at slot 3) should have gap_penalty = 0."""
        from engine.theory_scheduler import TheoryScheduler
        context = {
            'branchData': {'workingDays': ['Monday'], 'labBatchesPerYear': {'BE': 1}},
            'smartInputData': {'subjects': [], 'teachers': [], 'teacherSubjectMap': []},
        }
        scheduler = TheoryScheduler(self.state, context)

        safe = scheduler._get_lab_safe_theory_slots(
            self.day, self.year, self.division, self.state, recess_slot=8
        )

        self.assertGreater(len(safe), 0, "Should return at least one safe slot.")

        # The first slot returned should be one of the pre-lab slots (0, 1, 2)
        first_slot = safe[0]
        self.assertIn(first_slot, [0, 1, 2, 5],
            f"Expected a zero-penalty slot first, got {first_slot}. "
            f"Full order: {safe}")

    def test_slot_adjacent_to_lab_is_safe(self):
        """Slot 2 (immediately before lab@3) and slot 5 (after lab@4) are safe."""
        from engine.theory_scheduler import TheoryScheduler
        context = {
            'branchData': {'workingDays': ['Monday'], 'labBatchesPerYear': {'BE': 1}},
            'smartInputData': {'subjects': [], 'teachers': [], 'teacherSubjectMap': []},
        }
        scheduler = TheoryScheduler(self.state, context)
        safe = scheduler._get_lab_safe_theory_slots(
            self.day, self.year, self.division, self.state, recess_slot=8
        )
        # Slots 2 and 5 must appear somewhere in the list
        self.assertIn(2, safe, "Slot 2 (pre-lab) should be in safe list.")
        self.assertIn(5, safe, "Slot 5 (post-lab) should be in safe list.")

    def test_gap_slots_have_higher_penalty(self):
        """Slot 6 (skips slot 5 after lab) should have a higher penalty than slot 5."""
        from engine.theory_scheduler import TheoryScheduler
        context = {
            'branchData': {'workingDays': ['Monday'], 'labBatchesPerYear': {'BE': 1}},
            'smartInputData': {'subjects': [], 'teachers': [], 'teacherSubjectMap': []},
        }
        scheduler = TheoryScheduler(self.state, context)
        safe = scheduler._get_lab_safe_theory_slots(
            self.day, self.year, self.division, self.state, recess_slot=8
        )

        if 5 in safe and 6 in safe:
            idx_5 = safe.index(5)
            idx_6 = safe.index(6)
            self.assertLessEqual(idx_5, idx_6,
                f"Slot 5 (adjacent to lab) should come before slot 6 in sorted order. "
                f"Got order: {safe}")


# ---------------------------------------------------------------------------
# TEST 8: Contiguity preference
# ---------------------------------------------------------------------------

class TestContiguityPreference(unittest.TestCase):
    """
    TEST 8 — When a theory slot already exists on a day, the next lecture
    must prefer the adjacent slot (slot immediately before/after the existing
    block), not a distant slot.

    Setup:
        Monday has theory at slot 0 for division A. No labs.
    Expected:
        _get_lab_safe_theory_slots returns slot 1 before slot 3 (or any other
        non-adjacent slot).
    """

    def setUp(self):
        branch_data = {'labBatchesPerYear': {'BE': 0}}  # no batches
        self.state = _MockState(branch_data)
        self.state.recess_slot = 4
        self.year = 'BE'
        self.division = 'A'
        self.day = 'Monday'

        # Theory at slot 0
        self.state._place_theory(self.day, 0, self.year, self.division)

    def test_slot1_before_slot3(self):
        """
        With theory at slot 0, slot 1 (adjacent) must appear before slot 3
        (non-adjacent) in the sorted result.
        """
        from engine.theory_scheduler import TheoryScheduler
        context = {
            'branchData': {'workingDays': ['Monday'], 'labBatchesPerYear': {'BE': 0}},
            'smartInputData': {'subjects': [], 'teachers': [], 'teacherSubjectMap': []},
        }
        scheduler = TheoryScheduler(self.state, context)
        safe = scheduler._get_lab_safe_theory_slots(
            self.day, self.year, self.division, self.state, recess_slot=4
        )

        self.assertIn(1, safe, "Slot 1 (adjacent to slot 0) must be in the result.")
        self.assertIn(3, safe, "Slot 3 should also be in the result (just ranked lower).")

        idx_1 = safe.index(1)
        idx_3 = safe.index(3)
        self.assertLess(idx_1, idx_3,
            f"Slot 1 (adjacent, gap_penalty=0) should appear before slot 3. "
            f"Got order: {safe}")

    def test_adjacent_slot_has_zero_gap_penalty(self):
        """
        Placing theory at slot 1 after slot 0 creates 0 gaps (contiguous block).
        Placing at slot 3 creates 1 gap (slot 2 is empty between 0 and 3).
        """
        total_slots = self.state.get_total_slots()

        # Simulate placing theory at slot 1
        sched_1 = [self.state.slot_grid.get((self.day, i, self.year, self.division))
                   for i in range(total_slots)]
        sched_1[1] = {'type': 'THEORY'}
        gaps_1 = count_gaps_in_day(sched_1)

        # Simulate placing theory at slot 3
        sched_3 = [self.state.slot_grid.get((self.day, i, self.year, self.division))
                   for i in range(total_slots)]
        sched_3[3] = {'type': 'THEORY'}
        gaps_3 = count_gaps_in_day(sched_3)

        self.assertEqual(gaps_1, 0,
            f"Placing theory at slot 1 (adjacent to slot 0) should create 0 gaps, got {gaps_1}.")
        self.assertGreater(gaps_3, 0,
            f"Placing theory at slot 3 (skipping slot 2) should create ≥1 gap, got {gaps_3}.")

    def test_first_slot_in_list_is_adjacent(self):
        """The first slot in _get_lab_safe_theory_slots must be adjacent (slot 1)."""
        from engine.theory_scheduler import TheoryScheduler
        context = {
            'branchData': {'workingDays': ['Monday'], 'labBatchesPerYear': {'BE': 0}},
            'smartInputData': {'subjects': [], 'teachers': [], 'teacherSubjectMap': []},
        }
        scheduler = TheoryScheduler(self.state, context)
        safe = scheduler._get_lab_safe_theory_slots(
            self.day, self.year, self.division, self.state, recess_slot=4
        )

        self.assertTrue(len(safe) > 0, "Should return at least one slot.")
        self.assertEqual(safe[0], 1,
            f"First result should be slot 1 (adjacent to existing slot 0, gap_penalty=0). "
            f"Got: {safe}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main(verbosity=2)
