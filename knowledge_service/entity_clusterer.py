"""
Entity Clusterer - Cluster similar entities using embeddings
"""

import logging
from typing import List, Dict, Set, Optional
import numpy as np

from .schema import EntityType, Triple

logger = logging.getLogger(__name__)

# Try to import clustering libraries
try:
    from sklearn.cluster import AgglomerativeClustering
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Clustering will be disabled.")

try:
    from hdbscan import HDBSCAN
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    logger.debug("hdbscan not available. Will use agglomerative clustering if sklearn is available.")


class EntityClusterer:
    """Cluster similar entities using embeddings"""
    
    def __init__(self, similarity_threshold: float = 0.75, use_hdbscan: bool = True):
        """
        Initialize EntityClusterer
        
        Args:
            similarity_threshold: Minimum similarity for clustering (default: 0.75)
            use_hdbscan: Whether to use HDBSCAN (default: True), falls back to AgglomerativeClustering
        """
        self.similarity_threshold = similarity_threshold
        self.use_hdbscan = use_hdbscan and HDBSCAN_AVAILABLE
        
        if not SKLEARN_AVAILABLE and not HDBSCAN_AVAILABLE:
            logger.warning("No clustering libraries available. Clustering will be disabled.")
    
    def cluster_entities(self, triples: List[Triple], embeddings: Optional[Dict[str, np.ndarray]] = None) -> Dict[str, Set[str]]:
        """
        Cluster entities from triples
        
        Args:
            triples: List of triples containing entities
            embeddings: Optional precomputed embeddings dict {entity_name: embedding}
            
        Returns:
            Dictionary mapping cluster_id -> set of entity names
        """
        if not SKLEARN_AVAILABLE and not HDBSCAN_AVAILABLE:
            logger.warning("Clustering libraries not available. Returning empty clusters.")
            return {}
        
        # Extract unique entities with their types
        entities_by_type: Dict[EntityType, List[str]] = {}
        for triple in triples:
            # Cluster subjects
            if triple.subject_type not in entities_by_type:
                entities_by_type[triple.subject_type] = []
            if triple.subject not in entities_by_type[triple.subject_type]:
                entities_by_type[triple.subject_type].append(triple.subject)
            
            # Cluster objects
            if triple.object_type not in entities_by_type:
                entities_by_type[triple.object_type] = []
            if triple.object not in entities_by_type[triple.object_type]:
                entities_by_type[triple.object_type].append(triple.object)
        
        # Cluster each entity type separately
        all_clusters: Dict[str, Set[str]] = {}
        
        for entity_type, entities in entities_by_type.items():
            if len(entities) < 2:
                continue  # Need at least 2 entities to cluster
            
            logger.debug(f"Clustering {len(entities)} entities of type {entity_type.value}")
            
            # Get embeddings for these entities
            entity_embeddings = []
            entity_names = []
            
            for entity in entities:
                if embeddings and entity in embeddings:
                    entity_embeddings.append(embeddings[entity])
                    entity_names.append(entity)
            
            if len(entity_embeddings) < 2:
                continue
            
            # Perform clustering
            clusters = self._cluster_embeddings(
                np.array(entity_embeddings),
                entity_names,
                entity_type
            )
            
            # Merge into all_clusters
            for cluster_id, cluster_entities in clusters.items():
                all_clusters[cluster_id] = cluster_entities
        
        logger.info(f"Created {len(all_clusters)} clusters")
        return all_clusters
    
    def _cluster_embeddings(self, embeddings: np.ndarray, entity_names: List[str], entity_type: EntityType) -> Dict[str, Set[str]]:
        """
        Cluster embeddings using HDBSCAN or AgglomerativeClustering
        
        Args:
            embeddings: Array of embeddings (n_entities, embedding_dim)
            entity_names: List of entity names corresponding to embeddings
            entity_type: Entity type for cluster ID prefix
            
        Returns:
            Dictionary mapping cluster_id -> set of entity names
        """
        clusters: Dict[str, Set[str]] = {}
        
        if self.use_hdbscan and HDBSCAN_AVAILABLE:
            # Use HDBSCAN
            try:
                clusterer = HDBSCAN(
                    min_cluster_size=2,
                    min_samples=1,
                    metric='cosine'
                )
                cluster_labels = clusterer.fit_predict(embeddings)
                
                for i, label in enumerate(cluster_labels):
                    if label == -1:  # Noise point, skip
                        continue
                    
                    cluster_id = f"{entity_type.value}_cluster_{label}"
                    if cluster_id not in clusters:
                        clusters[cluster_id] = set()
                    clusters[cluster_id].add(entity_names[i])
                
            except Exception as e:
                logger.warning(f"HDBSCAN clustering failed: {e}. Falling back to agglomerative.")
                return self._cluster_agglomerative(embeddings, entity_names, entity_type)
        else:
            # Use AgglomerativeClustering
            return self._cluster_agglomerative(embeddings, entity_names, entity_type)
        
        return clusters
    
    def _cluster_agglomerative(self, embeddings: np.ndarray, entity_names: List[str], entity_type: EntityType) -> Dict[str, Set[str]]:
        """
        Cluster using AgglomerativeClustering
        
        Args:
            embeddings: Array of embeddings
            entity_names: List of entity names
            entity_type: Entity type
            
        Returns:
            Dictionary mapping cluster_id -> set of entity names
        """
        if not SKLEARN_AVAILABLE:
            return {}
        
        clusters: Dict[str, Set[str]] = {}
        
        try:
            # Convert similarity threshold to distance threshold
            # cosine distance = 1 - cosine similarity
            distance_threshold = 1.0 - self.similarity_threshold
            
            clusterer = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=distance_threshold,
                metric='cosine',
                linkage='average'
            )
            
            cluster_labels = clusterer.fit_predict(embeddings)
            
            # Group entities by cluster
            for i, label in enumerate(cluster_labels):
                cluster_id = f"{entity_type.value}_cluster_{label}"
                if cluster_id not in clusters:
                    clusters[cluster_id] = set()
                clusters[cluster_id].add(entity_names[i])
            
        except Exception as e:
            logger.error(f"Agglomerative clustering failed: {e}")
            return {}
        
        return clusters
    
    def get_canonical_for_cluster(self, cluster_entities: Set[str], entity_type: EntityType) -> str:
        """
        Select canonical entity name for a cluster
        
        Args:
            cluster_entities: Set of entity names in cluster
            entity_type: Entity type
            
        Returns:
            Canonical entity name (prefer shortest, most common name)
        """
        if not cluster_entities:
            return ""
        
        # Prefer shorter names (likely canonical)
        sorted_entities = sorted(cluster_entities, key=lambda x: (len(x), x.lower()))
        return sorted_entities[0]
