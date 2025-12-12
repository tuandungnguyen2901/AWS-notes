"""
Main Importer - Orchestrate the import process
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

from .neo4j_client import Neo4jClient
from .markdown_parser import MarkdownParser, Document, Chunk
from .concept_extractor import ConceptExtractor, Concept
from .graph_builder import GraphBuilder
from .kg_gen_extractor import KGGenExtractor, KGGenEntity, KGGenRelation
from .chunk_processor import ChunkProcessor
from .schema import Triple
from .normalization_service import NormalizationService
from .validation_pipeline import ValidationPipeline
from .entity_clusterer import EntityClusterer
from .relation_normalizer import RelationNormalizer
from .merge_service import MergeService
from .triple_store import TripleStore
from .diff_extractor import DiffExtractor
from .config import ExtractionConfig, get_config

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class KnowledgeImporter:
    """Main class for importing knowledge into Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, database: str = "neo4j", use_kg_gen: bool = True, kg_gen_model: str = "google/gemini-2.0-flash-001", kg_gen_api_key: Optional[str] = None, config: Optional[ExtractionConfig] = None):
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
        
        # Configuration
        self.config = config or get_config()
        
        # New pipeline components
        self.chunk_processor = ChunkProcessor()
        self.normalization_service = None
        self.validation_pipeline = None
        self.entity_clusterer = None
        self.relation_normalizer = RelationNormalizer()
        self.merge_service = MergeService()
        self.triple_store = TripleStore()
        
        if self.config.enable_normalization:
            self.normalization_service = NormalizationService(
                similarity_threshold=self.config.similarity_threshold
            )
        
        if self.config.enable_validation:
            self.validation_pipeline = ValidationPipeline()
        
        if self.config.enable_clustering:
            self.entity_clusterer = EntityClusterer(
                similarity_threshold=self.config.similarity_threshold,
                use_hdbscan=self.config.use_hdbscan
            )
        
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
                self.kg_gen_extractor = KGGenExtractor(
                    model=kg_gen_model or self.config.kg_gen_model,
                    temperature=self.config.kg_gen_temperature,
                    api_key=api_key
                )
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
    
    def import_directory_strict(self, directory_path: str, clear_first: bool = False, incremental: bool = False) -> dict:
        """
        Import directory using strict schema mode with full pipeline
        
        Args:
            directory_path: Path to directory containing markdown files
            clear_first: Whether to clear the database before importing
            incremental: Whether to use incremental update mode
            
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
            'documents_created': 0,
            'chunks_processed': 0,
            'triples_extracted': 0,
            'triples_normalized': 0,
            'triples_validated': 0,
            'triples_merged': 0,
            'triples_stored': 0,
            'errors': []
        }
        
        all_triples = []
        
        # Process each file
        for i, file_path in enumerate(markdown_files, 1):
            try:
                logger.info(f"Processing [{i}/{len(markdown_files)}]: {file_path}")
                
                # Step 1: Parse markdown
                document = self.parser.parse_file(file_path)
                
                # Step 2: Chunk document
                chunks = self.parser.chunk_document(
                    document,
                    min_tokens=self.config.min_chunk_tokens,
                    max_tokens=self.config.max_chunk_tokens
                )
                stats['chunks_processed'] += len(chunks)
                logger.debug(f"  Chunked into {len(chunks)} chunks")
                
                # Step 3: Extract triples from chunks using kg-gen
                document_triples = []
                if self.use_kg_gen and self.kg_gen_extractor:
                    for chunk in chunks:
                        try:
                            triples = self.kg_gen_extractor.extract_from_chunk(chunk, use_strict_prompt=True)
                            document_triples.extend(triples)
                            stats['triples_extracted'] += len(triples)
                        except Exception as e:
                            logger.warning(f"  Error extracting from chunk: {e}")
                            continue
                else:
                    logger.warning("  kg-gen not available, skipping triple extraction")
                
                all_triples.extend(document_triples)
                stats['documents_created'] += 1
                stats['successful'] += 1
                
                logger.info(f"  ✓ Processed: {document.title} ({len(chunks)} chunks, {len(document_triples)} triples)")
                
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Error processing {file_path}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(f"  ✗ {error_msg}")
        
        # Step 4: Normalize entities
        if self.config.enable_normalization and self.normalization_service:
            logger.info("Normalizing entities...")
            normalized_triples, mappings, conflicts = self.normalization_service.normalize_triples(all_triples)
            stats['triples_normalized'] = len(normalized_triples)
            stats['normalization_mappings'] = len(mappings)
            stats['normalization_conflicts'] = len(conflicts)
            all_triples = normalized_triples
        
        # Step 5: Normalize relations
        logger.info("Normalizing relations...")
        for triple in all_triples:
            normalized_relation = self.relation_normalizer.normalize_triple_relation(triple)
            if normalized_relation:
                triple.relation = normalized_relation
        
        # Step 6: Validate triples
        if self.config.enable_validation and self.validation_pipeline:
            logger.info("Validating triples...")
            valid_triples, validation_report = self.validation_pipeline.validate(all_triples)
            stats['triples_validated'] = len(valid_triples)
            stats['validation_errors'] = len(validation_report.errors)
            all_triples = valid_triples
            
            if validation_report.errors:
                logger.warning(f"  Validation found {len(validation_report.errors)} errors")
        
        # Step 7: Cluster entities (if enabled)
        entity_clusters = {}
        if self.config.enable_clustering and self.entity_clusterer:
            logger.info("Clustering entities...")
            # Note: Would need embeddings here - simplified for now
            # entity_clusters = self.entity_clusterer.cluster_entities(all_triples, embeddings)
            pass
        
        # Step 8: Merge triples
        logger.info("Merging triples...")
        merged_triples = self.merge_service.merge_triples(all_triples, entity_clusters)
        stats['triples_merged'] = len(merged_triples)
        
        # Step 9: Diff extraction (if incremental)
        if incremental:
            logger.info("Extracting differences...")
            diff_extractor = DiffExtractor(self.triple_store)
            diff_result = diff_extractor.extract_diff(all_triples)
            stats['diff_new'] = len(diff_result.new_triples)
            stats['diff_updated'] = len(diff_result.updated_triples)
            stats['diff_conflicts'] = len(diff_result.conflicts)
            
            # Apply diff
            diff_stats = diff_extractor.apply_diff(diff_result)
            stats.update(diff_stats)
        else:
            # Add all triples to store
            for triple in all_triples:
                self.triple_store.add_triple(triple)
        
        # Step 10: Store in Neo4j
        logger.info("Storing triples in Neo4j...")
        try:
            # Store using new schema (use merged triples if available, otherwise use all_triples)
            triples_to_store = all_triples  # Use normalized/validated triples
            
            # Store using new schema
            self.builder.import_triples(triples_to_store)
            stats['triples_stored'] = len(triples_to_store)
            
        except Exception as e:
            logger.error(f"Error storing triples: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            stats['errors'].append(f"Storage error: {str(e)}")
        
        logger.info(f"\nImport complete!")
        logger.info(f"  Documents: {stats['documents_created']}")
        logger.info(f"  Chunks: {stats['chunks_processed']}")
        logger.info(f"  Triples extracted: {stats['triples_extracted']}")
        logger.info(f"  Triples normalized: {stats['triples_normalized']}")
        logger.info(f"  Triples validated: {stats['triples_validated']}")
        logger.info(f"  Triples merged: {stats['triples_merged']}")
        logger.info(f"  Triples stored: {stats['triples_stored']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        
        return stats
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
