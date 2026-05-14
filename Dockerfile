FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for downloading & processing
RUN apt-get update && apt-get install -y \
    git \
    wget \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server ./mcp_server
COPY scripts ./scripts

# Run as a non-root user whose UID/GID match the host user, so files written
# into the bind-mounted ./data dir are owned by the host user, not root.
# A real /etc/passwd entry + home dir is required (not just a numeric UID):
# torch/transformers call pwd.getpwuid() / getpass.getuser() at import time
# and crash with "uid not found" on a bare numeric UID.
# Placed last so editing this stage doesn't bust the apt/pip layer cache.
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" appuser \
    && useradd -u "${UID}" -g "${GID}" -m -d /home/appuser appuser
ENV HOME=/home/appuser
USER appuser

# Keep container running for manual script execution
CMD ["tail", "-f", "/dev/null"]
