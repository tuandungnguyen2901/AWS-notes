#!/usr/bin/env python3
"""
CLI interface for importing knowledge into Neo4j
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from knowledge_service import KnowledgeImporter

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_default_knowledge_dir():
    """Get default knowledge directory path"""
    # Check if knowledge directory exists
    if Path('./knowledge').exists():
        return './knowledge'
    # Fallback to domain_1 if knowledge doesn't exist
    if Path('./domain_1').exists():
        return './domain_1'
    return './knowledge'


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Import markdown knowledge files into Neo4j graph database'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import knowledge files')
    import_parser.add_argument(
        '--knowledge-dir',
        type=str,
        default=get_default_knowledge_dir(),
        help=f'Path to knowledge folder (default: {get_default_knowledge_dir()})'
    )
    import_parser.add_argument(
        '--neo4j-uri',
        type=str,
        default=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        help='Neo4j connection URI (default: from NEO4J_URI env var or bolt://localhost:7687)'
    )
    import_parser.add_argument(
        '--neo4j-user',
        type=str,
        default=os.getenv('NEO4J_USER', 'neo4j'),
        help='Neo4j username (default: from NEO4J_USER env var or neo4j)'
    )
    import_parser.add_argument(
        '--neo4j-password',
        type=str,
        default=os.getenv('NEO4J_PASSWORD', ''),
        help='Neo4j password (default: from NEO4J_PASSWORD env var)'
    )
    import_parser.add_argument(
        '--database',
        type=str,
        default=os.getenv('NEO4J_DATABASE', 'neo4j'),
        help='Neo4j database name (default: from NEO4J_DATABASE env var or neo4j)'
    )
    import_parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing graph before importing'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'import':
        # Validate password
        if not args.neo4j_password:
            logger.error("Neo4j password is required. Set NEO4J_PASSWORD env var or use --neo4j-password")
            sys.exit(1)
        
        # Validate knowledge directory
        knowledge_dir = Path(args.knowledge_dir)
        if not knowledge_dir.exists():
            logger.error(f"Knowledge directory not found: {knowledge_dir}")
            sys.exit(1)
        
        logger.info(f"Starting import from: {knowledge_dir}")
        logger.info(f"Neo4j URI: {args.neo4j_uri}")
        logger.info(f"Database: {args.database}")
        
        try:
            # Create importer
            importer = KnowledgeImporter(
                neo4j_uri=args.neo4j_uri,
                neo4j_user=args.neo4j_user,
                neo4j_password=args.neo4j_password,
                database=args.database
            )
            
            # Import knowledge
            with importer:
                stats = importer.import_directory(str(knowledge_dir), clear_first=args.clear)
            
            # Print summary
            print("\n" + "="*50)
            print("Import Summary")
            print("="*50)
            print(f"Total files processed: {stats['total_files']}")
            print(f"Successfully imported: {stats['successful']}")
            print(f"Failed: {stats['failed']}")
            print(f"Documents created: {stats['documents_created']}")
            print(f"Concepts created: {stats['concepts_created']}")
            
            if stats['errors']:
                print("\nErrors:")
                for error in stats['errors']:
                    print(f"  - {error}")
            
            print("="*50)
            
            if stats['failed'] > 0:
                sys.exit(1)
            
        except KeyboardInterrupt:
            logger.info("\nImport interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    main()
