"""
What-If Simulation Module

Enables safe simulation of hypothetical changes to timetable environment
before applying them to the actual timetable.
"""

from .state_cloner import clone_timetable, clone_context
from .impact_analyzer import ImpactAnalyzer
from .partial_scheduler import PartialScheduler
from .scenarios import (
    simulate_teacher_unavailable,
    simulate_lab_unavailable,
    simulate_days_reduced
)
from .simulation_report import generate_simulation_report

__all__ = [
    'clone_timetable',
    'clone_context',
    'ImpactAnalyzer',
    'PartialScheduler',
    'simulate_teacher_unavailable',
    'simulate_lab_unavailable',
    'simulate_days_reduced',
    'generate_simulation_report'
]
