"""
Triple Validator - Validate triples against schema rules
"""

import logging
from typing import List, Dict, Optional, Tuple

from .schema import Triple, EntityType, RelationType, validate_relation_compatibility, SCHEMA_RULES

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error"""
    def __init__(self, triple: Triple, reason: str, error_type: str = "schema"):
        self.triple = triple
        self.reason = reason
        self.error_type = error_type
    
    def __str__(self):
        return f"{self.error_type}: {self.reason}"


class TripleValidator:
    """Validate triples against schema and business rules"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def validate(self, triple: Triple) -> bool:
        """
        Validate a triple
        
        Args:
            triple: Triple to validate
            
        Returns:
            True if valid, False otherwise
        """
        self.errors.clear()
        
        # Check required fields
        if not self._check_required_fields(triple):
            return False
        
        # Check entity types exist in schema
        if not self._check_entity_types(triple):
            return False
        
        # Check relation compatibility
        if not self._check_relation_compatibility(triple):
            return False
        
        # Check evidence length
        if not self._check_evidence_length(triple):
            return False
        
        # Check business rules
        if not self._check_business_rules(triple):
            return False
        
        return True
    
    def _check_required_fields(self, triple: Triple) -> bool:
        """Check that all required fields are present"""
        if not triple.subject or not triple.subject.strip():
            self.errors.append(ValidationError(
                triple, "Subject is empty", "required_field"
            ))
            return False
        
        if not triple.object or not triple.object.strip():
            self.errors.append(ValidationError(
                triple, "Object is empty", "required_field"
            ))
            return False
        
        if not triple.evidence or not triple.evidence.strip():
            self.errors.append(ValidationError(
                triple, "Evidence is empty", "required_field"
            ))
            return False
        
        return True
    
    def _check_entity_types(self, triple: Triple) -> bool:
        """Check that entity types are valid"""
        try:
            # Verify enum values are valid
            EntityType(triple.subject_type.value)
            EntityType(triple.object_type.value)
            RelationType(triple.relation.value)
        except ValueError as e:
            self.errors.append(ValidationError(
                triple, f"Invalid entity or relation type: {e}", "schema"
            ))
            return False
        
        return True
    
    def _check_relation_compatibility(self, triple: Triple) -> bool:
        """Check that relation is compatible with entity types"""
        if not validate_relation_compatibility(
            triple.relation, triple.subject_type, triple.object_type
        ):
            self.errors.append(ValidationError(
                triple,
                f"Relation '{triple.relation.value}' is not compatible with "
                f"subject type '{triple.subject_type.value}' and object type '{triple.object_type.value}'",
                "schema"
            ))
            return False
        
        return True
    
    def _check_evidence_length(self, triple: Triple) -> bool:
        """Check that evidence has sufficient length"""
        evidence_words = triple.evidence.strip().split()
        
        # Require at least 3 words unless inferred
        if len(evidence_words) < 3 and not triple.inferred:
            self.errors.append(ValidationError(
                triple,
                f"Evidence too short ({len(evidence_words)} words). Minimum 3 words required unless inferred.",
                "evidence"
            ))
            return False
        
        return True
    
    def _check_business_rules(self, triple: Triple) -> bool:
        """Check business-specific rules"""
        # Rule 1: recommended_by only for BestPractice -> Pillar
        if triple.relation == RelationType.RECOMMENDED_BY:
            if triple.subject_type != EntityType.BEST_PRACTICE:
                self.errors.append(ValidationError(
                    triple,
                    f"Relation 'recommended_by' requires subject type 'BestPractice', got '{triple.subject_type.value}'",
                    "business_rule"
                ))
                return False
            if triple.object_type != EntityType.PILLAR:
                self.errors.append(ValidationError(
                    triple,
                    f"Relation 'recommended_by' requires object type 'Pillar', got '{triple.object_type.value}'",
                    "business_rule"
                ))
                return False
        
        # Rule 2: addresses only for Mitigation/BestPractice -> Risk
        if triple.relation == RelationType.ADDRESSES:
            if triple.subject_type not in {EntityType.MITIGATION, EntityType.BEST_PRACTICE}:
                self.errors.append(ValidationError(
                    triple,
                    f"Relation 'addresses' requires subject type 'Mitigation' or 'BestPractice', got '{triple.subject_type.value}'",
                    "business_rule"
                ))
                return False
            if triple.object_type != EntityType.RISK:
                self.errors.append(ValidationError(
                    triple,
                    f"Relation 'addresses' requires object type 'Risk', got '{triple.object_type.value}'",
                    "business_rule"
                ))
                return False
        
        # Rule 3: uses typically for Service/Component -> Component
        if triple.relation == RelationType.USES:
            if triple.subject_type not in {EntityType.SERVICE, EntityType.COMPONENT}:
                # Warning, not error (schema allows it)
                logger.debug(f"Relation 'uses' typically has Service/Component as subject, got '{triple.subject_type.value}'")
        
        return True
    
    def get_errors(self) -> List[ValidationError]:
        """Get validation errors"""
        return self.errors
    
    def validate_batch(self, triples: List[Triple]) -> Tuple[List[Triple], List[ValidationError]]:
        """
        Validate a batch of triples
        
        Args:
            triples: List of triples to validate
            
        Returns:
            Tuple of (valid_triples, errors)
        """
        valid_triples = []
        all_errors = []
        
        for triple in triples:
            if self.validate(triple):
                valid_triples.append(triple)
            else:
                all_errors.extend(self.errors)
        
        return valid_triples, all_errors
