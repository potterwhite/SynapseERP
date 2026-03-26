# syntax=docker/dockerfile:1
# SynapseERP — Backend image
# Base: Python 3.12-slim
# Runtime: Gunicorn (WSGI)
# Entry: docker/entrypoint.sh (waits for DB → migrate → collectstatic → start)

FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
# Copy requirements first to leverage layer caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory
COPY backend/ /app/backend/

# Install the backend package in editable mode so all synapse_* apps are importable.
# This mirrors the local dev setup: pip install -e backend/
RUN pip install --no-cache-dir -e /app/backend/

# PYTHONPATH: makes synapse_* Django apps importable by manage.py and Gunicorn
ENV PYTHONPATH=/app/backend/src

# Copy and enable the entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
