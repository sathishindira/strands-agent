FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including Docker CLI dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    graphviz \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add Docker's official GPG key
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg

# Setup Docker repository for Debian
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker CLI and clean up in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional: install uv if needed (skip if not used in final app)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -sf $(find / -name uv -type f | head -1) /usr/local/bin/uv && \
    ln -sf $(find / -name uvx -type f | head -1) /usr/local/bin/uvx

# Reinstall python with uv (optional, but redundant in this case)
RUN uv python install 3.11

# Extra Python packages (optional)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir diagrams

# Create output directories with proper permissions
RUN mkdir -p /app/generated-diagrams /tmp/generated-diagrams && \
    chmod 755 /app/generated-diagrams /tmp/generated-diagrams

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV DIAGRAM_OUTPUT_DIR=/tmp/generated-diagrams

# Expose port used by Streamlit
EXPOSE 8501

# Default command to run the Streamlit app
CMD ["streamlit", "run", "app.py"]
