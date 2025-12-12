#!/usr/bin/env python3
"""
Schema Migration Script - Migrate existing Concept nodes to typed entities
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import logging

from knowledge_service.neo4j_client import Neo4jClient
from knowledge_service.schema import EntityType, RelationType
from knowledge_service.canonical_registry import get_registry

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_concepts_to_typed_entities(client: Neo4jClient, dry_run: bool = False):
    """
    Migrate Concept nodes to typed entities (Service, Component, etc.)
    
    Args:
        client: Neo4jClient instance
        dry_run: If True, only show what would be migrated without making changes
    """
    logger.info("=" * 60)
    logger.info("Schema Migration: Concepts -> Typed Entities")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)
    
    registry = get_registry()
    
    # Get all Concept nodes
    query = "MATCH (c:Concept) RETURN c.name as name, c.type as type, c.description as description LIMIT 1000"
    concepts = client.execute_query(query)
    
    logger.info(f"Found {len(concepts)} Concept nodes to migrate")
    
    if dry_run:
        logger.info("\nDry run - would migrate:")
        for concept in concepts[:10]:  # Show first 10
            logger.info(f"  {concept['name']} (type: {concept.get('type', 'unknown')})")
        if len(concepts) > 10:
            logger.info(f"  ... and {len(concepts) - 10} more")
        return
    
    migration_stats = {
        'services': 0,
        'components': 0,
        'patterns': 0,
        'concepts_kept': 0,
        'errors': 0
    }
    
    # Migrate each concept
    for concept in concepts:
        name = concept['name']
        old_type = concept.get('type', 'concept')
        description = concept.get('description', '')
        
        # Try to find canonical entity
        entity_type = None
        
        # Check services
        if registry.find_canonical(name, EntityType.SERVICE):
            entity_type = EntityType.SERVICE
            migration_stats['services'] += 1
        # Check components
        elif registry.find_canonical(name, EntityType.COMPONENT):
            entity_type = EntityType.COMPONENT
            migration_stats['components'] += 1
        # Check patterns
        elif registry.find_canonical(name, EntityType.PATTERN):
            entity_type = EntityType.PATTERN
            migration_stats['patterns'] += 1
        else:
            # Keep as Concept
            migration_stats['concepts_kept'] += 1
            continue
        
        try:
            # Create new typed node
            label = entity_type.value
            create_query = f"""
            MATCH (c:Concept {{name: $name}})
            CREATE (n:{label} {{name: $name, description: $description}})
            WITH c, n
            MATCH (c)-[r]->(target)
            CREATE (n)-[r2:{r.type}]->(target)
            SET r2 = properties(r)
            WITH c, n
            MATCH (source)-[r]->(c)
            CREATE (source)-[r2:{r.type}]->(n)
            SET r2 = properties(r)
            DELETE c
            RETURN n
            """
            
            # Simplified migration: just create new node and copy relationships
            create_node_query = f"""
            MERGE (n:{label} {{name: $name}})
            SET n.description = $description,
                n.migrated_from = 'Concept',
                n.original_type = $old_type
            RETURN n
            """
            
            client.execute_write(create_node_query, {
                'name': name,
                'description': description,
                'old_type': old_type
            })
            
            # Copy relationships (simplified - would need to handle all relationship types)
            copy_rels_query = """
            MATCH (c:Concept {name: $name})-[r]->(target)
            MATCH (n) WHERE n.name = $name AND NOT n:Concept
            CREATE (n)-[r2]->(target)
            SET r2 = properties(r)
            WITH c, n
            MATCH (source)-[r]->(c)
            CREATE (source)-[r2]->(n)
            SET r2 = properties(r)
            """
            
            # Note: This is a simplified migration. Full migration would need to:
            # 1. Handle all relationship types
            # 2. Preserve all properties
            # 3. Handle bidirectional relationships
            
        except Exception as e:
            logger.error(f"Error migrating {name}: {e}")
            migration_stats['errors'] += 1
    
    logger.info("\nMigration complete:")
    logger.info(f"  Services: {migration_stats['services']}")
    logger.info(f"  Components: {migration_stats['components']}")
    logger.info(f"  Patterns: {migration_stats['patterns']}")
    logger.info(f"  Concepts kept: {migration_stats['concepts_kept']}")
    logger.info(f"  Errors: {migration_stats['errors']}")


def migrate_relations(client: Neo4jClient, dry_run: bool = False):
    """
    Migrate RELATES_TO relationships to specific relation types
    
    Args:
        client: Neo4jClient instance
        dry_run: If True, only show what would be migrated
    """
    logger.info("=" * 60)
    logger.info("Schema Migration: RELATES_TO -> Specific Relations")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)
    
    # Get all RELATES_TO relationships
    query = """
    MATCH (a)-[r:RELATES_TO]->(b)
    RETURN a.name as subject, labels(a) as subject_labels, 
           b.name as object, labels(b) as object_labels,
           r LIMIT 1000
    """
    relations = client.execute_query(query)
    
    logger.info(f"Found {len(relations)} RELATES_TO relationships")
    
    if dry_run:
        logger.info("\nDry run - would migrate:")
        for rel in relations[:10]:
            logger.info(f"  {rel['subject']} --RELATES_TO--> {rel['object']}")
        if len(relations) > 10:
            logger.info(f"  ... and {len(relations) - 10} more")
        return
    
    # Note: Full migration would require analyzing context to determine relation type
    # This is a placeholder for the migration logic
    logger.info("Relation migration requires context analysis - not implemented in this version")


def main():
    parser = argparse.ArgumentParser(description='Migrate Neo4j schema from legacy to strict mode')
    parser.add_argument(
        '--neo4j-uri',
        type=str,
        default=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        help='Neo4j connection URI'
    )
    parser.add_argument(
        '--neo4j-user',
        type=str,
        default=os.getenv('NEO4J_USER', 'neo4j'),
        help='Neo4j username'
    )
    parser.add_argument(
        '--neo4j-password',
        type=str,
        default=os.getenv('NEO4J_PASSWORD', ''),
        help='Neo4j password'
    )
    parser.add_argument(
        '--database',
        type=str,
        default=os.getenv('NEO4J_DATABASE', 'neo4j'),
        help='Neo4j database name'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    
    args = parser.parse_args()
    
    if not args.neo4j_password:
        logger.error("Neo4j password is required")
        sys.exit(1)
    
    client = Neo4jClient(
        uri=args.neo4j_uri,
        user=args.neo4j_user,
        password=args.neo4j_password,
        database=args.database
    )
    
    try:
        with client:
            logger.info("Starting schema migration...")
            migrate_concepts_to_typed_entities(client, dry_run=args.dry_run)
            migrate_relations(client, dry_run=args.dry_run)
            logger.info("Migration complete!")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
