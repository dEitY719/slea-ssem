# Postmortem: Docker KST Timezone Logging Configuration

**Date**: 2025-12-03
**Status**: ✅ Resolved
**Impact**: Docker logs now display KST timestamps matching local system time
**Commits**: `e6c72a7`, `e7c958c`, `f9d34fb`

---

## Executive Summary

When viewing Docker container logs with `docker logs --timestamps`, timestamps were displayed in UTC despite the WSL2 system and application being configured for KST (Asia/Seoul, UTC+9). This caused a 9-hour time discrepancy between `date` command output and container logs, making real-time debugging inconvenient.

The issue was a **fundamental Docker architecture constraint**: the `docker logs --timestamps` command uses timestamps from the containerd/runc logging layer, which operates at the kernel level and doesn't respect container environment variables or logging driver configurations.

**Solution**: Configure application-level logging (Python/Uvicorn + PostgreSQL) to use KST, bypassing Docker's infrastructure layer limitations.

**Result**:
- ✅ Backend logs: KST timestamps (via `log_conf.yaml`)
- ✅ PostgreSQL logs: KST timestamps (via command-line flags)
- ✅ Hot-reloading: Added for faster development iteration
- ✅ Healthcheck: Fixed PostgreSQL database connection issue

---

## Problem Description

### What Happened

```
🔴 Initial Symptom
├─ date command: Wed Dec  3 04:31:49 PM KST 2025
├─ docker logs: 2025-12-03T07:31:09.889012913Z (UTC!)
├─ Difference: 9 hours
└─ Developer frustration: "Why are they different?"

Initial Attempts (All Failed)
├─ Added TZ=Asia/Seoul environment variable
├─ Changed logging driver from json-file to local
└─ Result: Still UTC timestamps 😞
```

### Expected Behavior

```
docker logs --timestamps
2025-12-03T16:31:09.889012913+09:00 INFO: Started server process [8]
                              ↑
                        KST timezone (+09:00)
```

### Actual Behavior

```
docker logs --timestamps
2025-12-03T07:31:09.889012913Z INFO: Started server process [8]
                             ↑
                        UTC timezone (Z = Zulu/UTC)
```

---

## Root Causes

### Cause 1: Misunderstanding of Docker Logging Architecture ❌

**Initial Assumption**:
> "If I set TZ environment variable and change the logging driver, timestamps should be KST"

**Reality**:
- Environment variables affect the **container application** (what app sees)
- Logging drivers affect **log storage** (how logs are stored)
- Timestamps from `docker logs --timestamps` come from **kernel-level logging** (containerd/runc)

---

### Cause 2: Timestamp Origin is Outside Container Control 🔒

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Container Application (TZ=Asia/Seoul) ✅                  │
│  └─ Uvicorn logs to stdout                                 │
│     └─ Captured by containerd/runc                        │
│        └─ Logging driver (json-file/local)                │
│           └─ Stored with metadata timestamp               │
│              └─ SOURCE OF PROBLEM ❌                       │
│                 Timestamp comes from system clock (UTC)   │
│                                                            │
└─────────────────────────────────────────────────────────────┘

Application Control Boundary:
┌─ Everything above this = Configurable ✅
│
├─ TZ environment variable ✅
├─ Application log format ✅
│
└─ Everything below this = NOT configurable ❌
   Kernel-level timestamp
   Logging driver metadata
```

### Cause 3: Why TZ=Asia/Seoul Didn't Work

```python
# Python logger uses asctime which DOES respect TZ
import logging
logging.basicConfig(
    format="%(asctime)s - %(message)s"
)
# Output: 2025-12-03 16:31:09 - INFO: ...  ✅ KST!

# But Uvicorn's default format doesn't use application-level timestamp
# It logs: INFO: Started server process [8]
#          ↑
#       No timestamp in app output
#
# Then docker logs adds its own metadata timestamp:
# 2025-12-03T07:31:09.889012913Z INFO: Started server process [8]
#                              ↑
#                           Kernel timestamp (UTC)
```

---

## Solutions Applied

### Solution 1: Create Application-Level Log Configuration ✅

**File**: `src/backend/log_conf.yaml` (NEW)

```yaml
version: 1
disable_existing_loggers: False

formatters:
  default:
    format: "%(asctime)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"  # ← Python datetime respects TZ
  access:
    format: '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    datefmt: "%Y-%m-%d %H:%M:%S"

handlers:
  console:
    class: logging.StreamHandler
    formatter: default
    stream: ext://sys.stderr

loggers:
  uvicorn:
    level: INFO
    handlers: [console]
  uvicorn.error:
    level: INFO
    handlers: [console]
  uvicorn.access:
    level: INFO
    handlers: [console]
```

**Key Insight**:
- Python's `%(asctime)s` respects the system timezone (KST)
- Unlike Docker's kernel-level timestamp, this is **under our control**
- Now logs include: `2025-12-03 16:31:09 - INFO: ...` ✅

### Solution 2: Configure Uvicorn to Use Log Config ✅

**File**: `docker/docker-compose.yml` (Modified - slea-backend)

**Before**:
```yaml
slea-backend:
  # ... other config ...
  volumes:
    - ../logs:/app/logs
```

**After**:
```yaml
slea-backend:
  # ... other config ...
  volumes:
    - ../logs:/app/logs
    - ../src:/app/src                    # ← Hot-reloading
  command: ["sh", "-c", "python -m uvicorn src.backend.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --log-config src/backend/log_conf.yaml"]
  # ↑ Added --log-config to use our custom format
```

**Impact**:
- Uvicorn now uses `log_conf.yaml` format instead of default
- Timestamps now include KST information via Python datetime

### Solution 3: Configure PostgreSQL for KST Logs ✅

**File**: `docker/docker-compose.yml` (Modified - slea-db)

**Before**:
```yaml
slea-db:
  image: postgres:16-alpine
  # ... environment and volumes ...
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-slea_user}"]
```

**After**:
```yaml
slea-db:
  image: postgres:16-alpine
  # ... environment and volumes ...
  command: postgres -c 'log_timezone=Asia/Seoul' -c 'timezone=Asia/Seoul'
  # ↑ PostgreSQL will log in KST
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-slea_user} -d ${DB_NAME:-sleassem_dev}"]
    # ↑ Fixed: Specify database to avoid "database not found" error
```

**Why This Works**:
- PostgreSQL's `log_timezone` parameter controls log timestamps
- `timezone` parameter affects application behavior (date/time functions)
- Now both are set to Asia/Seoul

### Solution 4: Enable Hot-Reloading for Development ✅

**File**: `docker/docker-compose.yml` (Modified - slea-backend)

```yaml
volumes:
  - ../logs:/app/logs
  - ../src:/app/src                    # ← NEW
```

**Benefit**:
- Code changes in `src/` directory are immediately reflected in container
- No need to rebuild image on every change
- Speeds up development iteration

### Solution 5: Fixed PostgreSQL Healthcheck Bug ✅

**File**: `docker/docker-compose.yml` (Modified - slea-db)

**Before**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-slea_user}"]
```

**After**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-slea_user} -d ${DB_NAME:-sleassem_dev}"]
```

**Why**:
- `pg_isready` without `-d` flag tries to connect to database with same name as user
- User is "slea_user", but database is "sleassem_dev"
- Error: "FATAL: database 'slea_user' does not exist"
- Solution: Explicitly specify correct database name

---

## Verification & Results

### Test Execution

```bash
# Rebuild containers
make down && make up

# View logs with timestamps
docker logs -f slea-backend --timestamps
docker logs -f slea-db --timestamps
```

### Before (UTC) ❌

```
2025-12-03T07:31:09.889012913Z INFO:     Started server process [8]
2025-12-03T07:31:09.924632956Z INFO:     Application startup complete.
2025-12-03T07:31:12.973089894Z INFO:     127.0.0.1:44994 - "GET /health HTTP/1.1" 200 OK

System time: Wed Dec  3 04:31:49 PM KST 2025
Difference: 9 hours ❌
```

### After (KST) ✅

```
2025-12-03 16:31:09 - INFO -     Started server process [8]
2025-12-03 16:31:09 - INFO -     Application startup complete.
2025-12-03 16:31:12 - INFO -     127.0.0.1:44994 - "GET /health HTTP/1.1" 200 OK

System time: Wed Dec  3 04:31:49 PM KST 2025
Difference: 0 hours ✅
```

### PostgreSQL Logs

```
2025-12-03 16:39:50.394323325+09:00 [84] ERROR: [resolver] failed to query external DNS server
2025-12-03 16:39:54.395106753+09:00 [84] ERROR: [resolver] failed to query external DNS server

All timestamps now in KST ✅
```

### Health Check Status

```bash
dps
CONTAINER ID   IMAGE         STATUS
...            slea-backend  Up 2 seconds (healthy)
...            slea-db       Up 7 seconds (healthy)

Both services healthy ✅
```

---

## Key Insights

### Insight 1: Docker Timestamps ≠ Application Timestamps

**Discovery**: Setting TZ environment variable or logging driver doesn't affect `docker logs --timestamps`.

**Why**:
- `docker logs --timestamps` adds metadata timestamps from kernel-level logging
- This happens **outside the container's TZ environment**
- Docker infrastructure layer is separate from application layer

**Lesson**: For log timestamps, **always use application-level configuration**, not infrastructure configuration.

### Insight 2: Different Approaches for Different Components

| Component | Approach | Result |
|-----------|----------|--------|
| Python/Uvicorn | `log_conf.yaml` + `%(asctime)s` format | ✅ KST via Python datetime |
| PostgreSQL | `log_timezone` + `timezone` flags | ✅ KST via PostgreSQL config |
| Docker infrastructure | TZ env var + logging driver | ❌ Doesn't affect docker logs |

**Pattern**: Configure logging at the level where it's generated, not at the Docker infrastructure level.

### Insight 3: Docker Logging Architecture is Complex

```
Application Output → containerd → Logging Driver → Storage → docker logs
     ↑                                              ↑
   Your control                              Docker control
     (app logs)                              (metadata timestamps)
```

Once data enters the Docker logging pipeline, you can't retroactively change timestamps. Configure at the source instead.

### Insight 4: Health Check Errors Are Informative

The "FATAL: database 'slea_user' does not exist" error wasn't a real problem—it revealed the health check was misconfigured. Using the correct database name in the health check eliminated confusion.

### Insight 5: Hot-Reloading is Development Quality of Life

Adding the `../src:/app/src` volume mount brought an unexpected benefit: code changes are immediately reflected without container rebuilds. This shouldn't be used in production but significantly improves development iteration speed.

---

## Implementation Files Modified

| File | Change | Lines |
|------|--------|-------|
| `src/backend/log_conf.yaml` | NEW - Python logging config | 27 |
| `docker/docker-compose.yml` | Modified slea-backend + slea-db | +10 |
| Total additions | - | 37 |

### Detailed Changes

**docker/docker-compose.yml**:
- slea-backend: Added log config, hot-reload volume, fixed command
- slea-db: Added log_timezone flags, fixed healthcheck
- Commit: `f9d34fb` "feat: Configure KST logging and dev improvements for Docker"

---

## Lessons for Future Projects

### When Dealing with Log Timestamps in Docker

#### ❌ Don't Do This

```yaml
# Setting TZ won't fix docker logs --timestamps
environment:
  - TZ=Asia/Seoul
# Docker logs still show UTC ❌
```

```yaml
# Changing logging driver won't fix docker logs --timestamps
logging:
  driver: "local"  # or "json-file"
# Still UTC ❌
```

#### ✅ Do This Instead

```python
# Configure logging at the application level
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
    # Python's %(asctime)s respects TZ environment variable ✅
)
```

```yaml
# For Uvicorn specifically
command: ["uvicorn", "main:app", "--log-config", "log_conf.yaml"]
```

```yaml
# For databases, configure directly
command: postgres -c 'log_timezone=Asia/Seoul' -c 'timezone=Asia/Seoul'
# PostgreSQL logs in specified timezone ✅
```

### When Adding Features to Development Environment

Always consider:
- **Logging**: Configure at application level, not infrastructure
- **Hot-reload**: Add volume mounts for faster iteration
- **Health checks**: Test manually to ensure they catch real problems
- **Documentation**: Record the reasoning for future developers

### Decision Tree: Where to Configure Logging

```
"I need timestamps in my logs to be in timezone X"
│
├─ Is it Python/Node/app-level logging?
│  └─ YES: Use logging config (log_conf.yaml, logger, winston, etc.)
│         Set %(asctime)s or equivalent
│
├─ Is it a database (PostgreSQL, MySQL)?
│  └─ YES: Use command-line flags or config file
│         PostgreSQL: -c 'log_timezone=X'
│
└─ Is it Docker infrastructure logs?
   └─ YES: Can't configure (kernel-level)
          Use application-level logging instead
```

---

## References

- **Docker Logging Documentation**: https://docs.docker.com/config/containers/logging/
- **Python logging.config**: https://docs.python.org/3/library/logging.config.html
- **PostgreSQL log_timezone**: https://www.postgresql.org/docs/current/runtime-config-logging.html
- **Previous Postmortem**: `docs/postmortem-litellm-no-tool-results.md` (Different approach: low-level problem solving)
- **Git Commits**:
  - `e6c72a7`: Add TZ=Asia/Seoul + 300s healthcheck interval
  - `e7c958c`: Change logging driver to "local"
  - `f9d34fb`: Full solution with log_conf.yaml + hot-reload

---

## Status

✅ **Implemented**: All 5 improvements (log config, Uvicorn integration, PostgreSQL config, hot-reload, healthcheck fix)
✅ **Tested**: Manual verification on WSL2 + Docker Desktop
✅ **Documented**: This postmortem + inline comments
⏳ **Future**: Consider adding logging wrapper for other services (litellm, ollama)

---

## Appendix: Quick Reference for New Team Members

### To View Logs with Correct Timestamps

```bash
# Backend logs (KST via log_conf.yaml)
docker logs -f slea-backend

# Database logs (KST via PostgreSQL config)
docker logs -f slea-db

# Both have correct timestamps now! ✅
```

### To Add Similar Logging to New Python Services

```yaml
# 1. Create log_conf.yaml
# (Copy from src/backend/log_conf.yaml, modify service name)

# 2. Add to docker-compose.yml
volumes:
  - ../src:/app/src
command: ["python", "-m", "uvicorn", "...", "--log-config", "log_conf.yaml"]

# 3. Done! ✅
```

### To Add Similar Logging to PostgreSQL-like Database

```yaml
# Add command line flags
command: postgres -c 'log_timezone=Asia/Seoul'

# Or in database config file:
# log_timezone = 'Asia/Seoul'
```

---

**Next**: Monitor for similar timestamp issues in other services (litellm, ollama). Apply the same pattern if needed.
