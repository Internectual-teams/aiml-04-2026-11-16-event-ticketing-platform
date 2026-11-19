# syntax=docker/dockerfile:1
# BookMyShow Event Ticketing Platform - Recommendations Service
# Team: AIML-04 | Ticket: AIML-0011-W1-04 | Sprint: 1

FROM python:3.12-slim

# Prevent Python from writing bytecode (.pyc) and enable unbuffered output logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set working directory inside container
WORKDIR /app

# Install system dependencies if required (keep image minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies manifest first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Create a non-root application user for secure execution
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Copy application source code, dataset, and test suite
COPY src/ /app/src/
COPY data/ /app/data/
COPY tests/ /app/tests/

# Ensure application directories and mounted volumes are writeable
RUN mkdir -p /app/data \
    && chown -R appuser:appgroup /app \
    && chmod -R 777 /app/data

# Switch to non-root user
USER appuser

# Healthcheck to verify Python runtime and core libraries respond
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pandas, numpy, sklearn; print('healthy')" || exit 1

# Default command: Execute the main recommendation workflow
CMD ["python", "-m", "src.main"]
