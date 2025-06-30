# Database Logging Implementation

## Overview

The crypto gaming platform now includes comprehensive database logging that captures all HTTP requests, security events, and game actions. This provides complete audit trails, security monitoring, and analytics capabilities.

## What Gets Logged to Database

### 1. HTTP Request Logs (`request_logs` collection)
- **Method**: HTTP method (GET, POST, PUT, DELETE, etc.)
- **Path**: Request URL path
- **Status Code**: HTTP response status code
- **Client IP**: Source IP address
- **User Agent**: Browser/client information
- **Device Fingerprint**: Unique device identifier
- **Player ID**: Associated player (if authenticated)
- **Request Headers**: All request headers (for debugging)
- **Response Headers**: All response headers
- **Process Time**: Request processing duration
- **Error Message**: Any errors that occurred
- **Created At**: Timestamp of the request
- **TTL**: Automatic cleanup after 30 days

### 2. Security Event Logs (`security_logs` collection)
- **Event Type**: Type of security event
  - `failed_login`: Failed authentication attempts
  - `suspicious_activity`: Detected suspicious patterns
  - `ban`: Account bans
  - `cheat_detected`: Anti-cheat violations
- **Player ID**: Associated player (if known)
- **Client IP**: Source IP address
- **Device Fingerprint**: Device identifier
- **User Agent**: Browser/client information
- **Details**: Additional event details
- **Severity**: Event severity (info, warning, error, critical)
- **Created At**: Timestamp of the event
- **TTL**: Automatic cleanup after 90 days

### 3. Game Action Logs (`game_action_logs` collection)
- **Game ID**: Associated game session
- **Player ID**: Player performing the action
- **Action Type**: Type of game action
- **Action Data**: Detailed action information
- **Session ID**: Game session identifier
- **Client IP**: Source IP address
- **Device Fingerprint**: Device identifier
- **Timestamp**: When the action occurred

## Implementation Details

### Middleware Stack
The logging is implemented through a layered middleware approach:

1. **SecurityMiddleware**: Adds security headers
2. **SecurityLoggingMiddleware**: Detects and logs security events
3. **RequestLoggingMiddleware**: Logs all HTTP requests to database

### Logging Service
The `LoggingService` class provides methods to:
- Log requests, security events, and game actions
- Query logs with filtering options
- Generate log statistics
- Clean up old logs automatically
- Export logs in JSON or CSV format

### Database Indexes
Optimized indexes are created for efficient querying:
- **Request Logs**: player_id, method, path, status_code, client_ip, created_at, ttl
- **Security Logs**: player_id, event_type, severity, client_ip, created_at, ttl
- **Game Action Logs**: game_id, player_id, action_type, session_id, timestamp

### TTL (Time To Live)
- Request logs: 30 days
- Security logs: 90 days
- Game action logs: 7 days (no TTL, manual cleanup)

## Admin Panel Integration

### Log Viewing Endpoints
- `GET /api/v1/admin/logs/requests` - View request logs with filtering
- `GET /api/v1/admin/logs/security` - View security event logs
- `GET /api/v1/admin/logs/game-actions` - View game action logs
- `GET /api/v1/admin/logs/statistics` - Get logging statistics

### Log Management Endpoints
- `POST /api/v1/admin/logs/cleanup` - Clean up old logs
- `GET /api/v1/admin/logs/export` - Export logs in JSON/CSV format

### Filtering Options
All log endpoints support filtering by:
- Player ID
- Date range (start_date, end_date)
- Specific criteria (status_code, event_type, action_type, etc.)
- Limit results (default 100, max 1000)

## Security Features

### Device Fingerprinting
Each request generates a unique device fingerprint based on:
- User agent string
- Accept language
- Accept encoding
- Security headers

### Suspicious Activity Detection
The system automatically detects and logs:
- Known malicious user agents (sqlmap, nmap, etc.)
- Suspicious URL patterns (/admin, /.env, etc.)
- Failed authentication attempts
- Unusual request patterns

### Rate Limiting Support
The logging system provides data for implementing rate limiting:
- Track requests per IP
- Monitor authentication failures
- Detect automated attacks

## Performance Considerations

### Asynchronous Logging
All database logging is performed asynchronously to avoid blocking request processing.

### Indexed Queries
Optimized indexes ensure fast log retrieval even with large datasets.

### Automatic Cleanup
TTL indexes automatically remove old logs to prevent database bloat.

### Selective Logging
- Request bodies are not logged for security
- Sensitive headers are filtered
- Health check endpoints are excluded

## Usage Examples

### View Recent Failed Logins
```bash
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8000/api/v1/admin/logs/security?event_type=failed_login&limit=50"
```

### Get Request Statistics
```bash
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8000/api/v1/admin/logs/statistics"
```

### Export Security Logs
```bash
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8000/api/v1/admin/logs/export?log_type=security&format=csv"
```

### View Player Activity
```bash
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8000/api/v1/admin/logs/requests?player_id=<player_id>&limit=100"
```

## Monitoring and Alerts

### Key Metrics to Monitor
- Error rate percentage
- Critical security events count
- Recent activity levels (24h)
- Database size growth

### Alert Thresholds
- Error rate > 5%
- Critical security events > 10 in 1 hour
- Database size > 10GB
- Log cleanup failures

## Configuration

### Environment Variables
```bash
# Enable/disable database logging
ENABLE_DB_LOGGING=true

# Log retention periods (in days)
REQUEST_LOG_RETENTION=30
SECURITY_LOG_RETENTION=90
GAME_ACTION_LOG_RETENTION=7

# Logging exclusions
LOG_EXCLUDE_PATHS=/health,/docs,/openapi.json
```

### Middleware Configuration
```python
# Enable database logging in middleware
app.add_middleware(
    RequestLoggingMiddleware,
    exclude_paths=["/health", "/docs", "/openapi.json"],
    enable_db_logging=True
)
```

## Benefits

1. **Complete Audit Trail**: Every request is logged with full context
2. **Security Monitoring**: Real-time detection of suspicious activities
3. **Performance Analysis**: Track response times and error rates
4. **Compliance**: Meet regulatory requirements for audit logs
5. **Debugging**: Detailed logs for troubleshooting issues
6. **Analytics**: Rich data for business intelligence
7. **Anti-Cheat**: Track game actions for cheat detection
8. **User Behavior**: Understand player patterns and preferences

## Future Enhancements

1. **Real-time Alerts**: Webhook notifications for critical events
2. **Log Aggregation**: Centralized log management system
3. **Advanced Analytics**: Machine learning for anomaly detection
4. **Compliance Reporting**: Automated compliance report generation
5. **Performance Optimization**: Log compression and archiving
6. **Integration**: Connect with external monitoring tools 