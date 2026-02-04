FROM python:3.11-slim

# Set metadata
LABEL maintainer="your-email@example.com"
LABEL description="Linux ISO Torrent Updater for Transmission"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Copy application files
COPY linux_iso_torrent_updater.py .
COPY web_interface.py .
COPY templates/ templates/
COPY static/ static/
COPY entrypoint.sh .

# Note: Environment variables should be provided via docker run -e or --env-file
# The .env files are not copied into the image for security reasons

# Ensure scripts are executable
RUN chmod +x linux_iso_torrent_updater.py web_interface.py entrypoint.sh

# Create a non-root user to run the application
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app /opt/venv

# Switch to non-root user
USER appuser

# Set PATH to use the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Health check (optional - checks if Python can import required modules)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import transmission_rpc; import requests; import bs4; import flask; import apscheduler" || exit 1

# Expose port for web interface
EXPOSE 8084

# Run the script
# Use ENTRYPOINT with CMD to allow passing arguments
# For web mode: docker run ... --web
# For CLI mode: docker run ... --distro ubuntu
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []
