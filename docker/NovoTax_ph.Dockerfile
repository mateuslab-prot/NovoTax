FROM python:3.11-slim

WORKDIR /app
COPY count_lines.py /app/count_lines.py

RUN chmod +x /app/count_lines.py

ENTRYPOINT []
CMD ["/bin/bash"]
