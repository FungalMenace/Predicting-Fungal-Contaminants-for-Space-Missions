
# fungi_pipeline

A modularized, production-style Python package extracted and consolidated from your notebooks.

## Features
- Clean package layout with modules for I/O (UniProt/NCBI/OrthoDB), BLAST orchestration, scoring, and a CLI
- Tests (pytest)
- Code style via Black and Ruff
- A provenance module (`fungi_pipeline/_from_notebooks.py`) containing code extracted from your original notebooks

## Install (editable)
```bash
pip install -e .
```

## Run tests
```bash
pytest -q
```

## Format & lint
```bash
black .
ruff check .
```

## CLI example
```bash
python -m fungi_pipeline.cli score /path/to/category_identity.csv
```
