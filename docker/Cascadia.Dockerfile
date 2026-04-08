FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    git \
    ca-certificates \
    build-essential \
    bash \
    libxrender1 \
    libxext6 \
    libsm6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/local/bin/python && \
    ln -sf /usr/bin/pip3 /usr/local/bin/pip

RUN pip install --upgrade pip wheel

RUN pip install \
    torch==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu118

RUN pip install "git+https://github.com/mateuslab-prot/cascadia-novotax.git"

ENTRYPOINT []
CMD ["/bin/bash"]