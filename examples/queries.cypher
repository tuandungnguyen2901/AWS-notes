// Example Cypher Queries for Knowledge Graph
// These queries work with the strict schema mode

// =====================================================================
// Service and Component Queries
// =====================================================================

// Find all services that use a specific component
MATCH (s:Service)-[:uses]->(c:Component {name: 'EBS Volume'})
RETURN s.name as service, c.name as component

// Find all components used by a service
MATCH (s:Service {name: 'Amazon EC2'})-[:uses]->(c:Component)
RETURN s.name as service, c.name as component

// Find service dependencies
MATCH (s1:Service)-[:depends_on]->(s2:Service)
RETURN s1.name as dependent_service, s2.name as dependency

// =====================================================================
// Pattern Queries
// =====================================================================

// Find components that implement a pattern
MATCH (c:Component)-[:implements]->(p:Pattern {name: 'Multi-AZ Deployment'})
RETURN c.name as component, p.name as pattern

// Find services that are examples of a pattern
MATCH (s:Service)-[:example_of]->(p:Pattern)
RETURN s.name as service, p.name as pattern

// =====================================================================
// Well-Architected Pillar Queries
// =====================================================================

// Find best practices recommended by a pillar
MATCH (bp:BestPractice)-[:recommended_by]->(p:Pillar {name: 'Reliability'})
RETURN bp.name as best_practice, p.name as pillar

// Find what violates a pillar
MATCH (source)-[:violates]->(p:Pillar {name: 'Security'})
RETURN labels(source)[0] as entity_type, source.name as entity, p.name as pillar

// =====================================================================
// Risk and Mitigation Queries
// =====================================================================

// Find risks and their mitigations
MATCH (m:Mitigation)-[:addresses]->(r:Risk)
RETURN m.name as mitigation, r.name as risk

// Find best practices that address risks
MATCH (bp:BestPractice)-[:addresses]->(r:Risk)
RETURN bp.name as best_practice, r.name as risk

// =====================================================================
// Metric Queries
// =====================================================================

// Find what affects a specific metric
MATCH (source)-[:affects]->(m:Metric {name: 'RTO'})
RETURN labels(source)[0] as entity_type, source.name as entity, m.name as metric

// Find all metrics affected by a service
MATCH (s:Service {name: 'AWS Backup'})-[:affects]->(m:Metric)
RETURN s.name as service, m.name as metric

// =====================================================================
// Learning Flow Queries
// =====================================================================

// Find the complete architecture for a service
MATCH path = (s:Service {name: 'Amazon S3'})-[:uses|implements|depends_on*]->(related)
RETURN path
LIMIT 50

// Find best practices for a specific pillar with their evidence
MATCH (bp:BestPractice)-[:recommended_by]->(p:Pillar {name: 'Security'})
OPTIONAL MATCH (bp)-[:addresses]->(r:Risk)
RETURN bp.name as best_practice, p.name as pillar, 
       collect(DISTINCT r.name) as addressed_risks

// Find services that implement patterns recommended by a pillar
MATCH (s:Service)-[:implements]->(p:Pattern)
MATCH (bp:BestPractice)-[:recommended_by]->(pillar:Pillar)
MATCH (bp)-[:example_of]->(p)
RETURN s.name as service, p.name as pattern, pillar.name as pillar

// =====================================================================
// Verification Queries
// =====================================================================

// Count entities by type
MATCH (n)
RETURN labels(n)[0] as entity_type, count(n) as count
ORDER BY count DESC

// Find entities with most relationships
MATCH (n)-[r]->()
RETURN labels(n)[0] as entity_type, n.name as entity, count(r) as relationship_count
ORDER BY relationship_count DESC
LIMIT 20

// Find isolated entities (no relationships)
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n)[0] as entity_type, n.name as entity
LIMIT 20

// =====================================================================
// Evidence and Provenance Queries
// =====================================================================

// Find triples with evidence sources (if stored in relationships)
MATCH (s)-[r]->(o)
WHERE r.evidence IS NOT NULL
RETURN labels(s)[0] as subject_type, s.name as subject,
       type(r) as relation,
       labels(o)[0] as object_type, o.name as object,
       r.evidence as evidence
LIMIT 20
