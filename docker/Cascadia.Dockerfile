FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Small set of OS packages that commonly help scientific Python deps install cleanly
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libhdf5-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy metadata first for better layer caching
COPY pyproject.toml README.md /app/

# Copy package source
COPY cascadia /app/cascadia

# Install package and dependencies
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install .

ENTRYPOINT []
CMD ["/bin/bash"]
ENV PYTHONPATH=/app
