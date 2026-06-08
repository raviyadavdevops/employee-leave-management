"""Deployment documentation."""

# Deployment Guide

## Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 14+ (or use Docker Compose provided)
- RabbitMQ 3.13+ (or use Docker Compose provided)
- Python 3.13 (for local development)

## Quick Start (Docker Compose)

### 1. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

**IMPORTANT**: Update `.env` with production values:
- Change `JWT_SECRET` to a secure random string
- Update database passwords
- Configure CORS origins for your domain

### 2. Build and Run

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
curl http://localhost:8080/health
```

### 3. Run Database Migrations

```bash
# Auth service migrations
docker-compose exec auth-service alembic upgrade head

# User service migrations
docker-compose exec user-service alembic upgrade head

# Leave service migrations
docker-compose exec leave-service alembic upgrade head

# Notification service migrations
docker-compose exec notification-service alembic upgrade head
```

### 4. Verify Deployment

```bash
# Check all services
curl http://localhost:8080/api/v1/auth/health
curl http://localhost:8080/api/v1/users/health
curl http://localhost:8080/api/v1/leaves/health
curl http://localhost:8080/api/v1/notifications/health
```

## Development Mode

For local development with hot reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This mounts source code as volumes and enables auto-reload.

## Production Considerations

### Security

1. **JWT Secrets**: Generate strong random secrets
2. **Database**: Use managed PostgreSQL (RDS, Cloud SQL)
3. **RabbitMQ**: Use managed service or secure deployment
4. **HTTPS**: Deploy NGINX with TLS certificates
5. **Secrets Management**: Use vault/secrets manager

### Scaling

- **Horizontal**: Scale services independently via `docker-compose scale`
- **Database**: Use connection pooling (configured in each service)
- **RabbitMQ**: Configure clustering for high availability

### Monitoring

- **Logs**: Aggregate logs to ELK or CloudWatch
- **Metrics**: Add Prometheus endpoints
- **Tracing**: Correlation IDs included in all logs

## Troubleshooting

**Services won't start:**
```bash
docker-compose down -v
docker-compose up --build
```

**Database connection errors:**
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running: `docker-compose ps postgres`

**RabbitMQ issues:**
- Check RabbitMQ management UI: http://localhost:15672
- Default credentials: rabbitmq/rabbitmq

**Port conflicts:**
- Update port mappings in `docker-compose.yml`
