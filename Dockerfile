# Use Python 3.9 Alpine image for smaller size and security
FROM python:3.9-alpine3.13  

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=event_scheduling_system.settings

# Set work directory
WORKDIR /app

# Install system dependencies for Alpine Linux
RUN apk update \
    && apk add --no-cache \
        gcc \
        g++ \
        musl-dev \
        postgresql-dev \
        python3-dev \
    && rm -rf /var/cache/apk/*

# Create a non-root user for security (Alpine Linux)
RUN addgroup -g 1000 django && adduser -D -s /bin/sh -u 1000 -G django django

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/static /app/media \
    && chown -R django:django /app

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py check || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
