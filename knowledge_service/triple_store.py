"""
Triple Store - Store normalized triples with fingerprints for diff extraction
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

from .schema import Triple, EntityType, RelationType

logger = logging.getLogger(__name__)


@dataclass
class StoredTriple:
    """Represents a stored triple with evidence sources"""
    fingerprint: str
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str
    object_type: EntityType
    evidence_sources: List[Dict] = field(default_factory=list)
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    update_count: int = 0
    
    def add_evidence(self, evidence: str, source: str, section: Optional[str] = None, 
                     timestamp: Optional[str] = None, url: Optional[str] = None):
        """Add evidence source"""
        evidence_source = {
            'evidence': evidence,
            'source': source,
            'section': section,
            'timestamp': timestamp or datetime.now().isoformat(),
            'url': url
        }
        self.evidence_sources.append(evidence_source)
        self.update_count += 1
        
        if not self.first_seen:
            self.first_seen = evidence_source['timestamp']
        self.last_seen = evidence_source['timestamp']


class TripleStore:
    """In-memory store for triples with deduplication"""
    
    def __init__(self):
        self.triples: Dict[str, StoredTriple] = {}
        self.conflicts: List[Dict] = []
    
    def _create_fingerprint(self, subject: str, relation: str, object_name: str) -> str:
        """
        Create fingerprint for triple
        
        Args:
            subject: Canonical subject name
            relation: Relation name
            object_name: Canonical object name
            
        Returns:
            Fingerprint string
        """
        key = f"{subject.lower()}|{relation.lower()}|{object_name.lower()}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def add_triple(self, triple: Triple) -> Tuple[bool, Optional[str]]:
        """
        Add a triple to the store
        
        Args:
            triple: Triple to add
            
        Returns:
            Tuple of (is_new, fingerprint)
            - is_new: True if this is a new triple, False if it already exists
            - fingerprint: Fingerprint of the triple
        """
        fingerprint = self._create_fingerprint(
            triple.subject,
            triple.relation.value,
            triple.object
        )
        
        if fingerprint in self.triples:
            # Triple already exists - append evidence
            stored = self.triples[fingerprint]
            stored.add_evidence(
                evidence=triple.evidence,
                source=triple.source or "unknown",
                section=triple.section,
                timestamp=triple.timestamp,
                url=triple.url
            )
            return False, fingerprint
        else:
            # New triple
            stored = StoredTriple(
                fingerprint=fingerprint,
                subject=triple.subject,
                subject_type=triple.subject_type,
                relation=triple.relation,
                object=triple.object,
                object_type=triple.object_type
            )
            stored.add_evidence(
                evidence=triple.evidence,
                source=triple.source or "unknown",
                section=triple.section,
                timestamp=triple.timestamp,
                url=triple.url
            )
            self.triples[fingerprint] = stored
            return True, fingerprint
    
    def get_triple(self, fingerprint: str) -> Optional[StoredTriple]:
        """Get stored triple by fingerprint"""
        return self.triples.get(fingerprint)
    
    def find_triple(self, subject: str, relation: str, object_name: str) -> Optional[StoredTriple]:
        """Find triple by subject, relation, object"""
        fingerprint = self._create_fingerprint(subject, relation, object_name)
        return self.triples.get(fingerprint)
    
    def get_all_triples(self) -> List[StoredTriple]:
        """Get all stored triples"""
        return list(self.triples.values())
    
    def get_stats(self) -> Dict:
        """Get statistics about stored triples"""
        total_evidence = sum(len(t.evidence_sources) for t in self.triples.values())
        return {
            'total_triples': len(self.triples),
            'total_evidence_sources': total_evidence,
            'avg_evidence_per_triple': total_evidence / len(self.triples) if self.triples else 0,
            'conflicts': len(self.conflicts)
        }
    
    def clear(self):
        """Clear all stored triples"""
        self.triples.clear()
        self.conflicts.clear()
