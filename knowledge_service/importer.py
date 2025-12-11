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
from .kg_gen_extractor import KGGenExtractor, KGGenEntity, KGGenRelation

logger = logging.getLogger(__name__)


class KnowledgeImporter:
    """Main class for importing knowledge into Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, database: str = "neo4j", use_kg_gen: bool = True, kg_gen_model: str = "google/gemini-1.5-pro-002", kg_gen_api_key: Optional[str] = None):
        """
        Initialize KnowledgeImporter
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            database: Database name (default: neo4j)
            use_kg_gen: Whether to use kg-gen for first-line extraction (default: True)
            kg_gen_model: Model to use for kg-gen (default: google/gemini-2.0-flash-001 - cheapest option)
            kg_gen_api_key: API key for kg-gen (optional, can be set via environment variable KG_GEN_API_KEY or GOOGLE_API_KEY)
        """
        import os
        
        self.client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password, database)
        self.parser = MarkdownParser()
        self.extractor = ConceptExtractor()
        self.builder = None  # Will be initialized after connection
        
        # Initialize kg-gen extractor if requested
        self.use_kg_gen = use_kg_gen
        self.kg_gen_extractor = None
        
        logger.info("=" * 60)
        logger.info("KG-Gen Configuration Check")
        logger.info(f"  use_kg_gen flag: {use_kg_gen}")
        
        if use_kg_gen:
            # Check for API key in environment variables
            api_key = kg_gen_api_key or os.getenv('KG_GEN_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            
            if api_key:
                api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
                logger.info(f"  ✓ API key found: {api_key_preview}")
            else:
                logger.warning("  ✗ No API key found in arguments or environment variables")
                logger.warning("    Checked: KG_GEN_API_KEY, GOOGLE_API_KEY, GEMINI_API_KEY")
            
            logger.info(f"  Model: {kg_gen_model}")
            
            try:
                logger.info("  Attempting to initialize KGGenExtractor...")
                self.kg_gen_extractor = KGGenExtractor(model=kg_gen_model, api_key=api_key)
                logger.info("  ✓ KG-gen extractor initialized successfully")
                
                # Optional: Perform a health check (can be disabled for faster startup)
                logger.info("  Performing health check...")
                if self.kg_gen_extractor.health_check():
                    logger.info("  ✓ KG-gen is ready to use")
                else:
                    logger.warning("  ⚠ KG-gen health check failed, but continuing...")
                
                logger.info("=" * 60)
            except ImportError as e:
                logger.error("  ✗ kg-gen library not available")
                logger.error(f"    Error: {e}")
                logger.warning("  Continuing without kg-gen...")
                logger.info("=" * 60)
                self.use_kg_gen = False
            except Exception as e:
                logger.error("  ✗ Failed to initialize kg-gen")
                logger.error(f"    Error: {e}")
                logger.error(f"    Error type: {type(e).__name__}")
                import traceback
                logger.debug(f"    Traceback:\n{traceback.format_exc()}")
                logger.warning("  Continuing without kg-gen...")
                logger.info("=" * 60)
                self.use_kg_gen = False
        else:
            logger.info("  kg-gen is disabled (use_kg_gen=False)")
            logger.info("=" * 60)
        
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
            'kg_gen_entities_created': 0,
            'documents_created': 0,
            'errors': []
        }
        
        # Process each file
        for i, file_path in enumerate(markdown_files, 1):
            try:
                logger.info(f"Processing [{i}/{len(markdown_files)}]: {file_path}")
                
                # Parse markdown
                document = self.parser.parse_file(file_path)
                
                # Extract concepts using rule-based extractor
                concepts = self.extractor.extract_concepts(document.content)
                stats['concepts_created'] += len(concepts)
                
                # Extract relationships
                relationships = self.extractor.extract_relationships(document.content, concepts)
                
                # Extract first line and use kg-gen if enabled
                kg_gen_entities = []
                kg_gen_relations = []
                if self.use_kg_gen:
                    if self.kg_gen_extractor:
                        logger.debug(f"  Using kg-gen extractor for document: {document.title}")
                        first_line = self.parser.extract_first_line(document.content)
                        if first_line:
                            logger.debug(f"  First line extracted: {first_line[:80]}...")
                            try:
                                entities, relations = self.kg_gen_extractor.extract_from_first_line(
                                    first_line,
                                    context=f"Document: {document.title}"
                                )
                                kg_gen_entities = entities
                                kg_gen_relations = relations
                                stats['kg_gen_entities_created'] += len(kg_gen_entities)
                                logger.info(f"  ✓ kg-gen: {len(kg_gen_entities)} entities, {len(kg_gen_relations)} relations")
                            except Exception as e:
                                logger.error(f"  ✗ kg-gen extraction failed: {e}")
                                logger.error(f"    Error type: {type(e).__name__}")
                                import traceback
                                logger.debug(f"    Traceback:\n{traceback.format_exc()}")
                        else:
                            logger.debug("  No first line extracted, skipping kg-gen")
                    else:
                        logger.warning("  kg-gen is enabled but extractor is not initialized")
                else:
                    logger.debug("  kg-gen is disabled for this import")
                
                # Import into Neo4j
                self.builder.import_document(document, concepts, relationships, kg_gen_entities, kg_gen_relations)
                
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
        if self.use_kg_gen:
            logger.info(f"  KG-gen Entities: {stats['kg_gen_entities_created']}")
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
