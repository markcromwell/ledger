"""
Decision Ledger — FastAPI application.

Conventions (enforced by forge_new_program bootstrap):
  - GET /health — no auth, returns {"status": "ok"}
  - All routes under routes/ as APIRouter
  - Tests in scripts/test_unit.py
"""
from fastapi import FastAPI

app = FastAPI(title="Decision Ledger", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "decision-ledger"}
