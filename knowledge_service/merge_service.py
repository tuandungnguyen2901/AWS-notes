"""
Merge Service - Merge clustered entities and aggregate evidence
"""

import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .schema import Triple, EntityType

logger = logging.getLogger(__name__)


@dataclass
class EvidenceSource:
    """Represents a source of evidence for a triple"""
    source: str
    section: Optional[str] = None
    score: float = 1.0
    timestamp: Optional[str] = None
    url: Optional[str] = None


@dataclass
class MergedTriple:
    """Represents a merged triple with aggregated evidence"""
    subject: str
    subject_type: EntityType
    relation: str
    object: str
    object_type: EntityType
    evidence_sources: List[EvidenceSource] = field(default_factory=list)
    inferred_count: int = 0
    total_count: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    conflicts: List[Dict] = field(default_factory=list)
    
    def add_evidence(self, triple: Triple):
        """Add evidence from a triple"""
        self.total_count += 1
        if triple.inferred:
            self.inferred_count += 1
        
        evidence_source = EvidenceSource(
            source=triple.source or "unknown",
            section=triple.section,
            score=triple.confidence,
            timestamp=triple.timestamp or datetime.now().isoformat(),
            url=triple.url
        )
        
        self.evidence_sources.append(evidence_source)
        
        # Update timestamps
        if not self.first_seen:
            self.first_seen = evidence_source.timestamp
        self.last_seen = evidence_source.timestamp


class MergeService:
    """Service to merge clustered entities and aggregate evidence"""
    
    def __init__(self):
        self.merged_triples: Dict[str, MergedTriple] = {}
    
    def merge_triples(self, triples: List[Triple], entity_clusters: Optional[Dict[str, Set[str]]] = None) -> List[MergedTriple]:
        """
        Merge triples, applying entity clustering if provided
        
        Args:
            triples: List of triples to merge
            entity_clusters: Optional dictionary mapping cluster_id -> set of entity names
            
        Returns:
            List of merged triples
        """
        logger.info(f"Merging {len(triples)} triples...")
        
        # Build entity mapping from clusters
        entity_to_canonical: Dict[str, str] = {}
        if entity_clusters:
            for cluster_id, cluster_entities in entity_clusters.items():
                # Select canonical entity (shortest name)
                canonical = min(cluster_entities, key=lambda x: (len(x), x.lower()))
                for entity in cluster_entities:
                    if entity != canonical:
                        entity_to_canonical[entity] = canonical
        
        # Merge triples
        for triple in triples:
            # Apply entity clustering
            subject_canonical = entity_to_canonical.get(triple.subject, triple.subject)
            object_canonical = entity_to_canonical.get(triple.object, triple.object)
            
            # Create fingerprint for deduplication
            fingerprint = self._create_fingerprint(
                subject_canonical,
                triple.relation.value,
                object_canonical
            )
            
            # Check for conflicts (same fingerprint but different evidence)
            if fingerprint in self.merged_triples:
                merged = self.merged_triples[fingerprint]
                
                # Check if this is a conflict (contradictory evidence)
                # For now, we'll just aggregate all evidence
                # Conflicts can be detected later by analyzing evidence
                merged.add_evidence(triple)
            else:
                # Create new merged triple
                merged = MergedTriple(
                    subject=subject_canonical,
                    subject_type=triple.subject_type,
                    relation=triple.relation.value,
                    object=object_canonical,
                    object_type=triple.object_type
                )
                merged.add_evidence(triple)
                self.merged_triples[fingerprint] = merged
        
        merged_list = list(self.merged_triples.values())
        
        logger.info(f"Merged into {len(merged_list)} unique triples")
        logger.info(f"  Average evidence sources per triple: {sum(len(m.evidence_sources) for m in merged_list) / len(merged_list) if merged_list else 0:.1f}")
        
        return merged_list
    
    def _create_fingerprint(self, subject: str, relation: str, object_name: str) -> str:
        """
        Create fingerprint for triple deduplication
        
        Args:
            subject: Subject entity name
            relation: Relation name
            object_name: Object entity name
            
        Returns:
            Fingerprint string
        """
        import hashlib
        key = f"{subject.lower()}|{relation.lower()}|{object_name.lower()}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def detect_conflicts(self, merged_triples: List[MergedTriple]) -> List[Dict]:
        """
        Detect conflicts in merged triples
        
        Args:
            merged_triples: List of merged triples
            
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        for merged in merged_triples:
            # Check for contradictory evidence
            # This is a simplified check - in practice, you'd analyze evidence text
            if merged.inferred_count > 0 and merged.total_count > merged.inferred_count:
                # Mix of inferred and explicit - potential conflict
                conflicts.append({
                    'triple': f"{merged.subject} --[{merged.relation}]--> {merged.object}",
                    'type': 'mixed_inference',
                    'inferred_count': merged.inferred_count,
                    'explicit_count': merged.total_count - merged.inferred_count,
                    'evidence_sources': len(merged.evidence_sources)
                })
        
        if conflicts:
            logger.warning(f"Detected {len(conflicts)} potential conflicts")
        
        return conflicts
    
    def get_merged_triple(self, fingerprint: str) -> Optional[MergedTriple]:
        """Get merged triple by fingerprint"""
        return self.merged_triples.get(fingerprint)
    
    def clear(self):
        """Clear all merged triples"""
        self.merged_triples.clear()
