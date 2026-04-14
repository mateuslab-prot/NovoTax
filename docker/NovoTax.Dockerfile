FROM mambaorg/micromamba:2.5.0

COPY --chown=$MAMBA_USER:$MAMBA_USER docker/novotax_env.yaml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml \
    && micromamba clean --all --yes

WORKDIR /app
ENV PYTHONPATH=/app

COPY --chown=$MAMBA_USER:$MAMBA_USER . /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD ["/bin/bash"]
