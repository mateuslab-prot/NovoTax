FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/usr/local/bin:/usr/bin:/bin

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

RUN python -m pip install --upgrade pip wheel

RUN python -m pip install \
    torch==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu118

RUN python -m pip install "git+https://github.com/mateuslab-prot/cascadia-novotax.git"

RUN command -v cascadia && cascadia --help >/dev/null 2>&1 || (echo "cascadia CLI not found"; exit 1)

RUN mkdir -p /opt/models
COPY cascadia.ckpt /opt/models/cascadia.ckpt

ENTRYPOINT []
CMD ["/bin/bash"]
