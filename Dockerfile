FROM python:3.11-slim

WORKDIR /app

# Non-root runtime user (CoEv2 finding + container-security baseline).
RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh && chown -R appuser:appuser /app

USER appuser

# Internal port is fixed; the host port is mapped per-tier by compose.
ENV PORT=8765
EXPOSE 8765

# Migrate the schema, then serve. LEDGER has no create_all on boot — it relies on
# alembic — so `alembic upgrade head` MUST run before uvicorn (see docker-entrypoint.sh).
ENTRYPOINT ["./docker-entrypoint.sh"]
