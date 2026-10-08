FROM python:3.12-slim

RUN pip install --no-cache-dir duckdb pypdf

# The repo is bind-mounted read-only at /workspace, so the src/ packages are put on the
# import path rather than pip-installed (an editable install would write egg-info).
ENV PYTHONPATH=/workspace/src

COPY container_entrypoint.sh /opt/agent/entrypoint.sh
RUN chmod 755 /opt/agent/entrypoint.sh

ENTRYPOINT ["/opt/agent/entrypoint.sh"]
