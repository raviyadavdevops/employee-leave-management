"""API Usage Guide."""

# API Usage Guide

## Authentication Flow

### 1. Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "employee@company.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2. Use Access Token

Include token in Authorization header for all authenticated requests:

```bash
Authorization: Bearer eyJhbGc...
```

### 3. Refresh Token

When access token expires (15 minutes):

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

## Common Scenarios

### Employee: View Leave Balances

```bash
GET /api/v1/leave-balances/me
Authorization: Bearer {access_token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "employee_id": "uuid",
    "leave_type_id": 1,
    "leave_type_name": "annual",
    "leave_type_display_name": "Annual Leave",
    "year": 2026,
    "total_allocated": 20,
    "available": 15,
    "provisional": 3,
    "consumed": 2
  }
]
```

### Employee: Submit Leave Request

```bash
POST /api/v1/leave-requests
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "leave_type_id": 1,
  "start_date": "2026-07-01",
  "end_date": "2026-07-05",
  "reason": "Family vacation"
}
```

**Response:**
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "leave_type_id": 1,
  "leave_type_name": "annual",
  "start_date": "2026-07-01",
  "end_date": "2026-07-05",
  "days_requested": 5,
  "reason": "Family vacation",
  "status": "pending",
  "created_at": "2026-06-04T10:00:00Z"
}
```

### Employee: Track Request Status

```bash
GET /api/v1/leave-requests
Authorization: Bearer {access_token}
```

Optional filters:
- `?status=pending` - Only pending requests
- `?status=approved` - Only approved requests

### Manager: View Team Requests

```bash
GET /api/v1/leave-requests/team/requests
Authorization: Bearer {access_token}
```

Optional: `?status=pending`

### Manager: Approve Request

```bash
POST /api/v1/leave-requests/{request_id}/approve
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "comment": "Approved. Enjoy your vacation!"
}
```

### Manager: Reject Request

```bash
POST /api/v1/leave-requests/{request_id}/reject
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "comment": "Team coverage insufficient during this period."
}
```

**Note**: Comment is mandatory for rejections.

### Manager: View Team Calendar

```bash
GET /api/v1/leave-requests/team/calendar
Authorization: Bearer {access_token}
```

Optional filters:
- `?start_date=2026-07-01`
- `?end_date=2026-07-31`

**Response includes:**
- Team leave entries
- Coverage warnings (>30% on leave)

### View Notifications

```bash
GET /api/v1/notifications/me
Authorization: Bearer {access_token}
```

Optional:
- `?status=sent` - Only delivered notifications
- `?limit=20` - Limit results
- `?offset=0` - Pagination offset

## Error Responses

All errors follow standard format:

```json
{
  "error": "ValidationException",
  "detail": "end_date must be after start_date",
  "status_code": 422,
  "correlation_id": "uuid"
}
```

Common status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (overlapping requests)
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

API gateway enforces rate limiting:
- 100 requests per minute per IP
- 1000 requests per hour per IP

Exceeded limits return `429 Too Many Requests`.

## CORS

Allowed origins configured via `CORS_ORIGINS` environment variable.

Default development: `http://localhost:3000,http://localhost:8080`
