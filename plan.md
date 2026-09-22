# Plan: ASRS Knowledge Graph PoC - Initial Setup

## Context
I have read and understood the ASRS Knowledge Graph PoC project context document. The repository is currently empty (only contains the context file and a minimal README.md). We are at the very beginning of Phase 1 (ASRS ingestion).

## Current State
- Repository: `/c/Users/benjamin.deporte/Documents/095_Code_Python_Toy/KG_agentic_PoC/`
- Files present: README.md, asrs-knowledge-graph-poc-project-context.md
- No Python files, no virtual environment, no requirements, no data

## Immediate Goal
Complete **Phase 1, Task 1**: Project setup - repo structure, uv, pyproject.toml, .env for API keys, README skeleton.

## Detailed Plan for Task 1

### Subtask 1.1: Create repository structure
- Create directory structure for the project:
  - `data/` - for raw and processed data
  - `data/raw/` - CSV exports from ASRS
  - `data/processed/` - cleaned/normalized data
  - `data/extracted/` - JSONL extraction (source of truth)
  - `notebooks/` - exploration notebooks
  - `src/` - main source code
  - `src/ingestion/` - data acquisition and processing
  - `src/graph/` - graph construction and loading
  - `src/agent/` - LangGraph agent implementation
  - `src/gui/` - Streamlit interface
  - `tests/` - unit and integration tests
  - `docs/` - documentation
  - `config/` - configuration files
  - `docker/` - Docker compose files

### Subtask 1.2: Create virtual environment with uv
- Install uv if not present (`pip install uv` or use uv installer)
- Initialize uv project: `uv init` (creates pyproject.toml with .venv/)
- Use Python 3.10+ (check user's available version)
- Note: uv manages the virtual environment automatically in `.venv/`

### Subtask 1.3: Define dependencies in pyproject.toml
- Create/configure `pyproject.toml` with uv dependency management
- Add dependencies to pyproject.toml using `uv add`:
  - Core: pandas, numpy, pydantic
  - Graph: neo4j (Python driver)
  - Agentic: langgraph, langchain
  - Embeddings: sentence-transformers, numpy
  - GUI: streamlit, streamlit-agraph
  - Dev: pytest, black, ruff, mypy (as dev dependencies)
  - Utilities: python-dotenv, requests, tqdm
- Use `uv lock` to generate lockfile
- Note: requirements.txt can be generated from pyproject.toml if needed (`uv export`)

### Subtask 1.4: Create .env template
- Create `.env.example` with placeholder values for:
  - NEO4J_URI
  - NEO4J_USER
  - NEO4J_PASSWORD
  - MISTRAL_API_KEY (or other LLM provider)
  - Any other API keys needed
- Add `.env` to `.gitignore`

### Subtask 1.5: Enhance README.md
- Expand README with:
  - Project description
  - Quick start instructions
  - Repository structure
  - Setup instructions
  - License information

### Subtask 1.6: Create .gitignore
- Add standard Python patterns
- Add data directories (or specific patterns for sensitive data)
- Add IDE files (.vscode/, .idea/)
- Add `.venv/` (uv virtual environment)
- Add `__pycache__/` and `*.py[cod]`
- Add `.env` (environment file)

## Validation Criteria for Task 1
- [ ] Directory structure created
- [ ] uv project initialized with `.venv/` virtual environment
- [ ] pyproject.toml created with all necessary dependencies (using `uv add`)
- [ ] uv lockfile generated (`uv lock`)
- [ ] .env.example created with all required environment variables
- [ ] .gitignore properly configured (includes `.venv/`)
- [ ] README.md expanded with project information
- [ ] All files committed to git

## Next Tasks After Completion
- Phase 1, Task 2: ASRS reconnaissance
- Phase 1, Task 3: Define acquisition scope
- Phase 1, Task 4: Write paging acquisition script

## Dependencies and Assumptions
- User has Python 3.10+ installed
- User has uv installed (or can install it via `pip install uv`)
- User will provide API keys (Mistral, Neo4j credentials) when needed
- Docker may be needed for Neo4j (Phase 2)

## Risk Mitigations
- Verify Python version before initializing uv project
- Pin versions in pyproject.toml for reproducibility (uv handles this well)
- Document all setup steps clearly, including uv installation

## Notes
The project context document is comprehensive and well-structured. Following its 4-phase, 43-task plan will ensure we build a solid foundation. Phase 1 is about data acquisition and freezing, which is critical before any graph construction or agent work.
