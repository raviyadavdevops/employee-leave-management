# Employee Leave Management System

A comprehensive microservices-based backend system for managing employee leave requests, approvals, and balances. Built with FastAPI, PostgreSQL, RabbitMQ, and Docker.

**Repository:** [github.com/raviyadavdevops/employee-leave-management](https://github.com/raviyadavdevops/employee-leave-management)

## 🏗️ Architecture Overview

The system consists of 4 independent microservices orchestrated via Docker Compose:

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX API Gateway                     │
│                    (Port 8080)                           │
└────────┬────────────┬────────────┬─────────────────────┘
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌─────────┐  ┌──────────┐
    │  Auth  │  │  User   │  │  Leave   │
    │Service │  │ Service │  │ Service  │
    │:8000   │  │ :8001   │  │ :8002    │
    └────┬───┘  └────┬────┘  └────┬─────┘
         │           │            │
         │           │            │ (events)
         │           │            ▼
         │           │       ┌──────────────┐
         │           │       │Notification  │
         │           │       │Service       │
         │           │       └──────┬───────┘
         │           │              │
         ▼           ▼              ▼
    ┌──────────────────────────────────┐
    │      PostgreSQL Database         │
    │   Schemas: auth, users, leaves,  │
    │          notifications            │
    └──────────────────────────────────┘
                    │
                    ▼
            ┌──────────────┐
            │  RabbitMQ    │
            │ Message Queue│
            └──────────────┘
```

### Services

- **Auth Service** (`:8000`): JWT-based authentication, token generation/validation
- **User Service** (`:8001`): Employee & manager profiles, reporting hierarchy
- **Leave Service** (`:8002`): Leave requests, approvals, balance management, event publishing
- **Notification Service**: RabbitMQ consumer for async notification delivery
- **NGINX Gateway** (`:8080`): API gateway with path-based routing
- **PostgreSQL**: Database with schema isolation per service
- **RabbitMQ**: Message queue for event-driven notifications

## 🚀 Quick Start

### Prerequisites

- Docker 24+ and Docker Compose 2.20+
- Git

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd employee-leave-management

# 2. Copy environment configuration
cp .env.example .env

# 3. Update JWT secret in .env (required for production)
# Edit .env and change JWT_SECRET to a secure random string

# 4. Start all services
docker-compose up -d

# 5. Verify services are running
docker-compose ps

# 6. Access the API
curl http://localhost:8080/
# Expected: {"status":"ok","message":"Employee Leave Management API Gateway","version":"1.0.0"}
```

### Development Mode (with hot reload)

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Services will auto-reload on code changes
```

## 📚 API Documentation

### Base URL
- **Production**: `http://localhost:8080`
- **Direct Service Access** (development):
  - Auth: `http://localhost:8000`
  - User: `http://localhost:8001`
  - Leave: `http://localhost:8002`

### Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login (returns access + refresh tokens) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout (blacklist refresh token) |
| GET | `/api/v1/auth/health` | Health check |

### User Endpoints (`/api/v1/users`, `/api/v1/employees`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/employees` | Create employee | Yes (Manager) |
| GET | `/api/v1/employees/me` | Get current user profile | Yes |
| GET | `/api/v1/employees/{id}` | Get employee by ID | Yes |
| GET | `/api/v1/employees/team/members` | Get team members (managers) | Yes (Manager) |
| GET | `/api/v1/users/health` | Health check | No |

### Leave Endpoints (`/api/v1/leaves`, `/api/v1/leave-requests`, `/api/v1/leave-balances`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/leave-balances/me` | Get my leave balances | Yes |
| POST | `/api/v1/leave-requests` | Submit leave request | Yes |
| GET | `/api/v1/leave-requests` | Get my leave requests | Yes |
| GET | `/api/v1/leave-requests/{id}` | Get leave request by ID | Yes |
| GET | `/api/v1/leave-requests/team/requests` | Get team leave requests | Yes (Manager) |
| POST | `/api/v1/leave-requests/{id}/approve` | Approve leave request | Yes (Manager) |
| POST | `/api/v1/leave-requests/{id}/reject` | Reject leave request | Yes (Manager) |
| GET | `/api/v1/leaves/health` | Health check | No |

### OpenAPI Documentation

API contracts (OpenAPI 3.0 specifications):

- **Auth Service**: [docs/contracts/auth-service.yml](docs/contracts/auth-service.yml)
- **User Service**: [docs/contracts/user-service.yml](docs/contracts/user-service.yml)
- **Leave Service**: [docs/contracts/leave-service.yml](docs/contracts/leave-service.yml)
- **Notification Service**: [docs/contracts/notification-service.yml](docs/contracts/notification-service.yml)

Interactive API documentation is available when running in DEBUG mode:
- Auth Service: http://localhost:8000/docs
- User Service: http://localhost:8001/docs
- Leave Service: http://localhost:8002/docs

## 🗄️ Database

### Schema Design

Each microservice has its own PostgreSQL schema for data isolation:

- `auth`: User credentials, roles, refresh tokens
- `users`: Employee profiles, reporting hierarchy
- `leaves`: Leave types, balances, requests, transactions
- `notifications`: Notification delivery logs

### Running Migrations

```bash
# Auth Service migrations
docker-compose exec auth-service alembic upgrade head

# User Service migrations
docker-compose exec user-service alembic upgrade head

# Leave Service migrations
docker-compose exec leave-service alembic upgrade head

# Notification Service migrations
docker-compose exec notification-service alembic upgrade head
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d leave_management

# View schemas
\dn

# View tables in a schema
\dt auth.*
\dt users.*
\dt leaves.*
\dt notifications.*
```

## 🐰 RabbitMQ

### Management Interface

Access RabbitMQ Management UI:
- **URL**: http://localhost:15672
- **Username**: `rabbitmq` (see `.env`)
- **Password**: `rabbitmq` (see `.env`)

### Event Flow

1. Leave Service publishes events when leave requests are created/approved/rejected
2. Notification Service consumes events and sends notifications
3. Events are persisted to PostgreSQL for audit trail

## 🧪 API Testing (Postman)

Use the provided collection at repository root:

- `demo.postman_collection.json`

### Import and Run

1. Import `demo.postman_collection.json` into Postman.
2. Disable proxy for local requests in Postman settings:
   - Turn off `Global Proxy Configuration`
   - Turn off `Use System Proxy`
   - Add `localhost,127.0.0.1` in no-proxy bypass list
3. Run requests in this order:
   - `02 Auth > Login Manager`
   - `02 Auth > Login Employee`
   - `02 Auth > Verify Manager Token`
   - `02 Auth > Verify Employee Token`
   - Then run `03 Employees` and remaining folders

### Notes

- Collection variables are namespaced with `elm*` to avoid collisions with existing Postman env/global variables.
- Base URL variable is `elmApiBaseUrl` (default: `http://127.0.0.1:8080`).
- If `auth-service` is restarted/rebuilt, run login requests again to regenerate fresh tokens.

### Minimal cURL smoke checks

```bash
curl -s http://localhost:8080/
curl -s http://localhost:8080/api/v1/auth/health
curl -s http://localhost:8080/api/v1/users/health
curl -s http://localhost:8080/api/v1/leaves/health
```

## 📂 Project Structure

```
employee-leave-management/
├── services/                    # Microservices
│   ├── auth-service/           # JWT authentication
│   ├── user-service/           # User & employee management
│   ├── leave-service/          # Leave request management
│   └── notification-service/   # Async notifications
├── shared/                      # Shared utilities
│   └── common/                 # Logging, auth, exceptions
├── infrastructure/             # Infrastructure configuration
│   ├── nginx/                  # API gateway
│   ├── postgres/               # Database init scripts
│   └── rabbitmq/               # Message queue config
├── docs/                        # Documentation
│   ├── api-usage.md            # API usage guide
│   ├── deployment.md           # Deployment guide
│   └── contracts/              # OpenAPI specifications
├── docker-compose.yml          # Production orchestration
├── docker-compose.dev.yml      # Development overrides
└── .env.example                # Environment template
```

## 🛠️ Development

### Adding a New Feature

1. Review the API contracts in `docs/contracts/`
2. Follow TDD: write tests first, then implementation
3. Use structured logging with correlation IDs
4. Update API documentation if adding new endpoints

### Code Standards

- **Clean Architecture**: Repository pattern (data access) + Service pattern (business logic)
- **Type Safety**: Pydantic schemas for all requests/responses
- **Testing**: 80% minimum coverage (100% for business-critical paths)
- **Security**: JWT auth, input validation, no secrets in code
- **Logging**: Structured JSON logs with correlation IDs

## 🔧 Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart auth-service

# Rebuild containers
docker-compose up --build
```

### Database connection errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify schemas exist
docker-compose exec postgres psql -U postgres -d leave_management -c "\dn"
```

### RabbitMQ connection errors

```bash
# Check RabbitMQ health
docker-compose ps rabbitmq

# View RabbitMQ logs
docker-compose logs rabbitmq

# Verify queues exist (via Management UI)
# http://localhost:15672/#/queues
```

## 📖 Additional Documentation

- **API Contracts (OpenAPI)**: [docs/contracts/](docs/contracts/)
- **API Usage Guide**: [docs/api-usage.md](docs/api-usage.md)
- **Deployment Guide**: [docs/deployment.md](docs/deployment.md)

## 📄 License

[Add your license here]

## 👥 Contributing

[Add contribution guidelines here]
