"""
Constraint Definition Engine

This module defines the rule-based validation system for timetable generation.
It enforces hard constraints (must never be violated) and soft constraints (optimization goals).
"""

from .base import Constraint, ConstraintViolation
from .hard_constraints import (
    TeacherNonOverlapConstraint,
    RoomNonOverlapConstraint,
    PracticalBatchSyncConstraint,
    WeeklyLectureCompletionConstraint,
    StructuralValidityConstraint
)
from .soft_constraints import (
    BalancedTeacherLoadConstraint,
    BalancedDailyLoadConstraint,
    SubjectRepetitionConstraint,
    PreferenceConstraint
)
from .constraint_engine import ConstraintEngine

__all__ = [
    'Constraint',
    'ConstraintViolation',
    'TeacherNonOverlapConstraint',
    'RoomNonOverlapConstraint',
    'PracticalBatchSyncConstraint',
    'WeeklyLectureCompletionConstraint',
    'StructuralValidityConstraint',
    'BalancedTeacherLoadConstraint',
    'BalancedDailyLoadConstraint',
    'SubjectRepetitionConstraint',
    'PreferenceConstraint',
    'ConstraintEngine'
]
