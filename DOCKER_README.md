#Auto generated file - might be incorrect
# Docker Development Setup for Event Scheduling System

This document provides instructions for running the Event Scheduling System using Docker for development.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd Assignment

# Copy environment file
cp env.example .env
# Edit .env file with your settings
```

### 2. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f web
```

### 3. Run Migrations

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser (optional)
docker-compose exec web python manage.py createsuperuser
```

### 4. Access the Application

- **Django Admin**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/

## Docker Commands

### Development Commands

```bash
# Start services in background
docker-compose up -d

# Start services with logs
docker-compose up

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs web
docker-compose logs -f web  # Follow logs

# Execute commands in container
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py test
```

### Database Commands

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Reset database (WARNING: This will delete all data)
docker-compose exec web python manage.py flush

# Create database backup
docker-compose exec web python manage.py dumpdata > backup.json

# Load database backup
docker-compose exec web python manage.py loaddata backup.json
```

### Testing Commands

```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test events
docker-compose exec web python manage.py test bookings

# Run with coverage
docker-compose exec web python -m pytest --cov=.
```

## File Structure

```
Assignment/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Multi-container setup
├── .dockerignore             # Files to exclude from Docker build
├── requirements.txt          # Python dependencies
├── env.example              # Environment variables template
├── DOCKER_README.md         # This file
└── event_scheduling_system/ # Django project
    ├── manage.py
    ├── event_scheduling_system/
    ├── events/
    ├── bookings/
    └── user/
```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and customize:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (for future PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### Docker Compose Configuration

The `docker-compose.yml` includes:

- **Web service**: Django application
- **Volume mounting**: For development hot-reload
- **Port mapping**: 8000:8000
- **Environment variables**: From .env file
- **Networks**: Isolated network for services

## Development Workflow

### 1. Making Changes

```bash
# Start services
docker-compose up -d

# Make code changes (hot-reload enabled)
# Changes are automatically reflected

# Run tests after changes
docker-compose exec web python manage.py test
```

### 2. Adding Dependencies

```bash
# Add to requirements.txt
# Rebuild container
docker-compose up --build
```

### 3. Database Changes

```bash
# Create new migration
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```



## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Or use different port in docker-compose.yml
   ```

2. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Database issues**
   ```bash
   # Reset database
   docker-compose down
   docker volume prune
   docker-compose up --build
   ```

4. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs web
   # Check container status
   docker-compose ps
   ```

### Debugging

```bash
# Access container shell
docker-compose exec web bash

# Check Django settings
docker-compose exec web python manage.py check

# Check database connection
docker-compose exec web python manage.py dbshell
```

## API Endpoints

Once running, access these endpoints:

- **API Root**: `GET /api/`
- **Events**: `GET /api/events/`
- **Bookings**: `GET /api/bookings/`
- **Users**: `GET /api/users/`
- **Admin**: `GET /admin/`
- **API Docs**: `GET /api/schema/swagger-ui/`

## Next Steps

1. **Add PostgreSQL**: Uncomment database service in docker-compose.yml when needed
2. **Add Redis**: For caching and session storage
3. **Add Nginx**: For reverse proxy and static files
4. **Add CI/CD**: GitHub Actions or GitLab CI
5. **Add Monitoring**: Health checks and logging

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Docker and Django logs
3. Ensure all prerequisites are met
4. Verify environment variables are set correctly
