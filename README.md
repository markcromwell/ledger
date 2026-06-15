# Decision Ledger

A FastAPI application bootstrapped by [Sovereign](https://github.com/markcromwell/master-control-program).

## Quickstart

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Conventions

This project follows the Sovereign coding conventions:

- `GET /health` — always present, no auth required
- Tests in `scripts/test_unit.py`, run with `pytest scripts/test_unit.py`
- Docker image built from `Dockerfile`
- CI in `.github/workflows/ci.yml`
- Environment vars in `.env` (never committed)

## Development

```bash
# Run tests
python -m pytest scripts/test_unit.py -x -q

# Lint
ruff check .
```
