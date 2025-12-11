"""
Main Importer - Orchestrate the import process
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

from .neo4j_client import Neo4jClient
from .markdown_parser import MarkdownParser, Document
from .concept_extractor import ConceptExtractor, Concept
from .graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class KnowledgeImporter:
    """Main class for importing knowledge into Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, database: str = "neo4j"):
        """
        Initialize KnowledgeImporter
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            database: Database name (default: neo4j)
        """
        self.client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password, database)
        self.parser = MarkdownParser()
        self.extractor = ConceptExtractor()
        self.builder = None  # Will be initialized after connection
        
    def connect(self):
        """Connect to Neo4j"""
        self.client.connect()
        self.builder = GraphBuilder(self.client)
    
    def close(self):
        """Close Neo4j connection"""
        self.client.close()
    
    def import_directory(self, directory_path: str, clear_first: bool = False) -> dict:
        """
        Import all markdown files from a directory
        
        Args:
            directory_path: Path to directory containing markdown files
            clear_first: Whether to clear the database before importing
            
        Returns:
            Dictionary with import statistics
        """
        if not self.builder:
            self.connect()
        
        # Clear database if requested
        if clear_first:
            logger.info("Clearing existing database...")
            self.client.clear_database()
        
        # Find all markdown files
        markdown_files = self._find_markdown_files(directory_path)
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        stats = {
            'total_files': len(markdown_files),
            'successful': 0,
            'failed': 0,
            'concepts_created': 0,
            'documents_created': 0,
            'errors': []
        }
        
        # Process each file
        for i, file_path in enumerate(markdown_files, 1):
            try:
                logger.info(f"Processing [{i}/{len(markdown_files)}]: {file_path}")
                
                # Parse markdown
                document = self.parser.parse_file(file_path)
                
                # Extract concepts
                concepts = self.extractor.extract_concepts(document.content)
                stats['concepts_created'] += len(concepts)
                
                # Extract relationships
                relationships = self.extractor.extract_relationships(document.content, concepts)
                
                # Import into Neo4j
                self.builder.import_document(document, concepts, relationships)
                
                stats['documents_created'] += 1
                stats['successful'] += 1
                
                logger.info(f"  ✓ Imported: {document.title} ({len(concepts)} concepts)")
                
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Error processing {file_path}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(f"  ✗ {error_msg}")
        
        logger.info(f"\nImport complete!")
        logger.info(f"  Documents: {stats['documents_created']}")
        logger.info(f"  Concepts: {stats['concepts_created']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        
        return stats
    
    def _find_markdown_files(self, directory_path: str) -> List[str]:
        """
        Recursively find all markdown files in a directory
        
        Args:
            directory_path: Path to directory
            
        Returns:
            List of file paths
        """
        path = Path(directory_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        markdown_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    markdown_files.append(file_path)
        
        return sorted(markdown_files)
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
