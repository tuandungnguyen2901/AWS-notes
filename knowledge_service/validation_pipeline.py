"""
Validation Pipeline - Orchestrate validation of triples
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .schema import Triple
from .triple_validator import TripleValidator, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Validation report"""
    total_triples: int
    valid_triples: int
    invalid_triples: int
    errors: List[ValidationError]
    error_summary: Dict[str, int]  # error_type -> count


class ValidationPipeline:
    """Pipeline for validating triples"""
    
    def __init__(self):
        self.validator = TripleValidator()
    
    def validate(self, triples: List[Triple]) -> Tuple[List[Triple], ValidationReport]:
        """
        Validate a list of triples
        
        Args:
            triples: List of triples to validate
            
        Returns:
            Tuple of (valid_triples, validation_report)
        """
        logger.info(f"Validating {len(triples)} triples...")
        
        valid_triples, errors = self.validator.validate_batch(triples)
        
        # Build error summary
        error_summary = {}
        for error in errors:
            error_type = error.error_type
            error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        report = ValidationReport(
            total_triples=len(triples),
            valid_triples=len(valid_triples),
            invalid_triples=len(errors),
            errors=errors,
            error_summary=error_summary
        )
        
        logger.info(f"Validation complete:")
        logger.info(f"  Valid: {report.valid_triples}")
        logger.info(f"  Invalid: {report.invalid_triples}")
        if error_summary:
            logger.info(f"  Error breakdown: {error_summary}")
        
        return valid_triples, report
    
    def generate_report(self, report: ValidationReport) -> str:
        """
        Generate a human-readable validation report
        
        Args:
            report: Validation report
            
        Returns:
            Report string
        """
        lines = [
            "=" * 60,
            "Validation Report",
            "=" * 60,
            f"Total triples: {report.total_triples}",
            f"Valid triples: {report.valid_triples}",
            f"Invalid triples: {report.invalid_triples}",
            ""
        ]
        
        if report.error_summary:
            lines.append("Error Summary:")
            for error_type, count in sorted(report.error_summary.items()):
                lines.append(f"  {error_type}: {count}")
            lines.append("")
        
        if report.errors:
            lines.append("Errors:")
            for i, error in enumerate(report.errors[:20], 1):  # Limit to first 20
                lines.append(f"  {i}. {error}")
                lines.append(f"     Triple: {error.triple.subject} --[{error.triple.relation.value}]--> {error.triple.object}")
            
            if len(report.errors) > 20:
                lines.append(f"  ... and {len(report.errors) - 20} more errors")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
