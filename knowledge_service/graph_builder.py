"""
Graph Builder - Build and execute Cypher queries for Neo4j
Uses parameterized queries for safety and proper handling of special characters
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from .markdown_parser import Document, Section
from .concept_extractor import Concept
from .kg_gen_extractor import KGGenEntity, KGGenRelation
from .schema import Triple, EntityType, RelationType
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
    
    def parse_folder_structure(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse folder structure to extract domain and category
        
        Args:
            file_path: Path to the document (e.g., "domain_1/network_connecting_strategies/AWS_PrivateLink.md")
            
        Returns:
            Tuple of (domain_name, category_name) or (None, None) if structure doesn't match
        """
        path_parts = Path(file_path).parts
        
        # Expected structure: domain_X/category_name/document.md
        if len(path_parts) >= 2:
            domain_name = path_parts[0]  # e.g., "domain_1"
            category_name = path_parts[1]  # e.g., "network_connecting_strategies"
            return domain_name, category_name
        
        return None, None
    
    def create_domain_node(self, domain_name: str) -> Tuple[str, Dict]:
        """
        Create a Domain node
        
        Args:
            domain_name: Name of the domain (e.g., "domain_1")
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MERGE (dom:Domain {name: $name})
        RETURN dom
        """
        params = {
            'name': domain_name
        }
        return query, params
    
    def create_category_node(self, category_name: str, domain_name: str) -> Tuple[str, Dict]:
        """
        Create a Category node
        
        Args:
            category_name: Name of the category (e.g., "network_connecting_strategies")
            domain_name: Name of the parent domain
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        # Use domain_name:category_name as unique identifier
        category_id = f"{domain_name}:{category_name}"
        
        query = """
        MERGE (cat:Category {id: $id})
        SET cat.name = $name,
            cat.domain = $domain
        RETURN cat
        """
        params = {
            'id': category_id,
            'name': category_name,
            'domain': domain_name
        }
        return query, params
    
    def create_domain_category_relationship(self, domain_name: str, category_name: str) -> Tuple[str, Dict]:
        """
        Create CONTAINS relationship (Domain -> Category)
        
        Args:
            domain_name: Name of the domain
            category_name: Name of the category
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        category_id = f"{domain_name}:{category_name}"
        
        query = """
        MATCH (dom:Domain {name: $domain_name})
        MATCH (cat:Category {id: $category_id})
        MERGE (dom)-[:CONTAINS]->(cat)
        RETURN dom, cat
        """
        params = {
            'domain_name': domain_name,
            'category_id': category_id
        }
        return query, params
    
    def create_category_document_relationship(self, category_name: str, domain_name: str, document_path: str) -> Tuple[str, Dict]:
        """
        Create CONTAINS relationship (Category -> Document)
        
        Args:
            category_name: Name of the category
            domain_name: Name of the domain
            document_path: Path to the document
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        category_id = f"{domain_name}:{category_name}"
        
        query = """
        MATCH (cat:Category {id: $category_id})
        MATCH (d:Document {file_path: $file_path})
        MERGE (cat)-[:CONTAINS]->(d)
        RETURN cat, d
        """
        params = {
            'category_id': category_id,
            'file_path': document_path
        }
        return query, params
    
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
    
    def create_kg_gen_entity_node(self, entity: KGGenEntity, document_path: str) -> Tuple[str, Dict]:
        """
        Create a KGGenEntity node (from kg-gen extraction)
        
        Args:
            entity: KGGenEntity object
            document_path: Path to the document that contains this entity
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MERGE (e:KGGenEntity {name: $name})
        SET e.type = $type,
            e.description = $description,
            e.source_document = $source_document
        RETURN e
        """
        params = {
            'name': entity.name,
            'type': entity.type,
            'description': (entity.description or "")[:500],
            'source_document': document_path
        }
        return query, params
    
    def create_kg_gen_relation(self, relation: KGGenRelation) -> Tuple[str, Dict]:
        """
        Create a relationship from kg-gen extraction
        
        Args:
            relation: KGGenRelation object
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        # Validate relationship type
        rel_type = relation.relation_type.replace(' ', '_').upper()
        if not rel_type.replace('_', '').isalnum():
            rel_type = "RELATES_TO"
        
        query = f"""
        MATCH (e1:KGGenEntity {{name: $source}})
        MATCH (e2:KGGenEntity {{name: $target}})
        MERGE (e1)-[:{rel_type}]->(e2)
        RETURN e1, e2
        """
        params = {
            'source': relation.source,
            'target': relation.target
        }
        return query, params
    
    def create_document_kg_gen_relationship(self, document_path: str, entity_name: str) -> Tuple[str, Dict]:
        """
        Create relationship between Document and KGGenEntity
        
        Args:
            document_path: Path to the document
            entity_name: Name of the kg-gen entity
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MATCH (d:Document {file_path: $file_path})
        MATCH (e:KGGenEntity {name: $entity_name})
        MERGE (d)-[:EXTRACTS]->(e)
        RETURN d, e
        """
        params = {
            'file_path': document_path,
            'entity_name': entity_name
        }
        return query, params
    
    # =====================================================================
    # New Schema Methods - Entity Types
    # =====================================================================
    
    def create_service_node(self, service_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Service node"""
        query = """
        MERGE (s:Service {name: $name})
        SET s.description = $description
        RETURN s
        """
        params = {
            'name': service_name,
            'description': description or ""
        }
        return query, params
    
    def create_component_node(self, component_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Component node"""
        query = """
        MERGE (c:Component {name: $name})
        SET c.description = $description
        RETURN c
        """
        params = {
            'name': component_name,
            'description': description or ""
        }
        return query, params
    
    def create_pattern_node(self, pattern_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Pattern node"""
        query = """
        MERGE (p:Pattern {name: $name})
        SET p.description = $description
        RETURN p
        """
        params = {
            'name': pattern_name,
            'description': description or ""
        }
        return query, params
    
    def create_pillar_node(self, pillar_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Pillar node"""
        query = """
        MERGE (p:Pillar {name: $name})
        SET p.description = $description
        RETURN p
        """
        params = {
            'name': pillar_name,
            'description': description or ""
        }
        return query, params
    
    def create_best_practice_node(self, practice_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a BestPractice node"""
        query = """
        MERGE (bp:BestPractice {name: $name})
        SET bp.description = $description
        RETURN bp
        """
        params = {
            'name': practice_name,
            'description': description or ""
        }
        return query, params
    
    def create_risk_node(self, risk_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Risk node"""
        query = """
        MERGE (r:Risk {name: $name})
        SET r.description = $description
        RETURN r
        """
        params = {
            'name': risk_name,
            'description': description or ""
        }
        return query, params
    
    def create_mitigation_node(self, mitigation_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Mitigation node"""
        query = """
        MERGE (m:Mitigation {name: $name})
        SET m.description = $description
        RETURN m
        """
        params = {
            'name': mitigation_name,
            'description': description or ""
        }
        return query, params
    
    def create_metric_node(self, metric_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Metric node"""
        query = """
        MERGE (m:Metric {name: $name})
        SET m.description = $description
        RETURN m
        """
        params = {
            'name': metric_name,
            'description': description or ""
        }
        return query, params
    
    def create_role_node(self, role_name: str, description: Optional[str] = None) -> Tuple[str, Dict]:
        """Create a Role node"""
        query = """
        MERGE (r:Role {name: $name})
        SET r.description = $description
        RETURN r
        """
        params = {
            'name': role_name,
            'description': description or ""
        }
        return query, params
    
    def create_typed_entity_node(self, entity_name: str, entity_type: EntityType, description: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Create a typed entity node based on entity type
        
        Args:
            entity_name: Entity name
            entity_type: Entity type
            description: Optional description
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        type_map = {
            EntityType.SERVICE: self.create_service_node,
            EntityType.COMPONENT: self.create_component_node,
            EntityType.PATTERN: self.create_pattern_node,
            EntityType.PILLAR: self.create_pillar_node,
            EntityType.BEST_PRACTICE: self.create_best_practice_node,
            EntityType.RISK: self.create_risk_node,
            EntityType.MITIGATION: self.create_mitigation_node,
            EntityType.METRIC: self.create_metric_node,
            EntityType.ROLE: self.create_role_node
        }
        
        creator = type_map.get(entity_type)
        if creator:
            return creator(entity_name, description)
        else:
            # Fallback to Concept node for unknown types
            return self.create_concept_node(Concept(name=entity_name, type=entity_type.value, description=description))
    
    # =====================================================================
    # New Schema Methods - Relations
    # =====================================================================
    
    def create_uses_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create USES relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.USES, object_name, object_type, evidence)
    
    def create_implements_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create IMPLEMENTS relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.IMPLEMENTS, object_name, object_type, evidence)
    
    def create_addresses_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create ADDRESSES relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.ADDRESSES, object_name, object_type, evidence)
    
    def create_recommended_by_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create RECOMMENDED_BY relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.RECOMMENDED_BY, object_name, object_type, evidence)
    
    def create_affects_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create AFFECTS relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.AFFECTS, object_name, object_type, evidence)
    
    def create_depends_on_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create DEPENDS_ON relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.DEPENDS_ON, object_name, object_type, evidence)
    
    def create_violates_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create VIOLATES relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.VIOLATES, object_name, object_type, evidence)
    
    def create_example_of_relationship(self, subject_name: str, subject_type: EntityType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """Create EXAMPLE_OF relationship"""
        return self._create_typed_relationship(subject_name, subject_type, RelationType.EXAMPLE_OF, object_name, object_type, evidence)
    
    def _create_typed_relationship(self, subject_name: str, subject_type: EntityType, relation: RelationType, object_name: str, object_type: EntityType, evidence: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Create a typed relationship between entities
        
        Args:
            subject_name: Subject entity name
            subject_type: Subject entity type
            relation: Relation type
            object_name: Object entity name
            object_type: Object entity type
            evidence: Optional evidence text
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        # Get node labels
        subject_label = self._entity_type_to_label(subject_type)
        object_label = self._entity_type_to_label(object_type)
        
        # Validate relation type (Cypher doesn't allow parameterized relationship types)
        rel_type = relation.value.upper().replace(' ', '_')
        if not rel_type.replace('_', '').isalnum():
            raise ValueError(f"Invalid relationship type: {rel_type}")
        
        query = f"""
        MATCH (s:{subject_label} {{name: $subject_name}})
        MATCH (o:{object_label} {{name: $object_name}})
        MERGE (s)-[r:{rel_type}]->(o)
        SET r.evidence = CASE 
            WHEN r.evidence IS NULL THEN $evidence
            ELSE r.evidence + ' | ' + $evidence
        END
        RETURN s, r, o
        """
        
        params = {
            'subject_name': subject_name,
            'object_name': object_name,
            'evidence': evidence or ''
        }
        
        return query, params
    
    def _entity_type_to_label(self, entity_type: EntityType) -> str:
        """Convert EntityType to Neo4j label"""
        type_to_label = {
            EntityType.SERVICE: "Service",
            EntityType.COMPONENT: "Component",
            EntityType.PATTERN: "Pattern",
            EntityType.PILLAR: "Pillar",
            EntityType.BEST_PRACTICE: "BestPractice",
            EntityType.RISK: "Risk",
            EntityType.MITIGATION: "Mitigation",
            EntityType.METRIC: "Metric",
            EntityType.ROLE: "Role",
            EntityType.CONCEPT: "Concept",
            EntityType.DOCUMENT: "Document",
            EntityType.SECTION: "Section",
            EntityType.DOMAIN: "Domain",
            EntityType.CATEGORY: "Category"
        }
        return type_to_label.get(entity_type, "Concept")
    
    def import_triples(self, triples: List[Triple]) -> None:
        """
        Import triples using new schema
        
        Args:
            triples: List of Triple objects to import
        """
        queries = []
        
        for triple in triples:
            # Create subject node
            queries.append(self.create_typed_entity_node(
                triple.subject,
                triple.subject_type,
                None  # Description not in Triple, could be enhanced
            ))
            
            # Create object node
            queries.append(self.create_typed_entity_node(
                triple.object,
                triple.object_type,
                None
            ))
            
            # Create relationship
            queries.append(self._create_typed_relationship(
                triple.subject,
                triple.subject_type,
                triple.relation,
                triple.object,
                triple.object_type,
                triple.evidence
            ))
        
        # Execute all queries in batch
        try:
            self.client.execute_batch(queries)
            logger.info(f"Imported {len(triples)} triples")
        except Exception as e:
            logger.error(f"Error importing triples: {e}")
            raise
    
    def import_document(self, document: Document, concepts: List[Concept], relationships: List[tuple], kg_gen_entities: Optional[List[KGGenEntity]] = None, kg_gen_relations: Optional[List[KGGenRelation]] = None) -> None:
        """
        Import a complete document with all its relationships
        
        Args:
            document: Document object
            concepts: List of extracted concepts
            relationships: List of (source, rel_type, target) tuples
            kg_gen_entities: Optional list of kg-gen extracted entities
            kg_gen_relations: Optional list of kg-gen extracted relations
        """
        queries = []
        
        # Parse folder structure to get domain and category
        domain_name, category_name = self.parse_folder_structure(document.file_path)
        
        # Create domain and category nodes if structure is present
        if domain_name and category_name:
            queries.append(self.create_domain_node(domain_name))
            queries.append(self.create_category_node(category_name, domain_name))
            queries.append(self.create_domain_category_relationship(domain_name, category_name))
        
        # Create document node
        queries.append(self.create_document_node(document))
        
        # Link document to category if structure is present
        if domain_name and category_name:
            queries.append(self.create_category_document_relationship(category_name, domain_name, document.file_path))
        
        # Create concept nodes
        for concept in concepts:
            queries.append(self.create_concept_node(concept))
        
        # Create kg-gen entity nodes
        if kg_gen_entities:
            for entity in kg_gen_entities:
                queries.append(self.create_kg_gen_entity_node(entity, document.file_path))
                queries.append(self.create_document_kg_gen_relationship(document.file_path, entity.name))
        
        # Create kg-gen relations
        if kg_gen_relations:
            for relation in kg_gen_relations:
                queries.append(self.create_kg_gen_relation(relation))
        
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
