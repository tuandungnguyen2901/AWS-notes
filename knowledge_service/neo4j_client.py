"""
Neo4j Client - Handles connection and database operations
"""

from neo4j import GraphDatabase
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Client for interacting with Neo4j database"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize Neo4j client
        
        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
            database: Database name (default: neo4j)
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a write transaction
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        with self.driver.session(database=self.database) as session:
            def work(tx):
                result = tx.run(query, parameters or {})
                return [record.data() for record in result]
            return session.execute_write(work)
    
    def execute_batch(self, queries: List[tuple]) -> None:
        """
        Execute multiple queries in a single transaction
        
        Args:
            queries: List of (query, parameters) tuples
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        with self.driver.session(database=self.database) as session:
            def work(tx):
                for query, params in queries:
                    tx.run(query, params or {})
            session.execute_write(work)
    
    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        # First, get counts before deletion
        count_query = "MATCH (n) RETURN count(n) as node_count"
        rel_count_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
        
        try:
            node_count_result = self.execute_query(count_query)
            rel_count_result = self.execute_query(rel_count_query)
            node_count = node_count_result[0]['node_count'] if node_count_result else 0
            rel_count = rel_count_result[0]['rel_count'] if rel_count_result else 0
            
            logger.info(f"Found {node_count} nodes and {rel_count} relationships to delete")
        except Exception as e:
            logger.warning(f"Could not get counts before deletion: {e}")
        
        # Delete all nodes and relationships
        query = "MATCH (n) DETACH DELETE n"
        self.execute_write(query)
        logger.info("✓ All nodes and relationships deleted from database")
    
    def clear_domain(self, domain_name: str):
        """
        Clear all data related to a specific domain
        
        Args:
            domain_name: Name of the domain to clear (e.g., 'domain_1_Design_Solutions_for_Organizational_Complexity')
        """
        # First, check if domain exists and get counts
        check_query = """
        MATCH (dom:Domain {name: $domain_name})
        OPTIONAL MATCH (dom)-[:CONTAINS]->(cat:Category)
        OPTIONAL MATCH (cat)-[:CONTAINS]->(doc:Document)
        OPTIONAL MATCH (doc)-[:CONTAINS]->(sec:Section)
        RETURN 
            count(DISTINCT dom) as domain_count,
            count(DISTINCT cat) as category_count,
            count(DISTINCT doc) as document_count,
            count(DISTINCT sec) as section_count
        """
        
        try:
            result = self.execute_query(check_query, {'domain_name': domain_name})
            if result and result[0]['domain_count'] > 0:
                counts = result[0]
                logger.info(f"Found domain '{domain_name}' with:")
                logger.info(f"  - {counts['category_count']} categories")
                logger.info(f"  - {counts['document_count']} documents")
                logger.info(f"  - {counts['section_count']} sections")
            else:
                logger.warning(f"Domain '{domain_name}' not found in database")
                return
        except Exception as e:
            logger.warning(f"Could not get domain counts: {e}")
        
        # Delete in order: Sections -> Documents -> Categories -> Domain
        # Also delete related concepts and relationships
        delete_query = """
        MATCH (dom:Domain {name: $domain_name})
        OPTIONAL MATCH (dom)-[:CONTAINS]->(cat:Category)
        OPTIONAL MATCH (cat)-[:CONTAINS]->(doc:Document)
        OPTIONAL MATCH (doc)-[:CONTAINS]->(sec:Section)
        OPTIONAL MATCH (doc)-[:DOCUMENTS]->(concept:Concept)
        OPTIONAL MATCH (doc)-[:EXTRACTS]->(kgEntity:KGGenEntity)
        OPTIONAL MATCH (sec)-[:MENTIONS]->(concept2:Concept)
        
        // Delete sections first
        DETACH DELETE sec
        
        // Delete documents and their relationships
        DETACH DELETE doc
        
        // Delete categories
        DETACH DELETE cat
        
        // Delete domain
        DETACH DELETE dom
        
        // Note: Concepts and KGGenEntities are kept if they're referenced by other documents
        RETURN count(dom) as deleted_domains
        """
        
        try:
            result = self.execute_write(delete_query, {'domain_name': domain_name})
            deleted = result[0]['deleted_domains'] if result else 0
            if deleted > 0:
                logger.info(f"✓ Successfully deleted domain '{domain_name}' and all related data")
            else:
                logger.warning(f"No data was deleted for domain '{domain_name}'")
        except Exception as e:
            logger.error(f"Error deleting domain '{domain_name}': {e}")
            raise
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
