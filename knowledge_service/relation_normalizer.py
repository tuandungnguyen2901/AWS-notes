"""
Relation Normalizer - Normalize relation names to canonical forms
"""

import re
import logging
from typing import Dict, Optional
from difflib import SequenceMatcher

from .schema import RelationType

logger = logging.getLogger(__name__)


class RelationNormalizer:
    """Normalize relation names to canonical forms"""
    
    def __init__(self):
        # Mapping of common paraphrases to canonical relations
        self.paraphrase_map: Dict[str, RelationType] = {
            # uses variations
            "utilizes": RelationType.USES,
            "employs": RelationType.USES,
            "leverages": RelationType.USES,
            "makes use of": RelationType.USES,
            "uses": RelationType.USES,
            
            # implements variations
            "implements": RelationType.IMPLEMENTS,
            "follows": RelationType.IMPLEMENTS,
            "adopts": RelationType.IMPLEMENTS,
            "applies": RelationType.IMPLEMENTS,
            
            # addresses variations
            "addresses": RelationType.ADDRESSES,
            "mitigates": RelationType.ADDRESSES,
            "resolves": RelationType.ADDRESSES,
            "solves": RelationType.ADDRESSES,
            "handles": RelationType.ADDRESSES,
            
            # recommended_by variations
            "recommended_by": RelationType.RECOMMENDED_BY,
            "recommended": RelationType.RECOMMENDED_BY,
            "suggested_by": RelationType.RECOMMENDED_BY,
            "suggested": RelationType.RECOMMENDED_BY,
            "aligned_with": RelationType.RECOMMENDED_BY,
            
            # affects variations
            "affects": RelationType.AFFECTS,
            "impacts": RelationType.AFFECTS,
            "influences": RelationType.AFFECTS,
            "improves": RelationType.AFFECTS,
            "enhances": RelationType.AFFECTS,
            "reduces": RelationType.AFFECTS,
            
            # depends_on variations
            "depends_on": RelationType.DEPENDS_ON,
            "depends": RelationType.DEPENDS_ON,
            "requires": RelationType.DEPENDS_ON,
            "relies_on": RelationType.DEPENDS_ON,
            "needs": RelationType.DEPENDS_ON,
            
            # violates variations
            "violates": RelationType.VIOLATES,
            "breaks": RelationType.VIOLATES,
            "contradicts": RelationType.VIOLATES,
            "conflicts_with": RelationType.VIOLATES,
            
            # example_of variations
            "example_of": RelationType.EXAMPLE_OF,
            "example": RelationType.EXAMPLE_OF,
            "instance_of": RelationType.EXAMPLE_OF,
            "demonstrates": RelationType.EXAMPLE_OF,
        }
        
        # Build fuzzy matching cache
        self._build_fuzzy_cache()
    
    def _build_fuzzy_cache(self):
        """Build cache of relation names for fuzzy matching"""
        self.canonical_names = [rt.value for rt in RelationType]
    
    def normalize(self, relation_name: str) -> Optional[RelationType]:
        """
        Normalize a relation name to canonical form
        
        Args:
            relation_name: Relation name to normalize
            
        Returns:
            Canonical RelationType or None if not found
        """
        if not relation_name or not relation_name.strip():
            return None
        
        # Normalize input
        normalized = relation_name.lower().strip()
        normalized = re.sub(r'[_\s]+', '_', normalized)  # Normalize separators
        
        # Direct lookup in paraphrase map
        if normalized in self.paraphrase_map:
            return self.paraphrase_map[normalized]
        
        # Try exact match with canonical names
        try:
            return RelationType(normalized)
        except ValueError:
            pass
        
        # Fuzzy matching
        best_match = None
        best_ratio = 0.0
        
        for canonical_name in self.canonical_names:
            ratio = SequenceMatcher(None, normalized, canonical_name.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = canonical_name
        
        # Use fuzzy match if similarity is high enough
        if best_match and best_ratio >= 0.8:
            try:
                return RelationType(best_match)
            except ValueError:
                pass
        
        # Try partial matching (e.g., "uses" in "uses_component")
        for canonical_name in self.canonical_names:
            if canonical_name.lower() in normalized or normalized in canonical_name.lower():
                try:
                    return RelationType(canonical_name)
                except ValueError:
                    pass
        
        logger.debug(f"Could not normalize relation: {relation_name}")
        return None
    
    def normalize_triple_relation(self, triple) -> Optional[RelationType]:
        """
        Normalize relation in a triple
        
        Args:
            triple: Triple object
            
        Returns:
            Normalized RelationType or None
        """
        # If already a RelationType, return as-is
        if isinstance(triple.relation, RelationType):
            return triple.relation
        
        # Normalize from string
        return self.normalize(str(triple.relation))
