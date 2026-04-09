FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
ENV GIT_PYTHON_REFRESH=quiet
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    ninja-build \
 && rm -rf /var/lib/apt/lists/*

COPY --chown=0:0 . /app/

RUN chown -R 0:0 /app

RUN mkdir -p /opt/models
COPY --chown=0:0 XuanjiNovo_130M_massnet_massivekb.ckpt /opt/models/XuanjiNovo_130M_massnet_massivekb.ckpt

RUN cd /app/ctcdecode-master && pip install .
RUN pip install -r /app/requirements-docker-cuda11.txt
RUN cd /app/imputer-pytorch && pip install -e .

ENTRYPOINT []
CMD ["/bin/bash"]
