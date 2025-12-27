"""
Timetable Optimizer

Post-generation optimization using local search to improve soft constraint scores.
"""

import random
import copy
from constraints.constraint_engine import ConstraintEngine


class TimetableOptimizer:
    """Optimizes timetable using local search"""
    
    def __init__(self, context):
        """
        Initialize optimizer.
        
        Args:
            context: Generation context
        """
        self.context = context
        self.constraint_engine = ConstraintEngine()
    
    def optimize(self, timetable, max_iterations=100):
        """
        Optimize timetable using hill climbing with random restarts.
        
        Args:
            timetable: Initial valid timetable
            max_iterations: Maximum optimization iterations
        
        Returns:
            Optimized timetable with better quality score
        """
        if not timetable:
            return timetable
        
        current_timetable = copy.deepcopy(timetable)
        current_score = self.constraint_engine.compute_quality_score(
            current_timetable, self.context
        )
        
        best_timetable = copy.deepcopy(current_timetable)
        best_score = current_score
        
        iterations_without_improvement = 0
        max_stuck = 20
        
        for i in range(max_iterations):
            # Try swapping two random slots
            neighbor = self._generate_neighbor(current_timetable)
            
            if not neighbor:
                continue
            
            # Check if neighbor is valid
            validation = self.constraint_engine.validate_timetable(
                neighbor, self.context
            )
            
            if not validation['valid']:
                continue  # Invalid swap, skip
            
            # Compute neighbor score
            neighbor_score = validation['qualityScore']
            
            # Hill climbing: accept if better
            if neighbor_score > current_score:
                current_timetable = neighbor
                current_score = neighbor_score
                iterations_without_improvement = 0
                
                # Update best if needed
                if neighbor_score > best_score:
                    best_timetable = copy.deepcopy(neighbor)
                    best_score = neighbor_score
            else:
                iterations_without_improvement += 1
            
            # Random restart if stuck
            if iterations_without_improvement >= max_stuck:
                current_timetable = copy.deepcopy(best_timetable)
                current_score = best_score
                iterations_without_improvement = 0
        
        return best_timetable
    
    def _generate_neighbor(self, timetable):
        """
        Generate a neighbor timetable by swapping two compatible slots.
        
        Args:
            timetable: Current timetable
        
        Returns:
            Modified timetable with two slots swapped
        """
        if len(timetable) < 2:
            return None
        
        # Filter out practical slots (can't swap easily)
        lecture_slots = [s for s in timetable if s.get('type') == 'Lecture']
        
        if len(lecture_slots) < 2:
            return None
        
        # Pick two random lecture slots
        slot1, slot2 = random.sample(lecture_slots, 2)
        
        # Only swap if they're for the same year/division
        # (to maintain subject distribution)
        if (slot1['year'] != slot2['year'] or 
            slot1['division'] != slot2['division']):
            return None
        
        # Create neighbor
        neighbor = copy.deepcopy(timetable)
        
        # Find and swap
        for i, slot in enumerate(neighbor):
            if slot['id'] == slot1['id']:
                # Swap time/day
                neighbor[i]['day'] = slot2['day']
                neighbor[i]['slot'] = slot2['slot']
            elif slot['id'] == slot2['id']:
                # Swap time/day
                neighbor[i]['day'] = slot1['day']
                neighbor[i]['slot'] = slot1['slot']
        
        return neighbor
