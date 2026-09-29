# syntax=docker/dockerfile:1
#
# Multi-stage build: dependencies are installed in a builder stage using a
# dependency-first COPY order (pyproject.toml before app source) so that an
# app-code-only change doesn't invalidate the dependency-install layer. See
# docs/architecture/docker-compose.md §1.

FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install dependencies first (cache-friendly): a stub package satisfies
# hatchling's build-backend requirement for `packages = ["app"]` without
# needing the real source yet.
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Now install the real application on top (fast: dependencies are already
# satisfied, this just (re)installs the local package with --no-deps).
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
RUN pip install --no-cache-dir --no-deps .

FROM python:3.12-slim AS runtime

# The base image's system-Python build tools (pip/setuptools/wheel, with their
# vendored msgpack) are unused at runtime — the app runs from /opt/venv — and
# carry HIGH CVEs Trivy gates on. Remove them from the runtime image.
RUN /usr/local/bin/python -m pip uninstall -y pip setuptools wheel

RUN groupadd --system app && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /opt/venv /opt/venv
# Same reason for the venv's own pip (vendors msgpack/setuptools).
RUN python -m pip uninstall -y pip
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic.ini ./
COPY --from=builder /app/alembic ./alembic

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
