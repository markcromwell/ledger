"""Unit tests for Decision Ledger."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from decision_ledger.app import app, get_db
from decision_ledger.database import Base
from decision_ledger.models import DECISION_STATUSES, Decision
from decision_ledger.schemas import DecisionStatus

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_decision_model_columns_and_defaults():
    mapper = inspect(Decision)
    column_names = {col.key for col in mapper.columns}
    assert column_names == {
        "id",
        "title",
        "context",
        "decision",
        "status",
        "decided_on",
        "created_at",
    }

    title_col = mapper.columns["title"]
    assert title_col.nullable is False

    status_col = mapper.columns["status"]
    assert status_col.nullable is False
    assert status_col.default.arg == "proposed"
    assert status_col.server_default is not None

    assert tuple(DecisionStatus) == DECISION_STATUSES
    assert DecisionStatus.proposed.value == "proposed"


def test_migration_is_offline_safe():
    migration_path = (
        Path(__file__).resolve().parent.parent
        / "alembic"
        / "versions"
        / "3371_create_decisions_table.py"
    )
    source = migration_path.read_text()
    assert "CREATE TABLE IF NOT EXISTS decisions" in source
    assert "DROP TABLE IF EXISTS decisions" in source
    assert "sa.inspect" not in source
    assert "get_bind" not in source


def test_create_decision(client):
    resp = client.post(
        "/decisions",
        json={"title": "Use PostgreSQL", "context": "Need durable storage"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Use PostgreSQL"
    assert body["context"] == "Need durable storage"
    assert body["status"] == "proposed"
    assert body["id"] >= 1


def test_create_rejects_empty_title(client):
    resp = client.post("/decisions", json={"title": "   "})
    assert resp.status_code == 422


def test_create_rejects_invalid_status(client):
    resp = client.post("/decisions", json={"title": "Valid title", "status": "pending"})
    assert resp.status_code == 422


def test_list_decisions_newest_first(client):
    now = datetime.now(timezone.utc)
    db = TestingSessionLocal()
    try:
        older = Decision(
            title="Older",
            status="proposed",
            created_at=now - timedelta(hours=1),
        )
        newer = Decision(
            title="Newer",
            status="adopted",
            created_at=now,
        )
        db.add_all([older, newer])
        db.commit()
    finally:
        db.close()

    resp = client.get("/decisions")
    assert resp.status_code == 200
    titles = [item["title"] for item in resp.json()]
    assert titles == ["Newer", "Older"]


def test_get_decision(client):
    created = client.post("/decisions", json={"title": "Fetch me"}).json()
    resp = client.get(f"/decisions/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Fetch me"


def test_get_decision_404(client):
    resp = client.get("/decisions/9999")
    assert resp.status_code == 404


def test_patch_decision(client):
    created = client.post(
        "/decisions",
        json={"title": "Original", "status": "proposed"},
    ).json()
    resp = client.patch(
        f"/decisions/{created['id']}",
        json={"status": "adopted", "decision": "Ship it"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "adopted"
    assert body["decision"] == "Ship it"
    assert body["title"] == "Original"


def test_patch_rejects_invalid_status(client):
    created = client.post("/decisions", json={"title": "Patch me"}).json()
    resp = client.patch(f"/decisions/{created['id']}", json={"status": "invalid"})
    assert resp.status_code == 422


def test_patch_rejects_null_title(client):
    """Explicit null for the NOT-NULL title column → 422, not a 500 IntegrityError."""
    created = client.post("/decisions", json={"title": "Has title"}).json()
    resp = client.patch(f"/decisions/{created['id']}", json={"title": None})
    assert resp.status_code == 422


def test_patch_rejects_null_status(client):
    """Explicit null for the NOT-NULL status column → 422, not a 500."""
    created = client.post("/decisions", json={"title": "Has status"}).json()
    resp = client.patch(f"/decisions/{created['id']}", json={"status": None})
    assert resp.status_code == 422


def test_patch_decision_404(client):
    resp = client.patch("/decisions/9999", json={"title": "Nope"})
    assert resp.status_code == 404


def test_requirements_pin_postgres_driver():
    """Prod uses Postgres: the driver must be pinned AND named in the URL, or prod
    startup crashes even though the SQLite-backed tests pass (the LEDGER dogfood bug)."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    reqs = (root / "requirements.txt").read_text(encoding="utf-8")
    assert "psycopg2" in reqs, "requirements.txt must pin a Postgres driver (psycopg2-binary)"
    db_src = (root / "decision_ledger" / "database.py").read_text(encoding="utf-8")
    assert "postgresql+psycopg2://" in db_src, "DATABASE_URL default must name the driver"


def test_delete_decision(client):
    created = client.post("/decisions", json={"title": "Delete me"}).json()
    resp = client.delete(f"/decisions/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/decisions/{created['id']}").status_code == 404


def test_delete_decision_404(client):
    resp = client.delete("/decisions/9999")
    assert resp.status_code == 404


def test_index_page_lists_decisions_and_form(client):
    db = TestingSessionLocal()
    try:
        db.add(
            Decision(
                title="Visible Decision",
                status="adopted",
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    finally:
        db.close()

    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text
    assert "Visible Decision" in html
    assert "adopted" in html
    assert '<form method="post" action="/">' in html
    assert 'name="title"' in html
    assert 'name="context"' in html
    assert 'name="decision"' in html
    assert 'name="status"' in html
    assert 'name="decided_on"' in html