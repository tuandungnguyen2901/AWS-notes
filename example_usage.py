"""
Example usage of the Knowledge Service library
"""

from knowledge_service import KnowledgeImporter
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def example_basic_import():
    """Basic example of importing knowledge"""
    # Create importer with connection details
    importer = KnowledgeImporter(
        neo4j_uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        neo4j_user=os.getenv('NEO4J_USER', 'neo4j'),
        neo4j_password=os.getenv('NEO4J_PASSWORD', 'password'),
        database=os.getenv('NEO4J_DATABASE', 'neo4j')
    )
    
    # Import knowledge folder
    with importer:
        stats = importer.import_directory('./domain_1', clear_first=False)
        
        print(f"\nImport Statistics:")
        print(f"  Documents created: {stats['documents_created']}")
        print(f"  Concepts created: {stats['concepts_created']}")
        print(f"  Successful imports: {stats['successful']}")
        print(f"  Failed imports: {stats['failed']}")


def example_clear_and_import():
    """Example of clearing database and re-importing"""
    importer = KnowledgeImporter(
        neo4j_uri='bolt://localhost:7687',
        neo4j_user='neo4j',
        neo4j_password='password'
    )
    
    with importer:
        # Clear existing data and import fresh
        stats = importer.import_directory('./domain_1', clear_first=True)
        print(f"Re-imported {stats['documents_created']} documents")


if __name__ == '__main__':
    print("Knowledge Service Example Usage")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    # example_basic_import()
    # example_clear_and_import()
    
    print("\nNote: Make sure Neo4j is running and credentials are correct!")
    print("See README.md for more information.")
