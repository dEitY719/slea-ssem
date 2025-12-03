# OIDC Authentication Workflow

## Overview

This document describes the Azure AD OpenID Connect (OIDC) authentication flow used in slea-ssem. This replaced the legacy local login mechanism to provide enterprise-grade Single Sign-On (SSO) integration.

---

## Current Flow (OIDC-based)

### Step-by-Step Process

#### 1. **Initial Page Load**
```
User visits http://localhost:3000
↓
Frontend: LoginPage.tsx renders
↓
Call isAuthenticated()
  ├─ GET /auth/status endpoint
  ├─ Backend checks auth_token cookie
  └─ Returns { authenticated: bool, user_id, knox_id }
```

#### 2. **No Authentication Found**
```
GET /auth/status → 401 Unauthorized (no cookie)
↓
Frontend redirects to Azure AD IDP:
  https://login.microsoftonline.com/{tenant}/oauth2/authorize
  ?client_id={OIDC_CLIENT_ID}
  &redirect_uri={OIDC_REDIRECT_URI}
  &response_type=code
  &scope=openid profile email
```

#### 3. **User Authentication at IDP**
```
User enters credentials at Azure AD login page
↓
IDP validates credentials
↓
IDP redirects browser to Frontend callback URL:
  http://localhost:3000/auth/callback?code=...
```

#### 4. **Frontend Callback Processing**
```
Frontend receives callback with authorization code
↓
parseUserData.ts extracts: knox_id, name, email, dept, business_unit
↓
Frontend makes request to Backend:
  POST /auth
  {
    "code": "{authorization_code}",
    "knox_id": "{knox_id}",
    "name": "{user_name}",
    "email": "{user_email}",
    "dept": "{department}",
    "business_unit": "{business_unit}"
  }
```

#### 5. **Backend OIDC Processing**
```
POST /auth endpoint receives callback:

1. Validate request (code, state, etc.)
2. OIDCAuthService.exchange_code_for_tokens(code)
   ├─ Call Azure AD token endpoint
   └─ Verify signature
3. Extract user data from IDP response
4. AuthService.authenticate_or_create_user(user_data)
   ├─ Query: User.query.filter(User.knox_id == knox_id).first()
   ├─ If not found: Create new User record in DB
   └─ If found: Update last_login timestamp
5. Generate JWT token (HS256, 24-hour expiration)
6. Set HttpOnly cookie in response
   └─ Cookie name: auth_token
   └─ HttpOnly: true (JS cannot access)
7. Return redirect response: HTTP 302 to /home
```

#### 6. **Browser Auto-Redirect & Session Establishment**
```
Backend returns 302 with Set-Cookie header
↓
Browser:
  1. Stores auth_token HttpOnly cookie
  2. Follows redirect to /home
  3. Auto-includes cookie in subsequent requests
```

---

## Key Changes from Legacy Login

### Before (Local Login)
```
Frontend LoginPage
  → User fills form: username, password
  → POST /auth/login
  → Backend: creates User in DB
  → Response: JWT token
  → Frontend: stores in localStorage
  → API requests: Authorization: Bearer {token}
```

### After (OIDC - Current)
```
Frontend LoginPage
  → Checks GET /auth/status
  → No cookie? → Redirect to Azure AD
  → IDP authenticates (secure, external)
  → Backend: receives OIDC callback
  → Backend: creates/updates User in DB
  → Response: HttpOnly cookie
  → API requests: Cookie auto-included
```

---

## Main Changes Summary

### 1. **Auth Mechanism**
- **Before**: Local login (username/password in app)
- **After**: Azure AD OIDC (enterprise SSO)

### 2. **Token Storage**
- **Before**: localStorage (JavaScript-accessible, XSS vulnerable)
- **After**: HttpOnly cookie (JavaScript-inaccessible, XSS protected)

### 3. **Login UI**
- **Before**: Direct login form with username/password input
- **After**: IDP redirect (user logs in at Azure AD, external)

### 4. **Users DB Creation**
- **Before**: Frontend POST /auth/login → Backend creates user
- **After**: Backend OIDC callback (/auth) → Backend creates/updates user

---

## Token Lifecycle

### Generation
```
User authenticates via IDP
  ↓
Backend: AuthService._generate_jwt(knox_id)
  ├─ Payload: { knox_id, iat, exp }
  ├─ Algorithm: HS256
  ├─ Secret: JWT_SECRET_KEY (from .env)
  └─ Expiration: 24 hours
  ↓
Set HttpOnly cookie: auth_token={JWT}
```

### Validation
```
Each API request includes auth_token cookie
  ↓
Backend: AuthService.decode_jwt(token)
  ├─ Verify HS256 signature
  ├─ Check expiration
  └─ Extract knox_id
  ↓
Valid: Continue request with knox_id
Invalid: Return 401 Unauthorized
```

---

## Environment Variables

### Required for OIDC
```env
OIDC_CLIENT_ID=your-azure-app-id
OIDC_CLIENT_SECRET=your-azure-client-secret
OIDC_TENANT_ID=your-tenant-id
OIDC_REDIRECT_URI=http://localhost:3000/auth/callback

JWT_SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24
```

### Development Mode
When `OIDC_CLIENT_ID == "your-azure-app-id"` (default):
- Backend generates mock tokens automatically
- No real Azure AD connection needed
- Each code generates unique user

---

## Security Highlights

- ✅ **HttpOnly Cookies**: Inaccessible to JavaScript
- ✅ **Secure Flag**: HTTPS only in production
- ✅ **SameSite=Strict**: CSRF protection
- ✅ **JWT Signature**: HS256 validation on every request
- ✅ **Expiration**: 24-hour TTL on tokens
- ✅ **State Parameter**: Authorization code interception prevention

---

## Version History

- **2025-11-25**: Initial document creation
  - Documented current OIDC workflow
  - Compared with legacy local login
  - Highlighted key architecture changes
