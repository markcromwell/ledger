"""
Decision Ledger — FastAPI application entry point.

Conventions (enforced by forge_new_program bootstrap):
  - GET /health — no auth, returns {"status": "ok"}
  - All routes under decision_ledger/app.py
  - Tests in scripts/test_unit.py
"""
from decision_ledger.app import app  # noqa: F401