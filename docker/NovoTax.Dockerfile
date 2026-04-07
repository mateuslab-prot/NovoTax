FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    procps \
    ca-certificates \
    curl \
    tar \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install MMseqs2 from official static binary
RUN curl -L https://mmseqs.com/latest/mmseqs-linux-avx2.tar.gz \
    | tar -xz -C /opt \
 && ln -s /opt/mmseqs/bin/mmseqs /usr/local/bin/mmseqs

# Copy only what is needed for the NovoTax tool
COPY pyproject.toml /app/
COPY NovoTax /app/NovoTax

# Optional: install requirements first if present
RUN if [ -f /app/NovoTax/requirements.txt ]; then \
      pip install --no-cache-dir -r /app/NovoTax/requirements.txt; \
    fi

# Install NovoTax itself
RUN pip install --no-cache-dir .

# Nextflow-friendly behavior
ENTRYPOINT []
CMD ["/bin/bash"]
