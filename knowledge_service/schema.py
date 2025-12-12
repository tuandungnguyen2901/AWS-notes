"""
Schema Definition - Strict entity types, relations, and validation rules
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Set, List
import logging

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Allowed entity types in the knowledge graph"""
    SERVICE = "Service"
    COMPONENT = "Component"
    PATTERN = "Pattern"
    PILLAR = "Pillar"
    BEST_PRACTICE = "BestPractice"
    RISK = "Risk"
    MITIGATION = "Mitigation"
    METRIC = "Metric"
    ROLE = "Role"
    
    # Legacy types for backward compatibility
    CONCEPT = "Concept"
    DOCUMENT = "Document"
    SECTION = "Section"
    DOMAIN = "Domain"
    CATEGORY = "Category"


class RelationType(str, Enum):
    """Allowed relation types in the knowledge graph"""
    USES = "uses"
    IMPLEMENTS = "implements"
    ADDRESSES = "addresses"
    RECOMMENDED_BY = "recommended_by"
    AFFECTS = "affects"
    DEPENDS_ON = "depends_on"
    VIOLATES = "violates"
    EXAMPLE_OF = "example_of"
    
    # Legacy relations for backward compatibility
    CONTAINS = "CONTAINS"
    DOCUMENTS = "DOCUMENTS"
    RELATES_TO = "RELATES_TO"
    REFERENCES = "REFERENCES"
    MENTIONS = "MENTIONS"
    EXTRACTS = "EXTRACTS"


# Schema validation rules: which entity types can use which relations
SCHEMA_RULES: Dict[RelationType, Dict[str, Set[EntityType]]] = {
    RelationType.USES: {
        "subject": {EntityType.SERVICE, EntityType.COMPONENT},
        "object": {EntityType.COMPONENT, EntityType.SERVICE}
    },
    RelationType.IMPLEMENTS: {
        "subject": {EntityType.COMPONENT, EntityType.SERVICE},
        "object": {EntityType.PATTERN}
    },
    RelationType.ADDRESSES: {
        "subject": {EntityType.MITIGATION, EntityType.BEST_PRACTICE},
        "object": {EntityType.RISK}
    },
    RelationType.RECOMMENDED_BY: {
        "subject": {EntityType.BEST_PRACTICE},
        "object": {EntityType.PILLAR}
    },
    RelationType.AFFECTS: {
        "subject": {EntityType.SERVICE, EntityType.COMPONENT, EntityType.PATTERN, EntityType.BEST_PRACTICE},
        "object": {EntityType.METRIC}
    },
    RelationType.DEPENDS_ON: {
        "subject": {EntityType.SERVICE, EntityType.COMPONENT},
        "object": {EntityType.SERVICE, EntityType.COMPONENT}
    },
    RelationType.VIOLATES: {
        "subject": {EntityType.SERVICE, EntityType.COMPONENT, EntityType.PATTERN},
        "object": {EntityType.PILLAR}
    },
    RelationType.EXAMPLE_OF: {
        "subject": {EntityType.SERVICE, EntityType.COMPONENT, EntityType.PATTERN},
        "object": {EntityType.PATTERN}
    }
}


@dataclass
class Triple:
    """Represents a knowledge graph triple with full metadata"""
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str  # 'object' is a keyword, but we need it for the triple
    object_type: EntityType
    evidence: str
    inferred: bool = False
    source: Optional[str] = None
    confidence: float = 1.0
    section: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Validate types after initialization"""
        if isinstance(self.subject_type, str):
            self.subject_type = EntityType(self.subject_type)
        if isinstance(self.object_type, str):
            self.object_type = EntityType(self.object_type)
        if isinstance(self.relation, str):
            self.relation = RelationType(self.relation)
    
    def to_dict(self) -> dict:
        """Convert triple to dictionary"""
        return {
            "subject": self.subject,
            "subject_type": self.subject_type.value,
            "relation": self.relation.value,
            "object": self.object,
            "object_type": self.object_type.value,
            "evidence": self.evidence,
            "inferred": self.inferred,
            "source": self.source,
            "confidence": self.confidence,
            "section": self.section,
            "url": self.url,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Triple":
        """Create triple from dictionary"""
        return cls(
            subject=data["subject"],
            subject_type=EntityType(data["subject_type"]),
            relation=RelationType(data["relation"]),
            object=data["object"],
            object_type=EntityType(data["object_type"]),
            evidence=data.get("evidence", ""),
            inferred=data.get("inferred", False),
            source=data.get("source"),
            confidence=data.get("confidence", 1.0),
            section=data.get("section"),
            url=data.get("url"),
            timestamp=data.get("timestamp")
        )
    
    def fingerprint(self) -> str:
        """Generate a fingerprint for deduplication"""
        import hashlib
        key = f"{self.subject.lower()}|{self.relation.value}|{self.object.lower()}"
        return hashlib.md5(key.encode()).hexdigest()


def validate_relation_compatibility(relation: RelationType, subject_type: EntityType, object_type: EntityType) -> bool:
    """
    Validate that a relation is compatible with the subject and object types
    
    Args:
        relation: The relation type
        subject_type: The subject entity type
        object_type: The object entity type
        
    Returns:
        True if compatible, False otherwise
    """
    if relation not in SCHEMA_RULES:
        # Legacy relations or unknown relations - allow for backward compatibility
        return True
    
    rules = SCHEMA_RULES[relation]
    subject_allowed = rules.get("subject", set())
    object_allowed = rules.get("object", set())
    
    if subject_allowed and subject_type not in subject_allowed:
        return False
    if object_allowed and object_type not in object_allowed:
        return False
    
    return True


def get_allowed_object_types(relation: RelationType, subject_type: EntityType) -> Set[EntityType]:
    """
    Get allowed object types for a given relation and subject type
    
    Args:
        relation: The relation type
        subject_type: The subject entity type
        
    Returns:
        Set of allowed object types
    """
    if relation not in SCHEMA_RULES:
        return set()  # Unknown relation
    
    rules = SCHEMA_RULES[relation]
    subject_allowed = rules.get("subject", set())
    
    if subject_allowed and subject_type not in subject_allowed:
        return set()  # Subject type not allowed
    
    return rules.get("object", set())


def get_allowed_subject_types(relation: RelationType, object_type: EntityType) -> Set[EntityType]:
    """
    Get allowed subject types for a given relation and object type
    
    Args:
        relation: The relation type
        object_type: The object entity type
        
    Returns:
        Set of allowed subject types
    """
    if relation not in SCHEMA_RULES:
        return set()  # Unknown relation
    
    rules = SCHEMA_RULES[relation]
    object_allowed = rules.get("object", set())
    
    if object_allowed and object_type not in object_allowed:
        return set()  # Object type not allowed
    
    return rules.get("subject", set())
