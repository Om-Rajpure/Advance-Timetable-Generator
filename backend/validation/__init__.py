"""
Validation & Optimization Layer

This package provides the final quality gate for timetables,
ensuring validity, scoring quality, and optimizing before user editing.
"""

from .validator import TimetableValidator
from .resource_analysis import ResourceAnalyzer
from .scorer import QualityScorer
from .improvement_engine import ImprovementEngine
from .explainer import TimetableExplainer
from .validation_report import ValidationReport

__all__ = [
    'TimetableValidator',
    'ResourceAnalyzer',
    'QualityScorer',
    'ImprovementEngine',
    'TimetableExplainer',
    'ValidationReport'
]
