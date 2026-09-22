# ASRS Knowledge Graph PoC

A proof-of-concept application demonstrating agentic AI with a knowledge graph built on the NASA ASRS (Aviation Safety Reporting System) dataset.

## Overview

This project implements a knowledge graph pipeline for aviation incident reports, combining:
- **Structural graph layer**: Built from coded fields (anomaly types, factors, aircraft, FAR references)
- **Constructed graph layer**: LLM-derived connections between reports (duplicates, causal relationships, similarities)
- **Agentic query engine**: LangGraph-based agent with curated Cypher tools for answering complex queries
- **Streamlit GUI**: Interactive interface for exploring the graph and querying the data

## Project Structure

```
KG_agentic_PoC/
├── data/
│   ├── raw/           # Original CSV exports from ASRS
│   ├── processed/     # Cleaned/normalized data
│   └── extracted/     # JSONL extraction (source of truth)
├── notebooks/         # Exploration and analysis notebooks
├── src/
│   ├── ingestion/     # Data acquisition and processing
│   ├── graph/         # Graph construction and loading
│   ├── agent/         # LangGraph agent implementation
│   └── gui/           # Streamlit interface
├── tests/             # Unit and integration tests
├── docs/              # Documentation
├── config/            # Configuration files
├── docker/            # Docker compose files
├── .env.example       # Environment variables template
├── pyproject.toml     # Project dependencies (uv)
└── README.md
```

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker and Docker Compose (for Neo4j)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd KG_agentic_PoC

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

### 2. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt  # if available
```

### 3. Start Neo4j

```bash
# Using Docker Compose
docker compose -f docker/docker-compose.neo4j.yml up -d

# Or manually
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/yourpassword neo4j:5
```

### 4. Run the Application

```bash
# Start the Streamlit GUI
uv run streamlit run src/gui/app.py
```

## Configuration

### Environment Variables

See `.env.example` for required environment variables:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
MISTRAL_API_KEY=your_mistral_api_key
```

### Project Settings

Edit `config/settings.py` for application-specific configurations.

## Data Acquisition

ASRS data is obtained manually from [NASA ASRS Database Online](https://asrs.arc.nasa.gov/search/database.html):

1. Use the query wizard to select desired fields
2. Export results as CSV (max 10,000 records per export)
3. Place CSV files in `data/raw/`
4. Run the ingestion pipeline:
   ```bash
   uv run python src/ingestion/acquire.py
   ```

## Graph Construction

Build the knowledge graph from extracted data:

```bash
# Load structural layer (from coded fields)
uv run python src/graph/load_structural.py

# Build constructed layer (LLM-derived edges)
uv run python src/graph/build_constructed.py
```

## Running Tests

```bash
uv run pytest tests/
```

## Development

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## License

This project is for research purposes only. The ASRS dataset is public domain (U.S. government work).

## References

- [NASA ASRS Database](https://asrs.arc.nasa.gov/)
- [Project Context Documentation](asrs-knowledge-graph-poc-project-context.md)
