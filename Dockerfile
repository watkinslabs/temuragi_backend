# Build stage
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 flask_user

# Create directory structure
RUN mkdir -p /web/temuragi/app/logs && chown -R flask_user:flask_user /web

WORKDIR /web/temuragi

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/flask_user/.local

# Copy application code - just the app directory contents
COPY --chown=flask_user:flask_user ./app ./app

# Switch to non-root user
USER flask_user

# Update PATH
ENV PATH=/home/flask_user/.local/bin:$PATH

# Environment variables
ENV FLASK_APP=app.app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/web/temuragi

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app.app:app"]