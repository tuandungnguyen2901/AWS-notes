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

### Node Labels

- **Document**: Represents markdown files
  - Properties: `title`, `file_path`, `content`, `created_at`
- **Concept**: Represents AWS services, features, technologies
  - Properties: `name`, `type` (service/feature/technology/concept), `description`
- **Section**: Represents document sections
  - Properties: `heading`, `level`, `content`, `start_line`, `end_line`

### Relationships

- `(Document)-[:DOCUMENTS]->(Concept)`: Document mentions/describes concept
- `(Concept)-[:RELATES_TO]->(Concept)`: Concepts are related
- `(Document)-[:REFERENCES]->(Document)`: Document references another document
- `(Document)-[:CONTAINS]->(Section)`: Document contains sections
- `(Section)-[:MENTIONS]->(Concept)`: Section mentions concept

## Example Cypher Queries

After importing, you can query your knowledge graph:

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

## Project Structure

```
AWS-notes/
├── knowledge/                    # Your knowledge folder (optional)
├── knowledge_service/
│   ├── __init__.py
│   ├── neo4j_client.py          # Neo4j connection handling
│   ├── markdown_parser.py        # Markdown parsing
│   ├── concept_extractor.py      # Concept extraction
│   ├── graph_builder.py          # Cypher query building
│   └── importer.py               # Main import orchestration
├── cli.py                        # CLI interface
├── requirements.txt
└── README.md
```

## Troubleshooting

1. **Connection Error**: Make sure Neo4j is running and the connection details are correct
2. **Password Required**: Set `NEO4J_PASSWORD` environment variable or use `--neo4j-password` flag
3. **No Files Found**: Check that your knowledge directory contains `.md` files
4. **Import Errors**: Check the error messages in the output for specific file issues

## License

MIT
