"""
Core Timetable Generation Engine

This package implements the CSP-based algorithm for generating valid,
optimized timetables.
"""

from .scheduler import TimetableScheduler
from .state_manager import TimetableState
from .candidate_generator import CandidateGenerator
from .heuristics import SlotHeuristics
from .optimizer import TimetableOptimizer

__all__ = [
    'TimetableScheduler',
    'TimetableState',
    'CandidateGenerator',
    'SlotHeuristics',
    'TimetableOptimizer'
]
