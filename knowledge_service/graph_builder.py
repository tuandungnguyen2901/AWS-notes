"""
Graph Builder - Build and execute Cypher queries for Neo4j
Uses parameterized queries for safety and proper handling of special characters
"""

from typing import List, Dict, Optional, Tuple
from .markdown_parser import Document, Section
from .concept_extractor import Concept
import logging

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build Cypher queries for creating graph structure"""
    
    def __init__(self, neo4j_client):
        """
        Initialize GraphBuilder
        
        Args:
            neo4j_client: Neo4jClient instance
        """
        self.client = neo4j_client
    
    def create_document_node(self, document: Document) -> Tuple[str, Dict]:
        """
        Create a Document node
        
        Args:
            document: Document object
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MERGE (d:Document {file_path: $file_path})
        SET d.title = $title,
            d.content = $content,
            d.created_at = $created_at,
            d.full_content = $full_content
        RETURN d
        """
        params = {
            'file_path': document.file_path,
            'title': document.title,
            'content': document.content[:1000],  # Truncate for performance
            'created_at': document.created_at,
            'full_content': document.content
        }
        return query, params
    
    def create_concept_node(self, concept: Concept) -> Tuple[str, Dict]:
        """
        Create a Concept node
        
        Args:
            concept: Concept object
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MERGE (c:Concept {name: $name})
        SET c.type = $type,
            c.description = $description
        RETURN c
        """
        params = {
            'name': concept.name,
            'type': concept.type,
            'description': (concept.description or "")[:500]
        }
        return query, params
    
    def create_section_node(self, section: Section, document_path: str) -> Tuple[str, Dict]:
        """
        Create a Section node
        
        Args:
            section: Section object
            document_path: Path to the document
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        section_id = f"{document_path}::{section.heading}"
        
        query = """
        MERGE (s:Section {id: $id})
        SET s.heading = $heading,
            s.level = $level,
            s.content = $content,
            s.start_line = $start_line,
            s.end_line = $end_line
        RETURN s
        """
        params = {
            'id': section_id,
            'heading': section.heading,
            'level': section.level,
            'content': section.content[:1000],
            'start_line': section.start_line,
            'end_line': section.end_line
        }
        return query, params
    
    def create_documents_relationship(self, document_path: str, concept_name: str) -> Tuple[str, Dict]:
        """
        Create DOCUMENTS relationship (Document -> Concept)
        
        Args:
            document_path: Path to the document
            concept_name: Name of the concept
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MATCH (d:Document {file_path: $file_path})
        MATCH (c:Concept {name: $concept_name})
        MERGE (d)-[:DOCUMENTS]->(c)
        RETURN d, c
        """
        params = {
            'file_path': document_path,
            'concept_name': concept_name
        }
        return query, params
    
    def create_relates_to_relationship(self, source_concept: str, target_concept: str, rel_type: str = "RELATES_TO") -> Tuple[str, Dict]:
        """
        Create RELATES_TO relationship (Concept -> Concept)
        
        Args:
            source_concept: Source concept name
            target_concept: Target concept name
            rel_type: Relationship type (default: RELATES_TO)
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        # Note: Relationship types cannot be parameterized in Cypher, so we validate it
        if not rel_type.replace('_', '').isalnum():
            raise ValueError(f"Invalid relationship type: {rel_type}")
        
        query = f"""
        MATCH (c1:Concept {{name: $source}})
        MATCH (c2:Concept {{name: $target}})
        MERGE (c1)-[:{rel_type}]->(c2)
        RETURN c1, c2
        """
        params = {
            'source': source_concept,
            'target': target_concept
        }
        return query, params
    
    def create_references_relationship(self, source_path: str, target_path: str) -> Tuple[str, Dict]:
        """
        Create REFERENCES relationship (Document -> Document)
        
        Args:
            source_path: Source document path
            target_path: Target document path (may be partial)
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MATCH (d1:Document {file_path: $source_path})
        MATCH (d2:Document)
        WHERE d2.file_path CONTAINS $target_path OR d2.title CONTAINS $target_path
        MERGE (d1)-[:REFERENCES]->(d2)
        RETURN d1, d2
        """
        params = {
            'source_path': source_path,
            'target_path': target_path
        }
        return query, params
    
    def create_contains_relationship(self, document_path: str, section_id: str) -> Tuple[str, Dict]:
        """
        Create CONTAINS relationship (Document -> Section)
        
        Args:
            document_path: Path to the document
            section_id: Section ID
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MATCH (d:Document {file_path: $file_path})
        MATCH (s:Section {id: $section_id})
        MERGE (d)-[:CONTAINS]->(s)
        RETURN d, s
        """
        params = {
            'file_path': document_path,
            'section_id': section_id
        }
        return query, params
    
    def create_mentions_relationship(self, section_id: str, concept_name: str) -> Tuple[str, Dict]:
        """
        Create MENTIONS relationship (Section -> Concept)
        
        Args:
            section_id: Section ID
            concept_name: Concept name
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MATCH (s:Section {id: $section_id})
        MATCH (c:Concept {name: $concept_name})
        MERGE (s)-[:MENTIONS]->(c)
        RETURN s, c
        """
        params = {
            'section_id': section_id,
            'concept_name': concept_name
        }
        return query, params
    
    def import_document(self, document: Document, concepts: List[Concept], relationships: List[tuple]) -> None:
        """
        Import a complete document with all its relationships
        
        Args:
            document: Document object
            concepts: List of extracted concepts
            relationships: List of (source, rel_type, target) tuples
        """
        queries = []
        
        # Create document node
        queries.append(self.create_document_node(document))
        
        # Create concept nodes
        for concept in concepts:
            queries.append(self.create_concept_node(concept))
        
        # Create section nodes
        for section in document.sections:
            section_id = f"{document.file_path}::{section.heading}"
            queries.append(self.create_section_node(section, document.file_path))
            queries.append(self.create_contains_relationship(document.file_path, section_id))
            
            # Find concepts mentioned in this section
            section_concepts = [c for c in concepts if c.name.lower() in section.content.lower()]
            for concept in section_concepts:
                queries.append(self.create_mentions_relationship(section_id, concept.name))
        
        # Create document-concept relationships
        for concept in concepts:
            queries.append(self.create_documents_relationship(document.file_path, concept.name))
        
        # Create concept-concept relationships
        for source, rel_type, target in relationships:
            queries.append(self.create_relates_to_relationship(source, target, rel_type))
        
        # Create document-document references
        for ref in document.references:
            queries.append(self.create_references_relationship(document.file_path, ref))
        
        # Execute all queries in batch
        try:
            self.client.execute_batch(queries)
            logger.info(f"Imported document: {document.title}")
        except Exception as e:
            logger.error(f"Error importing document {document.title}: {e}")
            raise
