"""
Validation Report

Generates comprehensive validation reports combining all validation components.
"""

from datetime import datetime
from .validator import TimetableValidator
from .resource_analysis import ResourceAnalyzer
from .scorer import QualityScorer
from .improvement_engine import ImprovementEngine
from .explainer import TimetableExplainer


class ValidationReport:
    """Generates comprehensive validation reports"""
    
    def __init__(self, context):
        """
        Initialize report generator.
        
        Args:
            context: Dictionary with branchData and smartInputData
        """
        self.context = context
        self.validator = TimetableValidator()
        self.resource_analyzer = ResourceAnalyzer(context)
        self.scorer = QualityScorer(context)
        self.improvement_engine = ImprovementEngine(context)
        self.explainer = TimetableExplainer()
    
    def generate_full_report(self, timetable, optimize=True):
        """
        Generate complete validation and optimization report.
        
        Args:
            timetable: List of slot dictionaries
            optimize: Whether to attempt optimization
        
        Returns:
            Comprehensive report dictionary
        """
        # Step 1: Validate
        validation_result = self.validator.validate(timetable, self.context)
        
        # Step 2: Resource analysis
        resource_metrics = self.resource_analyzer.analyze(timetable)
        
        # Step 3: Quality scoring
        quality_score = self.scorer.compute_score(timetable, resource_metrics)
        
        # Step 4: Optimization (if requested and valid)
        optimization_result = None
        final_timetable = timetable
        
        if optimize and validation_result['valid']:
            optimization_result = self.improvement_engine.improve(timetable)
            if optimization_result['improved']:
                final_timetable = optimization_result['timetable']
                # Recalculate score for optimized timetable
                quality_score = self.scorer.compute_score(final_timetable, resource_metrics)
        
        # Step 5: Generate explanations
        explanation = self.explainer.explain(validation_result, quality_score, resource_metrics)
        
        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "timetable": final_timetable,
            "validation": validation_result,
            "resourceAnalysis": resource_metrics,
            "qualityScore": quality_score,
            "optimization": optimization_result,
            "explanation": explanation,
            "canProceed": validation_result['canProceed']
        }
        
        return report
    
    def generate_quick_report(self, timetable):
        """
        Generate quick validation report without optimization.
        
        Args:
            timetable: List of slot dictionaries
        
        Returns:
            Simplified report
        """
        validation_result = self.validator.validate(timetable, self.context)
        quality_score = self.scorer.compute_score(timetable)
        
        return {
            "valid": validation_result['valid'],
            "canProceed": validation_result['canProceed'],
            "score": quality_score['score'],
            "grade": quality_score['grade'],
            "message": validation_result['message']
        }
