"""
Edit Module

Backend support for timetable editing with validation and auto-fix.
"""

from .validate_edit import validate_slot_edit, validate_timetable_changes
from .suggest_fix import suggest_fix, find_alternate_teacher, find_alternate_room

__all__ = [
    'validate_slot_edit',
    'validate_timetable_changes',
    'suggest_fix',
    'find_alternate_teacher',
    'find_alternate_room'
]
