FROM mambaorg/micromamba:2.5.0

ENV MAMBA_ROOT_PREFIX=/opt/conda
ENV PATH=${MAMBA_ROOT_PREFIX}/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
ENV PYTHONPATH=/app

COPY --chown=$MAMBA_USER:$MAMBA_USER docker/novotax_env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml \
    && micromamba clean --all --yes

USER root

RUN ln -sf ${MAMBA_ROOT_PREFIX}/bin/python /usr/local/bin/python \
    && ln -sf ${MAMBA_ROOT_PREFIX}/bin/python /usr/local/bin/python3 \
    && ln -sf ${MAMBA_ROOT_PREFIX}/bin/pip /usr/local/bin/pip \
    && ln -sf ${MAMBA_ROOT_PREFIX}/bin/pip /usr/local/bin/pip3

WORKDIR /work
COPY . /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD ["/bin/bash"]
