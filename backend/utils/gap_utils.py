"""
Gap Utilities — backend/utils/gap_utils.py

Shared gap-counting functions used by:
  - validation/scorer.py          (quality scoring)
  - engine/theory_scheduler.py    (smart slot selection & day scoring)
  - engine/optimizer.py           (batch-level swap evaluation)
  - constraints/soft_constraints.py

Kept here to avoid circular imports between the engine and validation layers.

FIX A / SHARED UTILITY: Added build_batch_daily_schedule() and count_batch_gaps()
  so that every layer evaluates gaps at the individual-student (per-batch) level,
  not the whole-division level.
"""


# ---------------------------------------------------------------------------
# Division-level helpers (unchanged from prior version)
# ---------------------------------------------------------------------------

def count_gaps_in_day(day_slot_list):
    """
    Count empty slots that fall BETWEEN the first and last occupied slot
    in a division's (or batch's) ordered daily slot list.

    A gap is defined as: an empty position at index i where
        first_occupied < i < last_occupied  AND  day_slot_list[i] is None.

    Args:
        day_slot_list: ordered list of slot values indexed by slot position.
                       None (or missing) means the slot is empty;
                       a non-None value (dict, etc.) means the slot is occupied.

    Returns:
        int: number of gap slots (0 if fewer than 2 occupied slots on the day).

    Examples:
        [L, None, L, None, L] -> 2 gaps
        [L, L, L]             -> 0 gaps
        [None, None, L, None, None] -> 0 gaps  (only one occupied slot)
    """
    occupied_indices = [i for i, s in enumerate(day_slot_list) if s is not None]
    if len(occupied_indices) < 2:
        return 0
    first = occupied_indices[0]
    last = occupied_indices[-1]
    return sum(1 for i in range(first + 1, last) if day_slot_list[i] is None)


def count_teacher_gaps_in_day(teacher_day_slots):
    """
    Count empty slots that fall BETWEEN the first and last teaching slot
    for a single teacher on one day.

    Args:
        teacher_day_slots: ordered list indexed by slot position.
                           None = free, non-None = teaching a class.

    Returns:
        int: number of idle slots (0 if teacher has fewer than 2 sessions).
    """
    occupied = [i for i, s in enumerate(teacher_day_slots) if s is not None]
    if len(occupied) < 2:
        return 0
    first = occupied[0]
    last = occupied[-1]
    return sum(1 for i in range(first + 1, last) if teacher_day_slots[i] is None)


# ---------------------------------------------------------------------------
# FIX A: Batch-level helpers
# ---------------------------------------------------------------------------

def build_batch_daily_schedule(state, year, division, batch_name, day):
    """
    Returns an ordered list of slot entries (None = free, dict = occupied)
    representing a single student's day in a specific batch.

    A student in batch B1 attends:
      - All theory lectures assigned to (year, division, day)  — shared by all batches
      - Lab sessions specifically assigned to batch B1 on that day
      - NOT labs assigned to B2 or B3

    Args:
        state:      TimetableState
        year:       e.g. "BE"
        division:   e.g. "A"
        batch_name: e.g. "B1"
        day:        e.g. "Monday"

    Returns:
        list of length = total_slots_per_day, each element:
            None  → slot is free for this batch
            dict  → slot has an activity (theory or this batch's lab)
    """
    total_slots = state.get_total_slots()
    schedule = [None] * total_slots

    for slot_idx in range(total_slots):
        key = (day, slot_idx, year, division)
        entry = state.slot_grid.get(key)

        if entry is None:
            continue

        # Theory lecture: all batches attend
        if isinstance(entry, dict) and entry.get('type') == 'THEORY':
            schedule[slot_idx] = entry

        # Lab slot: list of batch-specific sessions
        elif isinstance(entry, list):
            for batch_session in entry:
                if isinstance(batch_session, dict) and batch_session.get('batch') == batch_name:
                    schedule[slot_idx] = batch_session
                    break
            # If this batch has no lab here, schedule[slot_idx] stays None.
            # This is the CRITICAL difference — a free slot for THIS batch.

        # Single dict that is a lab (older storage format fallback)
        elif isinstance(entry, dict) and entry.get('type') == 'LAB':
            if entry.get('batch') == batch_name:
                schedule[slot_idx] = entry
            # else: not this batch's lab → stays None

    return schedule


def count_batch_gaps(state, year, division, day):
    """
    Returns total gap count summed across ALL batches for a
    (year, division, day) combination.

    This replaces the old division-level count_gaps_in_day() call for the
    main student-gap scoring.  Division-level fallback is preserved for
    classes that have no lab batches.

    Args:
        state:    TimetableState
        year:     e.g. "BE"
        division: e.g. "A"
        day:      e.g. "Monday"

    Returns:
        int: sum of gaps across all batches (or division-level gaps if no batches).
    """
    batches = state.get_batches_for_division(year, division)

    # No batches defined → fall back to division-level check
    if not batches:
        total_slots = state.get_total_slots()
        slots = [state.slot_grid.get((day, i, year, division))
                 for i in range(total_slots)]
        return count_gaps_in_day(slots)

    total_gaps = 0
    for batch_name in batches:
        batch_schedule = build_batch_daily_schedule(
            state, year, division, batch_name, day
        )
        total_gaps += count_gaps_in_day(batch_schedule)

    return total_gaps
