# Base stage
FROM python:3.13-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./services/leave-service/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Copy shared modules
COPY ./shared /app/shared

# Copy application code
COPY ./services/leave-service/src /app/src
COPY ./services/leave-service/alembic /app/alembic
COPY ./services/leave-service/alembic.ini /app/

# Expose port
EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]

# Production stage
FROM base as production

# Copy shared modules
COPY ./shared /app/shared

# Copy application code
COPY ./services/leave-service/src /app/src
COPY ./services/leave-service/alembic /app/alembic
COPY ./services/leave-service/alembic.ini /app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]
