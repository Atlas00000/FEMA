# FEMA offline ops only (INF-DOCKER). No MetaTrader / tester inside.
# Build from repo root:
#   docker build -f AI/Dockerfile -t fema-ops .
# Run:
#   docker run --rm -v "%CD%/AI/data:/work/AI/data" -v "%CD%/AI/kb:/work/AI/kb" -v "%CD%/Presets:/work/Presets:ro" fema-ops health

FROM python:3.12-slim

LABEL org.opencontainers.image.title="fema-ops" \
      org.opencontainers.image.description="FEMA Python offline ops (health, register, clone) — no MT5" \
      org.opencontainers.image.source="FEMA/AI"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/work/AI \
    FEMA_REPO_ROOT=/work

WORKDIR /work/AI

# Stdlib-only today; keep install step for future pins
COPY AI/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Ops package + certificate + schemas + kb defaults (data mounted at runtime)
COPY AI/fema_ops /work/AI/fema_ops
COPY AI/cert_loader.py AI/csv_util.py AI/paths.py AI/sync_from_agent.py /work/AI/
COPY AI/certificate_PRODUCTION_EURUSD.json AI/certificate_PRODUCTION_EURUSD.md /work/AI/
COPY AI/schemas /work/AI/schemas
COPY AI/kb /work/AI/kb
COPY AI/templates /work/AI/templates
COPY AI/requirements.txt /work/AI/requirements.txt
COPY ops/postgres/init /work/ops/postgres/init

# Placeholders so mounts are optional for --help
RUN mkdir -p /work/AI/data/live /work/Presets

ENTRYPOINT ["python", "-m", "fema_ops"]
CMD ["status"]
