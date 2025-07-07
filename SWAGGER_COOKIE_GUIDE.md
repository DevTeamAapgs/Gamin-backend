# Swagger UI with Cookie Authentication Guide

This guide explains how to use Swagger UI with the new cookie-based authentication system.

## Overview

Swagger UI has been configured to work with both cookie-based authentication and traditional Bearer token authentication. This provides flexibility for testing and development.

## How Swagger UI Works with Cookies

### 1. **Automatic Cookie Handling**
- When you make requests through Swagger UI, cookies are automatically included
- After login/register, cookies are set and subsequent requests use them
- No manual token management needed in Swagger UI

### 2. **Dual Authentication Support**
- **Primary**: Cookie-based authentication (automatic)
- **Fallback**: Bearer token authentication (manual)

## Using Swagger UI with Cookie Authentication

### Step 1: Access Swagger UI
1. Start your backend server
2. Navigate to `http://localhost:8000/docs`
3. You'll see the Swagger UI interface

### Step 2: Authentication Flow

#### Option A: Cookie-Based (Recommended)
1. **Register/Login First**
   - Use the `/api/v1/auth/register` or `/api/v1/auth/login` endpoint
   - Execute the request in Swagger UI
   - Cookies are automatically set in your browser

2. **Access Protected Endpoints**
   - Navigate to any protected endpoint (e.g., `/api/v1/auth/me`)
   - Execute the request
   - Swagger UI automatically includes the cookies

#### Option B: Bearer Token (Fallback)
1. **Get Token**
   - Use `/api/v1/auth/register` or `/api/v1/auth/login`
   - Copy the `access_token` from the response

2. **Authorize**
   - Click the "Authorize" button in Swagger UI
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

3. **Access Protected Endpoints**
   - All subsequent requests will include the Bearer token

## Swagger UI Configuration

The FastAPI app has been configured with enhanced Swagger UI settings:

```python
swagger_ui_parameters={
    "persistAuthorization": True,  # Keeps authorization across requests
    "displayRequestDuration": True,  # Shows request timing
    "tryItOutEnabled": True,  # Enables "Try it out" by default
    "requestSnippetsEnabled": True,  # Shows code snippets
    "defaultModelsExpandDepth": 1,
    "defaultModelExpandDepth": 1,
    "docExpansion": "list",  # Shows all endpoints
    "filter": True,  # Enables search/filter
    "showExtensions": True,
    "showCommonExtensions": True,
    "syntaxHighlight.theme": "monokai",  # Dark theme
    "syntaxHighlight.activated": True,
}
```

## OpenAPI Security Schemes

The API documentation includes two security schemes:

### 1. Cookie Authentication
```yaml
cookieAuth:
  type: apiKey
  in: cookie
  name: access_token
  description: Access token stored in HTTP-only cookie
```

### 2. Bearer Authentication
```yaml
bearerAuth:
  type: http
  scheme: bearer
  bearerFormat: JWT
  description: Bearer token for API clients (fallback)
```

## Testing Workflow

### Complete Testing Flow

1. **Start the Server**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Open Swagger UI**
   - Go to `http://localhost:8000/docs`

3. **Test Registration**
   - Find `/api/v1/auth/register`
   - Click "Try it out"
   - Enter test data:
   ```json
   {
     "wallet_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
     "username": "testuser",
     "email": "test@example.com",
     "device_fingerprint": "swagger-test"
   }
   ```
   - Execute
   - Check response for tokens and cookies

4. **Test Protected Endpoint**
   - Find `/api/v1/auth/me`
   - Click "Try it out"
   - Execute (no authorization needed - cookies are automatic)
   - Should return user data

5. **Test Admin Login**
   - Find `/api/v1/admin/login`
   - Click "Try it out"
   - Enter admin credentials
   - Execute
   - Cookies are set for admin access

6. **Test Admin Endpoints**
   - Find `/api/v1/admin/dashboard`
   - Click "Try it out"
   - Execute (uses admin cookies automatically)

## Browser Developer Tools

To verify cookies are working:

1. **Open Developer Tools** (F12)
2. **Go to Application/Storage tab**
3. **Check Cookies**
   - Look for `access_token` and `refresh_token` cookies
   - Verify they're set for `localhost:8000`

## Troubleshooting

### Common Issues

1. **"Not authenticated" Error**
   - Make sure you've logged in first
   - Check browser cookies
   - Try refreshing the page

2. **Cookies Not Set**
   - Check CORS configuration
   - Verify cookie domain settings
   - Check browser security settings

3. **Admin Access Denied**
   - Ensure you're using admin login endpoint
   - Check admin credentials
   - Verify admin user exists in database

### Debug Steps

1. **Check Network Tab**
   - Open Developer Tools → Network
   - Make a request
   - Check if cookies are sent in request headers

2. **Check Console**
   - Look for any JavaScript errors
   - Check for CORS errors

3. **Verify Environment**
   - Check `.env` file for cookie settings
   - Ensure server is running on correct port

## Advanced Usage

### Custom Headers
You can add custom headers in Swagger UI:
1. Click "Try it out"
2. Scroll to "Parameters" section
3. Add custom headers if needed

### Testing Different Scenarios
- **New User**: Use registration endpoint
- **Existing User**: Use login endpoint
- **Admin Access**: Use admin login endpoint
- **Token Refresh**: Use refresh endpoint (automatic with cookies)

### API Client Testing
For testing with external tools (Postman, curl):
- Use Bearer token authentication
- Include `Authorization: Bearer <token>` header

## Security Notes

1. **HTTP-Only Cookies**: Cookies are HTTP-only (not accessible via JavaScript)
2. **Secure Flag**: Set to `True` in production (HTTPS required)
3. **SameSite**: Configured to prevent CSRF attacks
4. **Automatic Cleanup**: Cookies expire automatically

## Best Practices

1. **Always Login First**: Before testing protected endpoints
2. **Use Cookie Auth**: For web applications and Swagger UI
3. **Use Bearer Auth**: For API clients and external tools
4. **Test Both**: Verify both authentication methods work
5. **Check Cookies**: Use browser dev tools to verify cookie behavior

## Example Test Sequence

```bash
# 1. Register new user
POST /api/v1/auth/register
{
  "wallet_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
  "username": "swaggeruser",
  "email": "swagger@test.com",
  "device_fingerprint": "swagger-ui"
}

# 2. Get current user (uses cookies automatically)
GET /api/v1/auth/me

# 3. Refresh token (uses cookies automatically)
POST /api/v1/auth/refresh

# 4. Admin login
POST /api/v1/admin/login
{
  "username": "admin",
  "password": "adminpass"
}

# 5. Access admin dashboard (uses admin cookies)
GET /api/v1/admin/dashboard

# 6. Logout (clears cookies)
POST /api/v1/auth/logout
```

This setup provides a seamless testing experience in Swagger UI while maintaining security and flexibility for different client types.

## Authentication Types

### 1. Regular Player Authentication
For player-specific endpoints (auth, player, game):
- Use `/api/v1/auth/login` or `/api/v1/auth/register`
- These create tokens without admin privileges

### 2. Admin Authentication (Required for Roles)
For admin and roles endpoints:
- **Use `/api/v1/admin/login`** - This is crucial for admin access
- This creates tokens with `is_admin: True` flag
- Required for all roles management endpoints

## Step-by-Step Authentication in Swagger UI

### For Admin/Roles Access:

1. **Open Swagger UI** at `/docs`

2. **Find the Admin Login endpoint**:
   - Navigate to the "Admin" section
   - Find `POST /api/v1/admin/login`

3. **Login with admin credentials**:
   ```json
   {
     "username": "admin@example.com",
     "password": "your_admin_password"
   }
   ```

4. **Execute the login request**
   - This will set authentication cookies automatically
   - The response will include access and refresh tokens

5. **Access Roles endpoints**:
   - Navigate to the "Roles" section
   - All endpoints should now show a lock icon 🔒
   - Click "Authorize" button if needed
   - You can now test roles endpoints

### For Regular Player Access:

1. **Use `/api/v1/auth/login`** or `/api/v1/auth/register`
2. **Login with player credentials**:
   ```json
   {
     "wallet_address": "0x...",
     "device_fingerprint": "device123"
   }
   ```

## Important Notes

- **Admin tokens** include `is_admin: True` in the payload
- **Player tokens** do not include admin privileges
- **Roles endpoints** require admin authentication
- **Cookies are automatically set** when using the login endpoints
- **Swagger UI persists authorization** between requests

## Troubleshooting

### If Roles endpoints show "Unauthorized":
1. Make sure you logged in via `/api/v1/admin/login`
2. Check that you're using admin credentials
3. Verify the admin account has `is_admin: True` in the database

### If authentication doesn't persist:
1. Check browser cookie settings
2. Ensure `withCredentials: true` is set in Swagger UI
3. Try refreshing the page and re-authenticating

## Database Setup

Ensure you have an admin user in the database:
```javascript
{
  "username": "admin",
  "email": "admin@example.com", 
  "password_hash": "hashed_password",
  "is_admin": true,
  "is_active": true
}
``` 