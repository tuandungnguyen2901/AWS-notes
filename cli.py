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
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all data from Neo4j database')
    clear_parser.add_argument(
        '--neo4j-uri',
        type=str,
        default=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        help='Neo4j connection URI (default: from NEO4J_URI env var or bolt://localhost:7687)'
    )
    clear_parser.add_argument(
        '--neo4j-user',
        type=str,
        default=os.getenv('NEO4J_USER', 'neo4j'),
        help='Neo4j username (default: from NEO4J_USER env var or neo4j)'
    )
    clear_parser.add_argument(
        '--neo4j-password',
        type=str,
        default=os.getenv('NEO4J_PASSWORD', ''),
        help='Neo4j password (default: from NEO4J_PASSWORD env var)'
    )
    clear_parser.add_argument(
        '--database',
        type=str,
        default=os.getenv('NEO4J_DATABASE', 'neo4j'),
        help='Neo4j database name (default: from NEO4J_DATABASE env var or neo4j)'
    )
    clear_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt (use with caution!)'
    )
    
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
    import_parser.add_argument(
        '--kg-gen-api-key',
        type=str,
        default=os.getenv('KG_GEN_API_KEY', ''),
        help='KG-Gen API key (default: from KG_GEN_API_KEY env var)'
    )
    import_parser.add_argument(
        '--kg-gen-model',
        type=str,
        default=os.getenv('KG_GEN_MODEL', 'google/gemini-2.0-flash-001'),
        help='KG-Gen model to use (default: from KG_GEN_MODEL env var or google/gemini-2.0-flash-001 - cheapest). Supported: google/gemini-2.0-flash-001 (cheapest), google/gemini-2.0-flash-exp, google/gemini-1.5-pro-002, etc.'
    )
    import_parser.add_argument(
        '--no-kg-gen',
        action='store_true',
        help='Disable kg-gen extraction'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'clear':
        # Validate password
        if not args.neo4j_password:
            logger.error("Neo4j password is required. Set NEO4J_PASSWORD env var or use --neo4j-password")
            sys.exit(1)
        
        logger.info(f"Connecting to Neo4j at {args.neo4j_uri}")
        logger.info(f"Database: {args.database}")
        
        # Confirmation prompt
        if not args.confirm:
            print("\n" + "="*60)
            print("WARNING: This will DELETE ALL DATA from the Neo4j database!")
            print("="*60)
            response = input(f"Are you sure you want to clear database '{args.database}'? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Clear operation cancelled")
                sys.exit(0)
        
        try:
            from knowledge_service.neo4j_client import Neo4jClient
            
            client = Neo4jClient(
                uri=args.neo4j_uri,
                user=args.neo4j_user,
                password=args.neo4j_password,
                database=args.database
            )
            
            with client:
                logger.info("Clearing all data from Neo4j database...")
                client.clear_database()
                logger.info("✓ Database cleared successfully")
            
        except KeyboardInterrupt:
            logger.info("\nClear operation interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to clear database: {e}", exc_info=True)
            sys.exit(1)
    
    elif args.command == 'import':
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
                database=args.database,
                use_kg_gen=not args.no_kg_gen,
                kg_gen_model=args.kg_gen_model,
                kg_gen_api_key=args.kg_gen_api_key if args.kg_gen_api_key else None
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
            if 'kg_gen_entities_created' in stats:
                print(f"KG-gen entities created: {stats['kg_gen_entities_created']}")
            
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
