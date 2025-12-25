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

# Keep container running for manual script execution
CMD ["tail", "-f", "/dev/null"]
