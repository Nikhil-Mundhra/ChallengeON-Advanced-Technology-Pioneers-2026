FROM python:3.12-slim

RUN pip install --no-cache-dir duckdb pypdf

COPY container_entrypoint.sh /opt/agent/entrypoint.sh
RUN chmod 755 /opt/agent/entrypoint.sh

ENTRYPOINT ["/opt/agent/entrypoint.sh"]
