"""
Slot Selection and Candidate Ordering Heuristics

Implements intelligent heuristics for CSP-based timetable generation.
"""


class SlotHeuristics:
    """Heuristics for slot selection and candidate ordering"""
    
    def __init__(self, state, context):
        """
        Initialize heuristics.
        
        Args:
            state: TimetableState instance
            context: Generation context
        """
        self.state = state
        self.context = context
        self.smart_input = context.get('smartInputData', {})
    
    def order_slots(self, slots):
        """
        Order slots by difficulty (Most Constrained First heuristic).
        
        Practicals are placed first as they have the hardest constraints
        (batch synchronization + multiple lab requirements).
        
        Args:
            slots: List of slot dictionaries
        
        Returns:
            Ordered list of slots
        """
        scored_slots = []
        
        for slot in slots:
            # Skip if already filled
            slot_key = (slot['day'], slot['slot'], slot['year'], slot['division'])
            if slot_key in self.state.slot_grid:
                continue
            
            # Skip if locked
            if self.state.is_slot_locked(slot_key):
                continue
            
            difficulty_score = self._calculate_slot_difficulty(slot)
            scored_slots.append((difficulty_score, slot))
        
        # Sort by difficulty (highest first)
        scored_slots.sort(key=lambda x: x[0], reverse=True)
        
        return [slot for (score, slot) in scored_slots]
    
    def _calculate_slot_difficulty(self, slot):
        """
        Calculate difficulty score for a slot.
        
        Higher score = more difficult (should be filled first)
        """
        score = 0
        year = slot['year']
        division = slot['division']
        
        # Check if this division needs practicals
        subjects = self.smart_input.get('subjects', [])
        has_practical = any(
            s.get('year') == year and 
            s.get('division') == division and 
            s.get('type') == 'Practical' and
            self.state.get_remaining_lectures(s.get('name'), year, division) > 0
            for s in subjects
        )
        
        if has_practical:
            score += 100  # Practicals are hardest
        
        # Check remaining subjects (fewer options = harder)
        remaining_subjects = sum(
            1 for s in subjects
            if (s.get('year') == year and 
                s.get('division') == division and
                self.state.get_remaining_lectures(s.get('name'), year, division) > 0)
        )
        
        if remaining_subjects > 0:
            score += (10 - remaining_subjects)  # Fewer options = higher score
        
        # Prefer earlier days
        day_order = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 
                     'Thursday': 3, 'Friday': 4, 'Saturday': 5}
        day_penalty = day_order.get(slot['day'], 6)
        score -= day_penalty  # Earlier days get slightly higher priority
        
        return score
    
    def select_next_slot(self, slots):
        """
        Select the next slot to fill using MRV (Minimum Remaining Values).
        
        Args:
            slots: List of unfilled slots
        
        Returns:
            The most constrained slot
        """
        if not slots:
            return None
        
        # Re-order and return first
        ordered = self.order_slots(slots)
        return ordered[0] if ordered else None
