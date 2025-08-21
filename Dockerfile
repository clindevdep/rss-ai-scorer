# RSS AI Scorer - Production Docker Container
# Based on LinuxServer.io base with proper init system

FROM lscr.io/linuxserver/baseimage-ubuntu:jammy

# Set version label
LABEL version="1.0.0"
LABEL description="RSS AI Scorer - AI-powered RSS article scoring system"
LABEL maintainer="clindevdep"

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY topic_scores_100_personalized.json ./
COPY templates/ ./templates/
COPY static/ ./static/

# Create data directory for persistence
RUN mkdir -p /app/data

# Copy init scripts
COPY docker/init/ /etc/cont-init.d/
RUN chmod +x /etc/cont-init.d/*

# Set proper permissions
RUN chown -R abc:abc /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command - run web application
CMD ["/init"]
