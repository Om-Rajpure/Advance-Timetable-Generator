"""
Improvement Engine

Safe optimization that improves timetable quality without breaking hard constraints.
"""

import copy
import random
from constraints.constraint_engine import ConstraintEngine


class ImprovementEngine:
    """Optimizes timetables while preserving hard constraints"""
    
    def __init__(self, context):
        """
        Initialize improvement engine.
        
        Args:
            context: Dictionary with branchData and smartInputData
        """
        self.context = context
        self.constraint_engine = ConstraintEngine()
    
    def improve(self, timetable, max_iterations=50):
        """
        Attempt to improve timetable quality via safe swaps.
        
        Args:
            timetable: List of slot dictionaries
            max_iterations: Maximum improvement attempts
        
        Returns:
            {
                "improved": bool,
                "timetable": [...],
                "improvements": [...],
                "scoreImprovement": float
            }
        """
        from .scorer import QualityScorer
        
        scorer = QualityScorer(self.context)
        
        # Compute initial score
        initial_score_data = scorer.compute_score(timetable)
        initial_score = initial_score_data['score']
        
        current_timetable = copy.deepcopy(timetable)
        current_score = initial_score
        
        improvements = []
        iterations_without_improvement = 0
        max_stuck = 15
        
        for i in range(max_iterations):
            # Try a safe swap
            improved_timetable = self._attempt_swap(current_timetable)
            
            if not improved_timetable:
                iterations_without_improvement += 1
                if iterations_without_improvement >= max_stuck:
                    break
                continue
            
            # Compute new score
            new_score_data = scorer.compute_score(improved_timetable)
            new_score = new_score_data['score']
            
            # Accept if better
            if new_score > current_score:
                current_timetable = improved_timetable
                improvement = new_score - current_score
                current_score = new_score
                iterations_without_improvement = 0
                
                improvements.append(f"Improved score by {improvement:.1f} points")
            else:
                iterations_without_improvement += 1
                if iterations_without_improvement >= max_stuck:
                    break
        
        return {
            "improved": current_score > initial_score,
            "timetable": current_timetable,
            "improvements": improvements,
            "scoreImprovement": round(current_score - initial_score, 1),
            "finalScore": current_score
        }
    
    def _attempt_swap(self, timetable):
        """
        Attempt a safe swap that preserves hard constraints.
        
        Returns:
            Modified timetable if swap is valid, None otherwise
        """
        # Filter lecture slots only (easier to swap)
        lecture_slots = [s for s in timetable if s.get('type') == 'Lecture']
        
        if len(lecture_slots) < 2:
            return None
        
        # Pick two random slots from the same division
        # Group by division
        division_slots = {}
        for slot in lecture_slots:
            key = (slot.get('year'), slot.get('division'))
            if key not in division_slots:
                division_slots[key] = []
            division_slots[key].append(slot)
        
        # Filter divisions with at least 2 slots
        swappable_divisions = {k: v for k, v in division_slots.items() if len(v) >= 2}
        
        if not swappable_divisions:
            return None
        
        # Pick random division
        division_key = random.choice(list(swappable_divisions.keys()))
        slots = swappable_divisions[division_key]
        
        # Pick two random slots
        slot1, slot2 = random.sample(slots, 2)
        
        # Create modified timetable with swapped day/time
        modified = copy.deepcopy(timetable)
        
        for i, slot in enumerate(modified):
            if slot.get('id') == slot1.get('id'):
                modified[i]['day'] = slot2['day']
                modified[i]['slot'] = slot2['slot']
            elif slot.get('id') == slot2.get('id'):
                modified[i]['day'] = slot1['day']
                modified[i]['slot'] = slot1['slot']
        
        # CRITICAL: Validate modified timetable
        validation = self.constraint_engine.validate_timetable(modified, self.context)
        
        if not validation['valid']:
            return None  # Reject swap that breaks constraints
        
        return modified
