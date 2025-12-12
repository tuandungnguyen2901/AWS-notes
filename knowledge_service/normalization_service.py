"""
Normalization Service - Orchestrate normalization pipeline
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .schema import Triple, EntityType
from .entity_normalizer import get_normalizer, EntityNormalizer

logger = logging.getLogger(__name__)


@dataclass
class NormalizationMapping:
    """Represents a normalization mapping"""
    original: str
    canonical: str
    entity_type: EntityType
    confidence: float
    method: str  # "exact", "alias", "semantic", "none"


class NormalizationService:
    """Service to orchestrate entity normalization"""
    
    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize normalization service
        
        Args:
            similarity_threshold: Similarity threshold for semantic matching
        """
        self.normalizer = get_normalizer(similarity_threshold=similarity_threshold)
        self.mappings: Dict[str, NormalizationMapping] = {}
        self.conflicts: List[Dict] = []
    
    def normalize_triples(self, triples: List[Triple]) -> Tuple[List[Triple], List[NormalizationMapping], List[Dict]]:
        """
        Normalize entities in a list of triples
        
        Args:
            triples: List of triples to normalize
            
        Returns:
            Tuple of (normalized_triples, mappings, conflicts)
        """
        normalized_triples = []
        mappings = []
        conflicts = []
        
        for triple in triples:
            try:
                # Normalize subject
                subject_canonical, subject_conf, subject_method = self.normalizer.normalize(
                    triple.subject, triple.subject_type
                )
                
                # Normalize object
                object_canonical, object_conf, object_method = self.normalizer.normalize(
                    triple.object, triple.object_type
                )
                
                # Check for conflicts
                subject_key = f"{triple.subject}:{triple.subject_type.value}"
                object_key = f"{triple.object}:{triple.object_type.value}"
                
                # Track mappings
                if subject_canonical:
                    if subject_key in self.mappings:
                        existing = self.mappings[subject_key]
                        if existing.canonical != subject_canonical:
                            conflicts.append({
                                'entity': triple.subject,
                                'type': triple.subject_type.value,
                                'existing_canonical': existing.canonical,
                                'new_canonical': subject_canonical,
                                'existing_confidence': existing.confidence,
                                'new_confidence': subject_conf
                            })
                    else:
                        mapping = NormalizationMapping(
                            original=triple.subject,
                            canonical=subject_canonical,
                            entity_type=triple.subject_type,
                            confidence=subject_conf,
                            method=subject_method
                        )
                        self.mappings[subject_key] = mapping
                        mappings.append(mapping)
                
                if object_canonical:
                    if object_key in self.mappings:
                        existing = self.mappings[object_key]
                        if existing.canonical != object_canonical:
                            conflicts.append({
                                'entity': triple.object,
                                'type': triple.object_type.value,
                                'existing_canonical': existing.canonical,
                                'new_canonical': object_canonical,
                                'existing_confidence': existing.confidence,
                                'new_confidence': object_conf
                            })
                    else:
                        mapping = NormalizationMapping(
                            original=triple.object,
                            canonical=object_canonical,
                            entity_type=triple.object_type,
                            confidence=object_conf,
                            method=object_method
                        )
                        self.mappings[object_key] = mapping
                        mappings.append(mapping)
                
                # Create normalized triple (use original if normalization failed)
                normalized_triple = Triple(
                    subject=subject_canonical or triple.subject,
                    subject_type=triple.subject_type,
                    relation=triple.relation,
                    object=object_canonical or triple.object,
                    object_type=triple.object_type,
                    evidence=triple.evidence,
                    inferred=triple.inferred,
                    source=triple.source,
                    confidence=min(subject_conf, object_conf) if subject_canonical and object_canonical else 0.0,
                    section=triple.section,
                    url=triple.url,
                    timestamp=triple.timestamp
                )
                
                normalized_triples.append(normalized_triple)
                
            except Exception as e:
                logger.warning(f"Error normalizing triple: {e}")
                logger.debug(f"  Triple: {triple.subject} --[{triple.relation.value}]--> {triple.object}")
                # Include original triple if normalization fails
                normalized_triples.append(triple)
        
        self.conflicts.extend(conflicts)
        
        logger.info(f"Normalized {len(normalized_triples)} triples")
        logger.info(f"  Created {len(mappings)} mappings")
        if conflicts:
            logger.warning(f"  Found {len(conflicts)} conflicts")
        
        return normalized_triples, mappings, conflicts
    
    def get_mapping(self, original: str, entity_type: EntityType) -> Optional[NormalizationMapping]:
        """
        Get normalization mapping for an entity
        
        Args:
            original: Original entity name
            entity_type: Entity type
            
        Returns:
            NormalizationMapping or None
        """
        key = f"{original}:{entity_type.value}"
        return self.mappings.get(key)
    
    def get_conflicts(self) -> List[Dict]:
        """Get all normalization conflicts"""
        return self.conflicts
    
    def clear_mappings(self):
        """Clear all mappings (for testing or reset)"""
        self.mappings.clear()
        self.conflicts.clear()
