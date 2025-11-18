# Frontend Error Handling Guide

## Overview

This document provides comprehensive guidance on handling errors in the frontend when calling backend APIs, particularly for the question generation workflow where transient failures may occur.

## Error Categories

### 1. **Transient Errors** (Recoverable with Retry)

These are temporary failures that may succeed on retry:

- Network timeouts
- Server temporarily unavailable (5xx errors with auto-retry on backend)
- Rate limiting (429 Too Many Requests)

**Backend Support**: The `/questions/generate` endpoint now implements automatic retry with exponential backoff (up to 3 attempts). Frontend should wait for the response even if it takes longer.

**Frontend Responsibility**:

- Implement request timeout (20-30 seconds) to account for backend retries
- Show loading state to user during the wait
- Do NOT retry on the frontend (backend handles this automatically)

### 2. **Validation Errors** (Client Mistake)

These indicate the request itself is invalid:

- Missing required fields (400 Bad Request)
- Invalid input format (400 Bad Request)
- Invalid session ID (404 Not Found)

**Frontend Responsibility**:

- Validate inputs before sending request
- Show user-friendly error message
- Do NOT retry (the error will persist)
- Guide user to fix the issue

### 3. **Authorization Errors** (Authentication/Permission)

These indicate the user is not allowed to perform the action:

- Not authenticated (401 Unauthorized)
- Not authorized for this resource (403 Forbidden)

**Frontend Responsibility**:

- Redirect to login page (401)
- Show access denied message (403)
- Do NOT retry

### 4. **Server Errors** (Unrecoverable)

These are permanent failures in the backend:

- Database connection error
- Unexpected exception (500 Internal Server Error)
- Maximum retry attempts exhausted on backend

**Frontend Responsibility**:

- Show error message to user
- Log the error for debugging
- Offer "Try Again Later" option
- Do NOT retry immediately (could be overwhelming the server)

## Implementation Pattern

### Basic Error Handling Flow

```typescript
async function generateQuestions(sessionId: string): Promise<void> {
  try {
    setIsLoading(true);
    setError(null);

    const response = await fetch(`/api/questions/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
      timeout: 30000, // 30 second timeout for backend retries
    });

    // Handle HTTP errors
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }

    const data = await response.json();

    // Success
    setQuestions(data.questions);
    setTokensUsed(data.total_tokens);

  } catch (error) {
    handleError(error);
  } finally {
    setIsLoading(false);
  }
}
```

### Specific Error Handlers

#### For Question Generation Endpoint

```typescript
function handleQuestionGenerationError(error: Error): void {
  if (error instanceof NetworkError) {
    // Network timeout or connection refused
    setError({
      title: "Connection Error",
      message: "Unable to reach the server. Please check your internet connection.",
      action: "Try Again",
      retry: true,
    });
  } else if (error instanceof ApiError) {
    switch (error.status) {
      case 400:
        setError({
          title: "Invalid Request",
          message: "Please ensure all required fields are filled correctly.",
          action: "Review Input",
          retry: false,
        });
        break;
      case 401:
        setError({
          title: "Session Expired",
          message: "Please log in again to continue.",
          action: "Log In",
          retry: false,
          redirect: "/login",
        });
        break;
      case 404:
        setError({
          title: "Session Not Found",
          message: "The test session could not be found.",
          action: "Start New Test",
          retry: false,
        });
        break;
      case 429:
        setError({
          title: "Too Many Requests",
          message: "Please wait a moment before trying again.",
          action: "Retry",
          retry: true,
          retryDelay: 5000, // Wait 5 seconds
        });
        break;
      case 500:
      case 502:
      case 503:
        setError({
          title: "Server Error",
          message: "The server is having issues. Please try again later.",
          action: "Try Later",
          retry: false,
        });
        break;
      default:
        setError({
          title: "Error",
          message: `An error occurred: ${error.message}`,
          action: "Try Again",
          retry: true,
        });
    }
  }
}
```

## Loading States

Display appropriate feedback during API calls:

```typescript
if (isLoading) {
  return (
    <div className="loading-container">
      <Spinner />
      <p>Generating questions...</p>
      <small>This may take a moment on the first attempt</small>
    </div>
  );
}
```

## Error Display Component

```typescript
interface ErrorMessage {
  title: string;
  message: string;
  action: string;
  retry?: boolean;
  retryDelay?: number;
  redirect?: string;
}

function ErrorAlert({ error, onRetry, onDismiss }: {
  error: ErrorMessage;
  onRetry: () => void;
  onDismiss: () => void;
}) {
  return (
    <div className="error-alert">
      <div className="error-header">
        <AlertCircle />
        <h3>{error.title}</h3>
      </div>
      <p className="error-message">{error.message}</p>
      <div className="error-actions">
        {error.retry && (
          <button onClick={onRetry} className="btn-primary">
            {error.action}
          </button>
        )}
        {!error.retry && error.redirect && (
          <button onClick={() => window.location.href = error.redirect} className="btn-primary">
            {error.action}
          </button>
        )}
        {!error.retry && !error.redirect && (
          <button onClick={onDismiss} className="btn-secondary">
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
```

## Backend-Frontend Communication

### How Backend Auto-Retry Works

The backend now implements automatic retry with exponential backoff:

```
Frontend Request
    ↓
Backend Attempt 1 (0-2s)
    ├─ Success? → Return questions ✅
    └─ Fail? → Wait 1s
Backend Attempt 2 (1-3s)
    ├─ Success? → Return questions ✅
    └─ Fail? → Wait 2s
Backend Attempt 3 (2-4s)
    ├─ Success? → Return questions ✅
    └─ Fail? → Return error 429 or 500 ❌

Total max wait: 7 seconds (1 + 2 + 4)
```

**Important**: Frontend should set request timeout to **30 seconds** to account for backend retries + network latency.

### Response Metadata

The backend includes attempt information in responses:

```json
{
  "questions": [...],
  "total_tokens": 4250,
  "attempt": 2,
  "max_attempts": 3
}
```

This allows frontend to:

- Understand if a retry was needed
- Adjust UI feedback based on attempt count
- Log for analytics

## Testing Error Scenarios

### Simulate Transient Failures

```bash
# Start server with simulated failure rate
FAILURE_RATE=0.5 npm run dev

# Then generate questions multiple times
# ~50% should fail first, succeed on retry
```

### Manual Testing Checklist

- [ ] Test successful question generation (happy path)
- [ ] Test with invalid session ID (400 error)
- [ ] Test with expired session (401 error)
- [ ] Test network timeout (manually disconnect WiFi)
- [ ] Test slow network (DevTools throttle)
- [ ] Verify loading state shows during wait
- [ ] Verify retry button works and state resets
- [ ] Verify error messages are clear and helpful

## Best Practices

### 1. **Request Timeout**

```typescript
const fetchWithTimeout = (url: string, options: RequestInit, timeoutMs: number) => {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
    ),
  ]);
};

// Use 30 seconds for endpoints with potential backend retries
const response = await fetchWithTimeout(
  '/api/questions/generate',
  { method: 'POST', body: JSON.stringify(data) },
  30000
);
```

### 2. **Debounce Retry Requests**

Prevent user from spamming retry button:

```typescript
const [isRetrying, setIsRetrying] = useState(false);

async function handleRetry() {
  if (isRetrying) return;

  setIsRetrying(true);
  try {
    await generateQuestions(sessionId);
  } finally {
    setIsRetrying(false);
  }
}
```

### 3. **User Feedback**

Always inform users about the operation:

```typescript
return (
  <>
    {isLoading && <LoadingMessage />}
    {error && <ErrorAlert error={error} onRetry={handleRetry} />}
    {questions && <QuestionsList questions={questions} />}
  </>
);
```

### 4. **Error Logging**

Log errors for debugging without exposing sensitive info to users:

```typescript
function logError(error: Error, context: string): void {
  console.error(`[${context}]`, {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
  });

  // Send to analytics/monitoring service
  analyticsService.trackError({
    context,
    message: error.message,
    severity: 'error',
  });
}
```

### 5. **Graceful Degradation**

If question generation fails after all retries:

```typescript
if (questionsGenerationFailed) {
  return (
    <div className="fallback-content">
      <ErrorAlert title="Unable to Generate Questions" />
      <button onClick={handleRetry}>Try Again</button>
      <Link to="/dashboard">Return to Dashboard</Link>
    </div>
  );
}
```

## Summary: Frontend Responsibilities

### DO ✅

- Set request timeout to 30+ seconds
- Show loading state during API calls
- Display clear error messages
- Allow retry for transient errors (400/500)
- Log errors for debugging
- Validate inputs before sending
- Handle network timeouts gracefully

### DON'T ❌

- Retry on the frontend (backend handles it)
- Show technical error details to users
- Spam retry button (debounce)
- Assume temporary errors will go away (need feedback)
- Ignore 401/403 errors (redirect to login)
- Block UI during loading (show spinner instead)

## Common Patterns by Endpoint

### POST /questions/generate

**Expected Behavior**:

- Initial request takes 1-7 seconds (backend may retry)
- Response includes `total_tokens` and `attempt` count
- May fail after 3 backend attempts, returns 500 error

**Frontend Pattern**:

```typescript
// Set 30s timeout, show loading for entire duration
// Don't retry on frontend - backend handles it
// On error, show "Unable to generate questions" message
// User can click "Try Again" to submit new request
```

### POST /questions/answer

**Expected Behavior**:

- Fast response (no retries needed)
- Validates answer format before accepting
- Returns score and feedback

**Frontend Pattern**:

```typescript
// Validate answer format first
// Set 10s timeout (no backend retries expected)
// On error, show validation-specific message
```

## Related Documentation

- `docs/AGENT-TEST-SCENARIO.md` - Backend agent behavior and limitations
- `docs/TOOL_QUICK_REFERENCE.md` - API endpoint details
- `docs/architecture_diagram.md` - System architecture overview

---

**Last Updated**: 2025-11-17
**Version**: 1.0
**Status**: Active
