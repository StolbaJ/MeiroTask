# Use Python 3.11 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements first for better caching
COPY required.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r required.txt

# Copy application code
COPY  . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Expose health check endpoint (if needed)
EXPOSE 8080

# Set default command
ENTRYPOINT ["python3"]

CMD ["main.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Labels for better maintainability
LABEL maintainer="Jakub Štolba" \
      version="1.0.0" \
      description="ShowAds Data Connector for processing customer data from CSV files"
