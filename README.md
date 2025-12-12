# Knowledge Service - Neo4j Import Tool

A Python service to import markdown knowledge files into a Neo4j graph database, creating a structured knowledge graph with documents, concepts, and relationships.

## Features

- Parse markdown files and extract structured content
- Extract AWS services, concepts, and technical terms
- Build relationships between documents and concepts
- Import everything into Neo4j graph database
- CLI interface for easy usage
- Support for recursive directory scanning

## Installation

1. Install `uv` (fast Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

   Or using traditional pip:
```bash
pip install -r requirements.txt
```

3. Set up Neo4j:
   - Install and start Neo4j (see [Neo4j Installation Guide](https://neo4j.com/docs/operations-manual/current/installation/))
   - Default connection: `bolt://localhost:7687`

3. Configure environment variables (optional):
   Create a `.env` file in the project root:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=neo4j
   ```

## Usage

### CLI Command

The simplest way to use the service is through the CLI:

```bash
# Activate virtual environment (if using uv)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Import knowledge from default ./knowledge folder
python cli.py import

# Import from custom knowledge folder
python cli.py import --knowledge-dir ./domain_1

# Import with custom Neo4j connection
python cli.py import --neo4j-uri bolt://localhost:7687 --neo4j-user neo4j --neo4j-password mypassword

# Clear existing graph and re-import
python cli.py import --clear

# Use strict schema mode with full pipeline
python cli.py import --schema-mode strict --normalize --validate --cluster

# Incremental update mode
python cli.py import --schema-mode strict --incremental

# Custom similarity threshold for normalization
python cli.py import --schema-mode strict --similarity-threshold 0.8
```

### Python Library

You can also use it as a Python library:

```python
from knowledge_service import KnowledgeImporter

# Create importer
importer = KnowledgeImporter(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# Import knowledge folder
with importer:
    stats = importer.import_directory("./knowledge/", clear_first=False)
    print(f"Imported {stats['documents_created']} documents")
```

## Knowledge Folder Structure

Organize your markdown files in any folder structure you prefer. The service will recursively scan for all `.md` files:

```
knowledge/
├── domain_1/
│   └── network_connecting_strategies/
│       ├── AWS_Client_VPN_Configuration.md
│       ├── AWS_Network_Connectivity_Options.md
│       └── ...
└── domain_2/
    └── ...
```

## Graph Schema

### Strict Schema Mode (New)

The system supports a strict, schema-driven approach with enforced entity types and relations:

#### Entity Types

- **Service**: AWS services (e.g., Amazon S3, AWS Lambda)
- **Component**: Sub-components (e.g., EBS Volume, VPC Subnet)
- **Pattern**: Architectural patterns (e.g., Multi-AZ Deployment, Blue-Green Deployment)
- **Pillar**: Well-Architected Pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization)
- **BestPractice**: Concrete recommendations
- **Risk**: Failure modes (e.g., single point of failure)
- **Mitigation**: Practices to address risks
- **Metric**: SLA/thresholds
- **Role**: Roles (e.g., DevOps, DBA, SRE)

#### Relations

- `uses`: Service/Component → Component
- `implements`: Component/Service → Pattern
- `addresses`: Mitigation/BestPractice → Risk
- `recommended_by`: BestPractice → Pillar
- `affects`: Service/Component/Pattern/BestPractice → Metric
- `depends_on`: Service/Component → Service/Component
- `violates`: Service/Component/Pattern → Pillar
- `example_of`: Service/Component/Pattern → Pattern

### Legacy Schema Mode

For backward compatibility, the system also supports the legacy schema:

#### Node Labels

- **Document**: Represents markdown files
  - Properties: `title`, `file_path`, `content`, `created_at`
- **Concept**: Represents AWS services, features, technologies
  - Properties: `name`, `type` (service/feature/technology/concept), `description`
- **Section**: Represents document sections
  - Properties: `heading`, `level`, `content`, `start_line`, `end_line`
- **Domain**: Represents domain folders
- **Category**: Represents category folders

#### Relationships

- `(Document)-[:DOCUMENTS]->(Concept)`: Document mentions/describes concept
- `(Concept)-[:RELATES_TO]->(Concept)`: Concepts are related
- `(Document)-[:REFERENCES]->(Document)`: Document references another document
- `(Document)-[:CONTAINS]->(Section)`: Document contains sections
- `(Section)-[:MENTIONS]->(Concept)`: Section mentions concept
- `(Domain)-[:CONTAINS]->(Category)`: Domain contains categories
- `(Category)-[:CONTAINS]->(Document)`: Category contains documents

## Enhanced Features

### Preprocessing and Chunking

Documents are automatically chunked by headings (1000-3000 tokens per chunk) with preserved context hierarchy. Each chunk includes metadata:
- Source document path
- Section heading path (H1 → H2 → H3)
- URL (if base URL provided)
- Timestamp

### Entity Normalization

Entities are normalized to canonical forms using:
1. **Rule-based normalization**: Alias mapping (S3 → Amazon S3, EC2 → Amazon EC2)
2. **Semantic matching**: Embedding-based similarity matching (threshold: 0.75)

### Validation

Triples are validated against:
- Schema rules (entity type - relation compatibility)
- Business rules (e.g., `recommended_by` only for BestPractice → Pillar)
- Evidence length requirements (minimum 3 words unless inferred)

### Clustering and Merging

Similar entities are clustered using embeddings, and triples are merged with aggregated evidence sources preserving provenance.

### Incremental Updates

When using `--incremental` mode, the system:
- Detects identical triples (appends evidence)
- Identifies new triples (inserts)
- Flags conflicts for review

## Example Cypher Queries

### Legacy Schema Queries

```cypher
// Find all documents that mention AWS Transit Gateway
MATCH (d:Document)-[:DOCUMENTS]->(c:Concept {name: 'AWS Transit Gateway'})
RETURN d.title, d.file_path

// Find all concepts related to VPN
MATCH (c1:Concept)-[:RELATES_TO]->(c2:Concept)
WHERE c1.name CONTAINS 'VPN' OR c2.name CONTAINS 'VPN'
RETURN c1.name, c2.name

// Find document references
MATCH (d1:Document)-[:REFERENCES]->(d2:Document)
RETURN d1.title, d2.title

// Get document structure
MATCH (d:Document)-[:CONTAINS]->(s:Section)
WHERE d.title = 'AWS Network Connectivity Options'
RETURN s.heading, s.level
ORDER BY s.start_line
```

### Strict Schema Queries

```cypher
// Find services that use a specific component
MATCH (s:Service)-[:uses]->(c:Component {name: 'EBS Volume'})
RETURN s.name, c.name

// Find best practices recommended by a pillar
MATCH (bp:BestPractice)-[:recommended_by]->(p:Pillar {name: 'Reliability'})
RETURN bp.name, p.name

// Find patterns that implement multi-AZ
MATCH (c:Component)-[:implements]->(pat:Pattern {name: 'Multi-AZ Deployment'})
RETURN c.name, pat.name

// Find risks and their mitigations
MATCH (m:Mitigation)-[:addresses]->(r:Risk)
RETURN m.name, r.name

// Find services that depend on other services
MATCH (s1:Service)-[:depends_on]->(s2:Service)
RETURN s1.name, s2.name

// Find what affects a specific metric
MATCH (source)-[:affects]->(m:Metric {name: 'RTO'})
RETURN labels(source)[0] as source_type, source.name, m.name
```

## Configuration

### Environment Variables

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# KG-Gen Configuration
KG_GEN_API_KEY=your_api_key
KG_GEN_MODEL=google/gemini-2.0-flash-001
GOOGLE_API_KEY=your_api_key  # Alternative
GEMINI_API_KEY=your_api_key  # Alternative

# Schema Mode Configuration
KG_SCHEMA_MODE=strict  # or 'legacy'
KG_ENABLE_NORMALIZATION=true
KG_ENABLE_VALIDATION=true
KG_ENABLE_CLUSTERING=true
KG_ENABLE_INCREMENTAL=false
KG_SIMILARITY_THRESHOLD=0.75
KG_MIN_CHUNK_TOKENS=1000
KG_MAX_CHUNK_TOKENS=3000
KG_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Project Structure

```
AWS-notes/
├── knowledge/                    # Your knowledge folder (optional)
├── domain_1/                     # Domain folders
├── domain_2/
├── services/                     # Service documentation
├── prompts/                      # Prompt templates
│   └── wa_prompt.txt            # Well-Architected prompt template
├── scripts/                      # Utility scripts
│   └── migrate_schema.py        # Schema migration script
├── examples/                     # Example queries
│   └── queries.cypher           # Cypher query examples
├── knowledge_service/
│   ├── __init__.py
│   ├── schema.py                # Schema definitions (NEW)
│   ├── canonical_registry.py    # Canonical entity registry (NEW)
│   ├── chunk_processor.py       # Chunk processing (NEW)
│   ├── prompt_templates.py      # Prompt templates (NEW)
│   ├── entity_normalizer.py     # Entity normalization (NEW)
│   ├── normalization_service.py # Normalization orchestration (NEW)
│   ├── triple_validator.py      # Triple validation (NEW)
│   ├── validation_pipeline.py   # Validation orchestration (NEW)
│   ├── entity_clusterer.py     # Entity clustering (NEW)
│   ├── relation_normalizer.py  # Relation normalization (NEW)
│   ├── merge_service.py        # Merge service (NEW)
│   ├── triple_store.py          # Triple storage (NEW)
│   ├── diff_extractor.py        # Diff extraction (NEW)
│   ├── config.py                # Configuration (NEW)
│   ├── neo4j_client.py          # Neo4j connection handling
│   ├── markdown_parser.py        # Markdown parsing (enhanced)
│   ├── concept_extractor.py     # Concept extraction
│   ├── kg_gen_extractor.py      # KG-gen extraction (enhanced)
│   ├── graph_builder.py         # Cypher query building (enhanced)
│   └── importer.py              # Main import orchestration (enhanced)
├── cli.py                        # CLI interface (enhanced)
├── requirements.txt             # Dependencies (updated)
└── README.md                    # This file
```

## Migration

To migrate from legacy schema to strict schema:

```bash
# Dry run to see what would be migrated
python scripts/migrate_schema.py --dry-run

# Perform migration
python scripts/migrate_schema.py
```

## Troubleshooting

1. **Connection Error**: Make sure Neo4j is running and the connection details are correct
2. **Password Required**: Set `NEO4J_PASSWORD` environment variable or use `--neo4j-password` flag
3. **No Files Found**: Check that your knowledge directory contains `.md` files
4. **Import Errors**: Check the error messages in the output for specific file issues

## License

MIT
