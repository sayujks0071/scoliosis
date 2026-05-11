# Dockerfile for IEC Model reproducibility
# 
# Build:
#   docker build -t spinalmodes:0.2.0 -f envs/Dockerfile .
#
# Run:
#   docker run --rm -v $(pwd):/workspace -w /workspace spinalmodes:0.2.0 python test_solver_upgrade.py
#
# For publication reproducibility, exact versions are pinned.
# This container has been tested with the BVP solver upgrade.
#
# Last updated: 2025-11-04
# Compatible with: IEC model v0.2.0 (BVP solver upgrade)

FROM python:3.10.12-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies (minimal for scientific computing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY envs/requirements.txt /tmp/requirements.txt

# Install Python dependencies with exact versions
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy project files
COPY . /workspace

# Set Python path to include project root
ENV PYTHONPATH=/workspace

# Default command: run smoke tests
CMD ["python", "test_solver_upgrade.py"]

# Metadata
LABEL maintainer="Dr. Sayuj Krishnan"
LABEL version="0.2.0"
LABEL description="IEC Model - Publication-ready BVP solver framework"
LABEL org.opencontainers.image.source="https://github.com/sayujks0071/life"



