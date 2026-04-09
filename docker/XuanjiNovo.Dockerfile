FROM guomics2017/massnet-dda:cuda11_v1.1

RUN mkdir -p /opt/models
COPY XuanjiNovo_130M_massnet_massivekb.ckpt /opt/models/XuanjiNovo_130M_massnet_massivekb.ckpt

ENTRYPOINT []
CMD ["/bin/bash"]
ENV PYTHONPATH=/app
