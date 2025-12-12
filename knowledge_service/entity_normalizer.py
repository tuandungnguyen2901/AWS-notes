"""
Entity Normalizer - Normalize entities using rules and semantic matching
"""

import re
import logging
from typing import Optional, Dict, Tuple
import numpy as np

from .schema import EntityType
from .canonical_registry import get_registry, CanonicalEntity

logger = logging.getLogger(__name__)

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Semantic matching will be disabled.")


class EntityNormalizer:
    """Normalize entity names to canonical forms"""
    
    def __init__(self, similarity_threshold: float = 0.75, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize EntityNormalizer
        
        Args:
            similarity_threshold: Minimum cosine similarity for semantic matching (default: 0.75)
            embedding_model: Sentence transformer model name (default: all-MiniLM-L6-v2)
        """
        self.registry = get_registry()
        self.similarity_threshold = similarity_threshold
        
        # Embedding model and cache
        self.embedding_model = None
        self.canonical_embeddings: Dict[str, np.ndarray] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {embedding_model}")
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info("✓ Embedding model loaded successfully")
                self._precompute_canonical_embeddings()
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                logger.warning("  Semantic matching will be disabled")
                self.embedding_model = None
        else:
            logger.warning("sentence-transformers not available. Using rule-based normalization only.")
    
    def _precompute_canonical_embeddings(self):
        """Precompute embeddings for all canonical entities"""
        if not self.embedding_model:
            return
        
        logger.info("Precomputing embeddings for canonical entities...")
        
        registries = [
            (self.registry.services, EntityType.SERVICE),
            (self.registry.components, EntityType.COMPONENT),
            (self.registry.patterns, EntityType.PATTERN),
            (self.registry.pillars, EntityType.PILLAR),
            (self.registry.best_practices, EntityType.BEST_PRACTICE),
            (self.registry.risks, EntityType.RISK),
            (self.registry.mitigations, EntityType.MITIGATION),
            (self.registry.metrics, EntityType.METRIC),
            (self.registry.roles, EntityType.ROLE)
        ]
        
        texts_to_embed = []
        keys = []
        
        for registry, entity_type in registries:
            for canonical_name, entity in registry.items():
                # Create text: name + description
                text = canonical_name
                if entity.description:
                    text += f". {entity.description}"
                
                texts_to_embed.append(text)
                keys.append((canonical_name, entity_type))
        
        if texts_to_embed:
            embeddings = self.embedding_model.encode(texts_to_embed, show_progress_bar=False)
            
            for i, (canonical_name, entity_type) in enumerate(keys):
                key = f"{canonical_name}:{entity_type.value}"
                self.canonical_embeddings[key] = embeddings[i]
        
        logger.info(f"✓ Precomputed embeddings for {len(self.canonical_embeddings)} canonical entities")
    
    def normalize(self, entity_name: str, entity_type: EntityType) -> Tuple[Optional[str], float, str]:
        """
        Normalize an entity name to canonical form
        
        Args:
            entity_name: Entity name to normalize
            entity_type: Expected entity type
            
        Returns:
            Tuple of (canonical_name, confidence, method)
            - canonical_name: Normalized name or None if not found
            - confidence: Confidence score (0.0 to 1.0)
            - method: Normalization method used ("exact", "alias", "semantic", "none")
        """
        if not entity_name or not entity_name.strip():
            return None, 0.0, "none"
        
        entity_name = entity_name.strip()
        
        # Step A: Simple rule-based normalization
        normalized = self._normalize_rules(entity_name, entity_type)
        if normalized:
            return normalized, 1.0, "exact"
        
        # Step B: Semantic matching (if embeddings available)
        if self.embedding_model:
            normalized, confidence = self._normalize_semantic(entity_name, entity_type)
            if normalized and confidence >= self.similarity_threshold:
                return normalized, confidence, "semantic"
        
        # Not found
        return None, 0.0, "none"
    
    def _normalize_rules(self, entity_name: str, entity_type: EntityType) -> Optional[str]:
        """
        Step A: Simple rule-based normalization
        
        Args:
            entity_name: Entity name to normalize
            entity_type: Expected entity type
            
        Returns:
            Canonical name if found, None otherwise
        """
        # Lowercase and strip
        normalized = entity_name.lower().strip()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(aws|amazon)\s+', '', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+(service|aws|amazon)$', '', normalized, flags=re.IGNORECASE)
        
        # Try direct lookup
        canonical = self.registry.find_canonical(normalized, entity_type)
        if canonical:
            return canonical
        
        # Try without entity type filter
        canonical = self.registry.find_canonical(normalized, None)
        if canonical:
            # Verify entity type matches
            entity_obj = None
            if entity_type == EntityType.SERVICE and canonical in self.registry.services:
                entity_obj = self.registry.services[canonical]
            elif entity_type == EntityType.COMPONENT and canonical in self.registry.components:
                entity_obj = self.registry.components[canonical]
            elif entity_type == EntityType.PATTERN and canonical in self.registry.patterns:
                entity_obj = self.registry.patterns[canonical]
            elif entity_type == EntityType.PILLAR and canonical in self.registry.pillars:
                entity_obj = self.registry.pillars[canonical]
            
            if entity_obj and entity_obj.entity_type == entity_type:
                return canonical
        
        # Handle common variations
        # Remove "bucket", "instance", etc. suffixes for services
        if entity_type == EntityType.SERVICE:
            for suffix in [' bucket', ' instance', ' volume', ' gateway', ' endpoint']:
                if normalized.endswith(suffix):
                    candidate = normalized[:-len(suffix)].strip()
                    canonical = self.registry.find_canonical(candidate, entity_type)
                    if canonical:
                        return canonical
        
        return None
    
    def _normalize_semantic(self, entity_name: str, entity_type: EntityType) -> Tuple[Optional[str], float]:
        """
        Step B: Semantic matching using embeddings
        
        Args:
            entity_name: Entity name to normalize
            entity_type: Expected entity type
            
        Returns:
            Tuple of (canonical_name, similarity_score)
        """
        if not self.embedding_model:
            return None, 0.0
        
        # Get or compute embedding for entity
        if entity_name in self.embedding_cache:
            entity_embedding = self.embedding_cache[entity_name]
        else:
            entity_embedding = self.embedding_model.encode([entity_name])[0]
            self.embedding_cache[entity_name] = entity_embedding
        
        # Find best matching canonical entity
        best_match = None
        best_similarity = 0.0
        
        # Filter canonical embeddings by entity type
        for key, canonical_embedding in self.canonical_embeddings.items():
            canonical_name, canonical_type_str = key.rsplit(':', 1)
            canonical_type = EntityType(canonical_type_str)
            
            # Only compare with same entity type
            if canonical_type != entity_type:
                continue
            
            # Calculate cosine similarity
            similarity = float(np.dot(entity_embedding, canonical_embedding) / 
                             (np.linalg.norm(entity_embedding) * np.linalg.norm(canonical_embedding)))
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = canonical_name
        
        if best_similarity >= self.similarity_threshold:
            return best_match, best_similarity
        
        return None, best_similarity
    
    def normalize_triple_entities(self, triple) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalize both subject and object in a triple
        
        Args:
            triple: Triple object
            
        Returns:
            Tuple of (normalized_subject, normalized_object)
        """
        subject_canonical, _, _ = self.normalize(triple.subject, triple.subject_type)
        object_canonical, _, _ = self.normalize(triple.object, triple.object_type)
        
        return subject_canonical, object_canonical


# Global normalizer instance
_normalizer_instance: Optional[EntityNormalizer] = None


def get_normalizer(similarity_threshold: float = 0.75) -> EntityNormalizer:
    """Get the global entity normalizer instance"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = EntityNormalizer(similarity_threshold=similarity_threshold)
    return _normalizer_instance
