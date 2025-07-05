# Cookie-Based Authentication Implementation

This document describes the implementation of cookie-based authentication for the gaming platform backend.

## Overview

The authentication system has been updated to use HTTP-only cookies for token storage instead of relying solely on Authorization headers. This provides better security and automatic token management.

## Key Components

### 1. Configuration (`app/core/config.py`)

Added cookie configuration settings:

```python
# Cookie Configuration
cookie_domain: str = os.getenv("COOKIE_DOMAIN", "localhost")
cookie_secure: bool = os.getenv("COOKIE_SECURE", "False").lower() == "true"
cookie_httponly: bool = os.getenv("COOKIE_HTTPONLY", "True").lower() == "true"
cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax")
access_token_cookie_name: str = os.getenv("ACCESS_TOKEN_COOKIE_NAME", "access_token")
refresh_token_cookie_name: str = os.getenv("REFRESH_TOKEN_COOKIE_NAME", "refresh_token")
```

### 2. Cookie Authentication (`app/auth/cookie_auth.py`)

New cookie-based authentication middleware that:
- Extracts tokens from cookies first, then falls back to Authorization headers
- Provides unified authentication for both cookie and header-based tokens
- Includes admin verification functionality

Key functions:
- `get_current_user()`: Required authentication
- `get_current_user_optional()`: Optional authentication
- `verify_admin()`: Admin-only authentication

### 3. Cookie Utilities (`app/utils/cookie_utils.py`)

Utility functions for managing authentication cookies:

- `set_auth_cookies()`: Set access and refresh token cookies with security settings
- `clear_auth_cookies()`: Clear authentication cookies
- `set_cookie_with_options()`: Set custom cookies with specific options

## Updated Endpoints

### Authentication Routes (`app/routes/auth.py`)

#### Register
```python
@router.post("/register", response_model=TokenResponse)
async def register_player(player_data: PlayerCreate, request: Request, response: Response):
    # ... registration logic ...
    
    # Set cookies automatically
    set_auth_cookies(response, access_token, refresh_token)
    
    return TokenResponse(...)
```

#### Login
```python
@router.post("/login", response_model=TokenResponse)
async def login_player(player_data: PlayerLogin, request: Request, response: Response):
    # ... login logic ...
    
    # Set cookies automatically
    set_auth_cookies(response, access_token, refresh_token)
    
    return TokenResponse(...)
```

#### Refresh Token
```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, response: Response):
    # Get refresh token from cookies
    refresh_token = cookie_auth.get_refresh_token_from_cookies(request)
    
    # ... refresh logic ...
    
    # Set new cookies
    set_auth_cookies(response, access_token, new_refresh_token)
    
    return TokenResponse(...)
```

#### Logout
```python
@router.post("/logout")
async def logout(request: Request, response: Response):
    # ... logout logic ...
    
    # Clear cookies
    clear_auth_cookies(response)
    
    return {"message": "Successfully logged out"}
```

#### Get Current User
```python
@router.get("/me", response_model=PlayerResponse)
async def get_current_player(current_user: dict = Depends(get_current_user)):
    # Uses cookie-based authentication automatically
    # ...
```

### Admin Routes (`app/routes/admin.py`)

#### Admin Login
```python
@router.post("/login", response_model=TokenResponse)
async def admin_login(admin_data: AdminLogin, response: Response):
    # ... admin login logic ...
    
    # Set cookies automatically
    set_auth_cookies(response, access_token, refresh_token)
    
    return TokenResponse(...)
```

#### Admin Endpoints
```python
@router.get("/dashboard")
async def get_admin_dashboard(current_admin: dict = Depends(verify_admin)):
    # Uses cookie-based admin authentication
    # ...

@router.get("/analytics/platform")
async def get_platform_analytics(current_admin: dict = Depends(verify_admin)):
    # Uses cookie-based admin authentication
    # ...
```

## Environment Variables

Add these to your `.env` file:

```env
# Cookie Configuration
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False
COOKIE_HTTPONLY=True
COOKIE_SAMESITE=lax
ACCESS_TOKEN_COOKIE_NAME=access_token
REFRESH_TOKEN_COOKIE_NAME=refresh_token
```

## Security Features

1. **HTTP-Only Cookies**: Prevents XSS attacks by making cookies inaccessible to JavaScript
2. **Secure Flag**: When enabled, cookies are only sent over HTTPS
3. **SameSite Attribute**: Prevents CSRF attacks
4. **Automatic Token Management**: Tokens are automatically included in requests
5. **Fallback Support**: Still supports Authorization headers for API clients

## Usage Examples

### Frontend Integration

The frontend no longer needs to manually manage tokens. Cookies are automatically sent with requests:

```javascript
// Login
const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(loginData)
});

// Cookies are automatically set and sent with subsequent requests
const userData = await fetch('/auth/me');
```

### API Client Integration

API clients can still use Authorization headers:

```javascript
// API client with Authorization header
const response = await fetch('/auth/me', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});
```

### Token Refresh

Refresh tokens are automatically handled:

```javascript
// Refresh endpoint automatically uses cookies
const response = await fetch('/auth/refresh', {
    method: 'POST'
});
```

## Migration Notes

1. **Backward Compatibility**: The system still supports Authorization headers for API clients
2. **Automatic Migration**: Existing clients will continue to work
3. **Enhanced Security**: New cookie-based system provides better security
4. **Simplified Frontend**: Frontend applications no longer need to manually manage tokens

## Testing

Test the cookie-based authentication:

1. **Login/Register**: Verify cookies are set
2. **Protected Endpoints**: Verify authentication works with cookies
3. **Token Refresh**: Verify refresh works automatically
4. **Logout**: Verify cookies are cleared
5. **Admin Endpoints**: Verify admin authentication works

## Troubleshooting

### Common Issues

1. **CORS Issues**: Ensure CORS is configured to allow credentials
2. **Cookie Not Set**: Check cookie domain and secure settings
3. **Authentication Fails**: Verify token verification logic
4. **Admin Access Denied**: Check admin verification in cookie_auth.py

### Debug Steps

1. Check browser developer tools for cookies
2. Verify environment variables are set correctly
3. Check server logs for authentication errors
4. Test with both cookie and header authentication 