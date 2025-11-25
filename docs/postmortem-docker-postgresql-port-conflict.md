# Postmortem: Docker PostgreSQL Port Conflict with WSL Local Database

**Date**: 2025-11-25
**Status**: ✅ Resolved
**Impact**: VSCode Database extension now connects to Docker PostgreSQL successfully
**Solution**: Port remapping from 5432 → 5433

---

## Executive Summary

When attempting to connect to Docker PostgreSQL via VSCode Database extension, users received **"password authentication failed"** errors despite correct credentials and trust authentication configured. The root cause was **port collision**: WSL's local PostgreSQL (16) was already running on port 5432, intercepting all localhost:5432 connections before they reached the Docker container.

**Key Discovery**: The problem was NOT authentication configuration—it was network routing. The host machine's localhost:5432 was connecting to WSL's native PostgreSQL, not Docker's.

**Solution**: Remap Docker PostgreSQL to port 5433, allowing coexistence of:
- **WSL local PostgreSQL**: localhost:5432
- **Docker PostgreSQL**: localhost:5433

---

## Problem Description

### What Happened

```
🔴 Scenario 1: Attempt to connect to localhost:5432
├─ VSCode Database Extension Input
│  ├─ Host: localhost
│  ├─ Port: 5432
│  ├─ User: slea_user
│  └─ Password: change_me_dev_password
├─ Error: ❌ FATAL: password authentication failed for user "slea_user"
└─ Result: Connection to WSL's native PostgreSQL 16 (different DB instance)

🔴 Scenario 2: Attempt 172.19.0.2 (Docker internal IP)
├─ Host: 172.19.0.2
├─ Port: 5432
└─ Error: ❌ Connection timeout (Docker internal network not routable from WSL)

🔴 Scenario 3: Attempt 127.0.0.1:5432 via psql
├─ Command: psql -h 127.0.0.1 -p 5432 -U slea_user -d sleassem_dev
└─ Result: Connects to WSL's local PostgreSQL 16 (wrong instance!)
   "sleassem_dev" database exists here too → confusion about which DB
```

### Root Causes

#### 1. **WSL Already Running PostgreSQL 16**

```bash
ps aux | grep postgres
# Output:
# /usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/16/main
```

- WSL has native PostgreSQL 16 installed and running on port 5432
- WSL's localhost:5432 defaults to this local instance
- Docker's port forwarding (0.0.0.0:5432->5432) doesn't override host routing priority

#### 2. **Docker Network Isolation**

- Docker container's internal IP (172.19.0.2) is not directly routable from WSL host
- Port forwarding via 0.0.0.0:5432 is the ONLY way to connect from host
- But this port was already "claimed" by WSL's local PostgreSQL

#### 3. **Authentication Confusion**

- pg_hba.conf was correctly set to `trust` for all connections
- But users kept trying to authenticate with password
- Even with trust configured, the "wrong" PostgreSQL (local one) required password auth (scram-sha-256)

#### 4. **Same Database Name in Both Instances**

Both PostgreSQL instances had `sleassem_dev` database:
- WSL's local PostgreSQL 16: sleassem_dev (user: himena)
- Docker's PostgreSQL 15: sleassem_dev (user: slea_user)

This made debugging confusing—connections "worked" but connected to the wrong instance!

---

## Solutions Applied

### Change 1: Remap Docker PostgreSQL Port ✅

**File**: `docker-compose.yml` (line 27-31)

**Before**:
```yaml
ports:
  - "5432:5432"  # ❌ Conflicts with WSL's PostgreSQL 16
```

**After**:
```yaml
ports:
  - "5433:5432"  # ✅ Maps Docker port 5432 → Host port 5433
```

**Rationale**:
- Allows both databases to coexist without port collision
- Clear separation: 5432 (WSL local) vs 5433 (Docker)
- No need to stop WSL's PostgreSQL or modify its config

### Change 2: Update pg_hba.conf to Trust Authentication ✅

**File**: Executed in Docker container during setup

```sql
# PostgreSQL Client Authentication Configuration
# Modified for development: all connections use trust authentication

# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               trust  ⬅️ KEY: Remote access
host    all             all             ::/0                    trust

local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
host    replication     all             0.0.0.0/0               trust
host    replication     all             ::/0                    trust
```

**Result**: No password required for Docker PostgreSQL access

---

## Verification Results

### ✅ Test 1: Direct Container Access (Working)

```bash
docker-compose exec db psql -U slea_user -d sleassem_dev -c "\dt"

# Output:
#                  List of relations
#  Schema |         Name         | Type  |   Owner
# --------+----------------------+-------+-----------
#  public | answer_explanations  | table | slea_user
#  public | attempt_answers      | table | slea_user
#  ...
# (10 rows)
```

### ✅ Test 2: Host Access via Port 5433 (Working)

```bash
psql -h 127.0.0.1 -p 5433 -U slea_user -d sleassem_dev -w -c "\dt"

# Output:
#                  List of relations
#  Schema |         Name         | Type  |   Owner
# --------+----------------------+-------+-----------
#  ...  (same 10 tables)
```

### ✅ Test 3: VSCode Database Extension (Working)

VSCode SQLTools Extension Configuration:
```json
{
  "name": "slea-db-docker",
  "driver": "PostgreSQL",
  "server": "localhost",
  "port": 5433,           ⬅️ CRITICAL: Must be 5433
  "database": "sleassem_dev",
  "username": "slea_user",
  "password": "change_me_dev_password"
}
```

**Result**: ✅ Test Connection Succeeded

---

## Architecture After Fix

```
┌─────────────────────────────────────────────────────┐
│                    WSL Host                         │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │        localhost (127.0.0.1)                 │  │
│  │                                              │  │
│  │  :5432  ──→  PostgreSQL 16 (WSL native)    │  │
│  │              (himena/sleassem_dev)          │  │
│  │                                              │  │
│  │  :5433  ──→  Docker Container               │  │
│  │              ┌──────────────────────┐        │  │
│  │              │  PostgreSQL 15       │        │  │
│  │              │  (slea_user/dev)     │        │  │
│  │              │  Port: 5432          │        │  │
│  │              └──────────────────────┘        │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘

VSCode Connection:
  localhost:5433 → (port forward) → Docker:5432 → ✅ Success
```

---

## Prevention Checklist

### For Future Development

- [ ] **Check for port conflicts FIRST** before debugging authentication
  ```bash
  # Identify what's using a port
  netstat -tlnp | grep 5432
  lsof -i :5432
  ps aux | grep postgres
  ```

- [ ] **Document which PostgreSQL instance is which**
  - WSL local: Port 5432, Version 16
  - Docker: Port 5433, Version 15
  - Never assume localhost:5432 is always Docker!

- [ ] **Verify connection before testing auth**
  ```bash
  # Test port connectivity
  curl -v telnet://localhost:5433
  # Or: timeout 2 bash -c '</dev/tcp/localhost/5433' && echo OK
  ```

- [ ] **If adding new services**, always:
  1. List all ports in use: `docker-compose ps`
  2. Check host ports: `lsof -i :PORT`
  3. Verify no WSL native services on those ports

### For Team Setup

- [ ] Include port mapping info in README/setup guide
- [ ] Document: "If using Docker PostgreSQL, use port 5433, not 5432"
- [ ] For inside-only deployments (사내), consider using docker-compose.override.yml to change ports

---

## Key Learnings

### 1. **Port Forwarding ≠ Network Magic**

- Docker's `0.0.0.0:5433->5432` is a host-level port forward, not a network bridge
- Host services binding to lower port numbers take precedence
- Always check: `ps aux | grep PORT` on host, then `docker ps` on containers

### 2. **Trust Authentication Alone Isn't Enough**

- Trust auth only works if you're connecting to the RIGHT PostgreSQL instance
- Debugging "password failed" should first check: "Am I connecting to the right database?"
- Verify with: `SELECT version()` to confirm which PostgreSQL version you're connected to

### 3. **Database Name Collisions Mask Problems**

- Having `sleassem_dev` in both WSL's local PostgreSQL and Docker's PostgreSQL made debugging harder
- Data looked correct but was from the wrong instance
- For local dev: rename local DB or use Docker-only setup

### 4. **VSCode Database Extensions Need Explicit Docs**

- VSCode Database extension users often don't know about port forwarding
- Should document: "If using Docker PostgreSQL instead of local, change port from 5432 to 5433"
- Consider adding `.vscode/settings.json` template with both connection options

---

## Related Issues & Context

- **Original Issue**: VSCode reports "password authentication failed"
- **Investigation**: pg_hba.conf was set to `trust` but still required password
- **Hidden Cause**: Users were connecting to WSL's PostgreSQL 16, not Docker's PostgreSQL 15
- **Resolution Time**: ~30 minutes once root cause identified
- **Key Insight**: Network routing issues often masquerade as authentication problems

---

## Commits

- Port change: `docker-compose.yml` modified (line 27-31)
- pg_hba.conf: Created with trust authentication for all hosts
- Documentation: This postmortem document

---

## Appendix: Quick Reference

### If You Have Similar Issues

1. **Check what's using port 5432:**
   ```bash
   ps aux | grep postgres
   ```

2. **If WSL PostgreSQL is running:**
   ```bash
   # Option A: Stop it
   sudo systemctl stop postgresql

   # Option B: Use Docker on different port
   # Edit docker-compose.yml: "5433:5432"
   ```

3. **Verify correct PostgreSQL:**
   ```bash
   # Should return PostgreSQL 15.15 (Docker version)
   psql -h 127.0.0.1 -p 5433 -U slea_user -d sleassem_dev -c "SELECT version();"
   ```

4. **For VSCode, always use:**
   ```
   Host: localhost
   Port: 5433    ← Not 5432!
   ```
