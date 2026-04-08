FROM python:3.11-slim

WORKDIR /app
COPY novotax_ph.py /app/novotax_ph.py

RUN chmod +x /app/novotax_ph.py

ENTRYPOINT []
CMD ["/bin/bash"]
