"""FastAPI application — Decision Ledger CRUD and server-rendered page."""
from __future__ import annotations

import html
from datetime import date
from typing import Generator, Optional

from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from decision_ledger.database import SessionLocal
from decision_ledger.models import Decision
from decision_ledger.schemas import DecisionCreate, DecisionPatch, DecisionRead, DecisionStatus

app = FastAPI(title="Decision Ledger", version="0.1.0")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "decision-ledger"}


@app.post("/decisions", response_model=DecisionRead, status_code=201)
def create_decision(payload: DecisionCreate, db: Session = Depends(get_db)):
    row = Decision(
        title=payload.title,
        context=payload.context,
        decision=payload.decision,
        status=payload.status.value,
        decided_on=payload.decided_on,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/decisions", response_model=list[DecisionRead])
def list_decisions(db: Session = Depends(get_db)):
    rows = db.query(Decision).order_by(Decision.created_at.desc(), Decision.id.desc()).all()
    return rows


@app.get("/decisions/{decision_id}", response_model=DecisionRead)
def get_decision(decision_id: int, db: Session = Depends(get_db)):
    row = db.get(Decision, decision_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return row


@app.patch("/decisions/{decision_id}", response_model=DecisionRead)
def patch_decision(decision_id: int, payload: DecisionPatch, db: Session = Depends(get_db)):
    row = db.get(Decision, decision_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    updates = payload.model_dump(exclude_unset=True)
    # Reject an explicit null for a NOT-NULL column with a clean 422 instead of
    # letting setattr() write NULL and surface a 500 IntegrityError at commit.
    for required in ("title", "status"):
        if required in updates and updates[required] is None:
            raise HTTPException(status_code=422, detail=f"{required} must not be null")
    if "status" in updates and updates["status"] is not None:
        updates["status"] = updates["status"].value
    if "title" in updates and updates["title"] is not None:
        updates["title"] = updates["title"].strip()
        if not updates["title"]:
            raise HTTPException(status_code=422, detail="title must not be empty")

    for field, value in updates.items():
        setattr(row, field, value)

    db.commit()
    db.refresh(row)
    return row


@app.delete("/decisions/{decision_id}", status_code=204)
def delete_decision(decision_id: int, db: Session = Depends(get_db)):
    row = db.get(Decision, decision_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    db.delete(row)
    db.commit()
    return None


def _render_decisions_page(decisions: list[Decision]) -> str:
    items = []
    for d in decisions:
        title = html.escape(d.title)
        status = html.escape(d.status)
        items.append(f"<li><strong>{title}</strong> — <em>{status}</em></li>")
    list_html = "\n".join(items) if items else "<li><em>No decisions yet.</em></li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Decision Ledger</title>
</head>
<body>
  <h1>Decision Ledger</h1>
  <section>
    <h2>Decisions</h2>
    <ul>
      {list_html}
    </ul>
  </section>
  <section>
    <h2>Add Decision</h2>
    <form method="post" action="/">
      <p>
        <label for="title">Title *</label><br>
        <input type="text" id="title" name="title" required>
      </p>
      <p>
        <label for="context">Context</label><br>
        <textarea id="context" name="context" rows="3"></textarea>
      </p>
      <p>
        <label for="decision">Decision</label><br>
        <textarea id="decision" name="decision" rows="3"></textarea>
      </p>
      <p>
        <label for="status">Status</label><br>
        <select id="status" name="status">
          <option value="proposed">proposed</option>
          <option value="adopted">adopted</option>
          <option value="superseded">superseded</option>
          <option value="rejected">rejected</option>
        </select>
      </p>
      <p>
        <label for="decided_on">Decided on</label><br>
        <input type="date" id="decided_on" name="decided_on">
      </p>
      <p><button type="submit">Add Decision</button></p>
    </form>
  </section>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index(db: Session = Depends(get_db)):
    decisions = db.query(Decision).order_by(Decision.created_at.desc(), Decision.id.desc()).all()
    return _render_decisions_page(decisions)


@app.post("/", response_class=RedirectResponse)
def create_from_form(
    title: str = Form(...),
    context: Optional[str] = Form(None),
    decision: Optional[str] = Form(None),
    status: str = Form("proposed"),
    decided_on: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not title or not title.strip():
        raise HTTPException(status_code=422, detail="title must not be empty")
    try:
        status_value = DecisionStatus(status).value
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid status")

    parsed_date: Optional[date] = None
    if decided_on:
        try:
            parsed_date = date.fromisoformat(decided_on)
        except ValueError:
            raise HTTPException(status_code=422, detail="invalid decided_on date")

    row = Decision(
        title=title.strip(),
        context=context or None,
        decision=decision or None,
        status=status_value,
        decided_on=parsed_date,
    )
    db.add(row)
    db.commit()
    return RedirectResponse(url="/", status_code=303)