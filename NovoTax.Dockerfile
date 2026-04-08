FROM python:3.11-slim

WORKDIR /app
COPY main.py /app/main.py

RUN chmod +x /app/main.py

ENTRYPOINT []
CMD ["/bin/bash"]
