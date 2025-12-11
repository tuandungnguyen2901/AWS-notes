"""
KG-Gen Extractor - Use kg-gen library for first-line text extraction and node creation
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from kg_gen import KGGen
    KG_GEN_AVAILABLE = True
    logger.info("✓ kg-gen library imported successfully")
except ImportError as e:
    KG_GEN_AVAILABLE = False
    logger.warning(f"✗ kg-gen not available: {e}. Install with: pip install kg-gen")


@dataclass
class KGGenEntity:
    """Represents an entity extracted by kg-gen"""
    name: str
    type: str
    description: Optional[str] = None


@dataclass
class KGGenRelation:
    """Represents a relation extracted by kg-gen"""
    source: str
    target: str
    relation_type: str


class KGGenExtractor:
    """Extract entities and relations using kg-gen"""
    
    def __init__(self, model: str = "google/gemini-2.0-flash-001", temperature: float = 0.0, api_key: Optional[str] = None):
        """
        Initialize KGGenExtractor
        
        Args:
            model: Model to use for kg-gen (default: google/gemini-2.0-flash-001 - cheapest option)
                   Supported Gemini models: google/gemini-2.0-flash-001 (cheapest), google/gemini-2.0-flash-exp, 
                   google/gemini-1.5-pro-002, google/gemini-2.5-pro-exp-03-25
            temperature: Temperature for generation (default: 0.0)
            api_key: API key (optional, can be set via environment variables: KG_GEN_API_KEY, GOOGLE_API_KEY, or GEMINI_API_KEY)
        """
        logger.info("=" * 60)
        logger.info("Initializing KGGenExtractor...")
        
        if not KG_GEN_AVAILABLE:
            logger.error("✗ kg-gen library is not available")
            raise ImportError("kg-gen is not installed. Install with: pip install kg-gen")
        
        logger.info(f"✓ kg-gen library is available")
        logger.info(f"  Model: {model}")
        logger.info(f"  Temperature: {temperature}")
        
        # Log API key status (without exposing the key)
        if api_key:
            api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            logger.info(f"  API Key: {api_key_preview} (provided)")
        else:
            logger.warning("  API Key: Not provided (will check environment variables)")
        
        try:
            self.kg = KGGen(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
            logger.info(f"✓ KGGenExtractor initialized successfully with model: {model}")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"✗ Failed to initialize KGGen: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.info("=" * 60)
            raise
        
        self.model = model
        self.api_key_provided = api_key is not None
    
    def health_check(self) -> bool:
        """
        Perform a health check to verify kg-gen is working
        
        Returns:
            True if kg-gen is working, False otherwise
        """
        logger.info("=" * 60)
        logger.info("KG-Gen Health Check")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  API Key provided: {self.api_key_provided}")
        
        if not KG_GEN_AVAILABLE:
            logger.error("  ✗ kg-gen library not available")
            logger.info("=" * 60)
            return False
        
        try:
            # Try a simple extraction with a test string
            test_text = "AWS CloudFront is a content delivery network."
            logger.info(f"  Testing with sample text: {test_text}")
            
            graph = self.kg.generate(
                input_data=test_text,
                context="Health check test"
            )
            
            logger.info(f"  ✓ Health check passed - kg-gen is working")
            logger.info(f"  Graph generated successfully")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Health check failed: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            import traceback
            logger.debug(f"  Traceback:\n{traceback.format_exc()}")
            logger.info("=" * 60)
            return False
    
    def extract_from_first_line(self, first_line: str, context: Optional[str] = None) -> Tuple[List[KGGenEntity], List[KGGenRelation]]:
        """
        Extract entities and relations from first line of text
        
        Args:
            first_line: First line of text to extract from
            context: Optional context for extraction
            
        Returns:
            Tuple of (entities, relations)
        """
        logger.debug("=" * 60)
        logger.debug("KG-Gen extraction started")
        
        if not first_line or not first_line.strip():
            logger.warning("  Empty first line provided, skipping kg-gen extraction")
            return [], []
        
        # Log input (truncated if too long)
        first_line_preview = first_line[:100] + "..." if len(first_line) > 100 else first_line
        logger.debug(f"  Input text: {first_line_preview}")
        logger.debug(f"  Context: {context or 'AWS knowledge documentation'}")
        
        try:
            logger.debug("  Calling kg-gen.generate()...")
            # Use kg-gen to generate knowledge graph from first line
            graph = self.kg.generate(
                input_data=first_line,
                context=context or "AWS knowledge documentation"
            )
            logger.debug(f"  ✓ kg-gen.generate() completed successfully")
            
            # Log graph structure for debugging
            logger.debug(f"  Graph object type: {type(graph)}")
            logger.debug(f"  Graph attributes: {[attr for attr in dir(graph) if not attr.startswith('_')]}")
            
            # Try to inspect the graph structure
            if hasattr(graph, '__dict__'):
                logger.debug(f"  Graph __dict__: {graph.__dict__}")
            
            # Log what attributes exist
            for attr in ['entities', 'edges', 'relations', 'nodes']:
                if hasattr(graph, attr):
                    value = getattr(graph, attr)
                    logger.debug(f"  graph.{attr}: {type(value)}, length: {len(value) if hasattr(value, '__len__') else 'N/A'}")
                    if value and hasattr(value, '__iter__'):
                        try:
                            first_item = next(iter(value))
                            logger.debug(f"    First item type: {type(first_item)}, value: {first_item}")
                        except StopIteration:
                            pass
            
            entities = []
            relations = []
            
            # Extract entities from graph
            # Handle different return formats: dict, string, or tuple
            if hasattr(graph, 'entities') and graph.entities:
                logger.debug(f"  Found {len(graph.entities)} entities in graph")
                logger.debug(f"  Entity type: {type(graph.entities)}")
                logger.debug(f"  First entity type: {type(list(graph.entities)[0]) if graph.entities else 'N/A'}")
                
                for i, entity in enumerate(graph.entities):
                    try:
                        # Handle dictionary format
                        if isinstance(entity, dict):
                            entity_obj = KGGenEntity(
                                name=entity.get('name', ''),
                                type=entity.get('type', 'entity'),
                                description=entity.get('description')
                            )
                        # Handle string format
                        elif isinstance(entity, str):
                            entity_obj = KGGenEntity(
                                name=entity,
                                type='entity',
                                description=None
                            )
                        # Handle tuple format (name, type) or (name, type, description)
                        elif isinstance(entity, (tuple, list)):
                            entity_obj = KGGenEntity(
                                name=entity[0] if len(entity) > 0 else '',
                                type=entity[1] if len(entity) > 1 else 'entity',
                                description=entity[2] if len(entity) > 2 else None
                            )
                        else:
                            # Try to convert to string
                            entity_obj = KGGenEntity(
                                name=str(entity),
                                type='entity',
                                description=None
                            )
                        
                        entities.append(entity_obj)
                        logger.debug(f"    Entity {i+1}: {entity_obj.name} ({entity_obj.type})")
                    except Exception as e:
                        logger.warning(f"    Failed to process entity {i+1}: {e}")
                        logger.debug(f"      Entity value: {entity}, type: {type(entity)}")
            else:
                logger.debug("  No entities found in graph")
            
            # Extract relations from graph
            # kg-gen may return relations in 'relations' attribute as tuples, or edges as strings (relation types)
            # Priority: relations > edges (if edges are tuples/dicts)
            
            # First, check for 'relations' attribute (most common format)
            if hasattr(graph, 'relations') and graph.relations:
                logger.debug(f"  Found {len(graph.relations)} relations in 'relations' attribute")
                logger.debug(f"  Relations type: {type(graph.relations)}")
                if graph.relations and hasattr(graph.relations, '__iter__'):
                    try:
                        first_rel = next(iter(graph.relations))
                        logger.debug(f"    First relation type: {type(first_rel)}, value: {first_rel}")
                    except StopIteration:
                        pass
                
                for i, rel in enumerate(graph.relations):
                    try:
                        # Handle tuple format: (source, relation, target) or (source, target, relation)
                        if isinstance(rel, (tuple, list)):
                            if len(rel) >= 3:
                                # Common format: (source, relation, target)
                                relation_obj = KGGenRelation(
                                    source=str(rel[0]),
                                    target=str(rel[2]),
                                    relation_type=str(rel[1])
                                )
                                relations.append(relation_obj)
                                logger.debug(f"    Relation {i+1}: {relation_obj.source} --[{relation_obj.relation_type}]--> {relation_obj.target}")
                            elif len(rel) == 2:
                                # Might be (source, target) - use default relation type
                                relation_obj = KGGenRelation(
                                    source=str(rel[0]),
                                    target=str(rel[1]),
                                    relation_type='RELATES_TO'
                                )
                                relations.append(relation_obj)
                                logger.debug(f"    Relation {i+1}: {relation_obj.source} --[{relation_obj.relation_type}]--> {relation_obj.target}")
                            else:
                                logger.warning(f"    Relation tuple has unexpected length: {len(rel)}")
                        # Handle dictionary format
                        elif isinstance(rel, dict):
                            relation_obj = KGGenRelation(
                                source=rel.get('source', rel.get('subject', '')),
                                target=rel.get('target', rel.get('object', '')),
                                relation_type=rel.get('relation', rel.get('predicate', rel.get('type', 'RELATES_TO')))
                            )
                            relations.append(relation_obj)
                            logger.debug(f"    Relation {i+1}: {relation_obj.source} --[{relation_obj.relation_type}]--> {relation_obj.target}")
                        else:
                            logger.debug(f"    Skipping relation {i+1}: unsupported format {type(rel)}")
                    except Exception as e:
                        logger.warning(f"    Failed to process relation {i+1}: {e}")
                        logger.debug(f"      Relation value: {rel}, type: {type(rel)}")
            
            # Then check 'edges' attribute (if relations weren't found or edges contain full relation data)
            if hasattr(graph, 'edges') and graph.edges:
                logger.debug(f"  Found {len(graph.edges)} edges in graph")
                logger.debug(f"  Edge type: {type(graph.edges)}")
                if graph.edges and hasattr(graph.edges, '__iter__'):
                    try:
                        first_edge = next(iter(graph.edges))
                        logger.debug(f"    First edge type: {type(first_edge)}, value: {first_edge}")
                    except StopIteration:
                        pass
                
                # If edges are strings, they're likely just relation types (not full relations)
                # We can't create relations from just types without source/target
                if graph.edges and isinstance(next(iter(graph.edges), None), str):
                    logger.debug("  Edges are strings (relation types only) - skipping, using 'relations' attribute instead")
                else:
                    # Process edges if they contain full relation data
                    for i, edge in enumerate(graph.edges):
                        try:
                            # Handle dictionary format
                            if isinstance(edge, dict):
                                relation_obj = KGGenRelation(
                                    source=edge.get('source', ''),
                                    target=edge.get('target', ''),
                                    relation_type=edge.get('relation', edge.get('type', 'RELATES_TO'))
                                )
                                relations.append(relation_obj)
                                logger.debug(f"    Edge {i+1}: {relation_obj.source} --[{relation_obj.relation_type}]--> {relation_obj.target}")
                            # Handle tuple format: (source, relation, target)
                            elif isinstance(edge, (tuple, list)):
                                if len(edge) >= 3:
                                    relation_obj = KGGenRelation(
                                        source=str(edge[0]),
                                        target=str(edge[2]),
                                        relation_type=str(edge[1])
                                    )
                                    relations.append(relation_obj)
                                    logger.debug(f"    Edge {i+1}: {relation_obj.source} --[{relation_obj.relation_type}]--> {relation_obj.target}")
                                elif len(edge) == 2:
                                    relation_obj = KGGenRelation(
                                        source=str(edge[0]),
                                        target=str(edge[1]),
                                        relation_type='RELATES_TO'
                                    )
                                    relations.append(relation_obj)
                                    logger.debug(f"    Edge {i+1}: {relation_obj.source} --[{relation_obj.relation_type}]--> {relation_obj.target}")
                                else:
                                    logger.debug(f"    Edge tuple has unexpected length: {len(edge)}")
                            # Skip string edges (they're just relation types, not full relations)
                            elif isinstance(edge, str):
                                logger.debug(f"    Skipping string edge (relation type only): {edge}")
                            else:
                                logger.debug(f"    Unsupported edge format: {type(edge)}, value: {edge}")
                        except Exception as e:
                            logger.warning(f"    Failed to process edge {i+1}: {e}")
                            logger.debug(f"      Edge value: {edge}, type: {type(edge)}")
            else:
                logger.debug("  No edges found in graph")
            
            logger.info(f"  ✓ Extracted {len(entities)} entities and {len(relations)} relations from first line")
            logger.debug("=" * 60)
            return entities, relations
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"  ✗ Error extracting with kg-gen: {e}")
            logger.error(f"  Error type: {type(e).__name__}")
            import traceback
            logger.debug(f"  Traceback:\n{traceback.format_exc()}")
            logger.error("=" * 60)
            return [], []
