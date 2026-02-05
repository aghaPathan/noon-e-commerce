# Noon E-Commerce — Critical Audit Report

**Date:** 2026-02-05  
**Auditor:** Paposhkov  
**Scope:** Full codebase evaluation (architecture, security, quality, testing, ops)

---

## Executive Summary

| Category | Grade | Notes |
|----------|-------|-------|
| **Architecture** | B+ | Clean separation, good tech choices, missing containerization |
| **Security** | B | Solid auth, env-based secrets, some gaps |
| **Code Quality** | B+ | Well-structured, consistent patterns, minor issues |
| **Testing** | C | Integration tests exist, unit tests missing |
| **Documentation** | A- | Excellent README, .env.example, inline docs |
| **Operations** | C+ | No Docker Compose, manual deployment |

**Overall: B (Good, with clear areas for improvement)**

---

## 1. Architecture

### Strengths ✅
- **Dual-database design**: PostgreSQL for transactional (users, auth), ClickHouse for analytics (price history) — appropriate separation
- **Clean API structure**: Routes split by domain (`routes_auth.py`, `routes_skus.py`, `routes_admin.py`, `routes_alerts.py`)
- **Modern stack**: FastAPI + Pydantic v2, React 18 + TypeScript, Vite
- **Code splitting**: React.lazy() for route-level splitting
- **Layered frontend**: Services → Hooks → Components pattern

### Issues ⚠️

| Issue | Severity | Location |
|-------|----------|----------|
| No Docker Compose | Medium | Project root |
| Duplicate DB connections | Low | `routes_auth.py` vs `db_postgres.py` |
| Port inconsistency | Low | `db_postgres.py` defaults to 5432, `.env` uses 5433 |
| Cache is in-memory dict | Medium | `main.py` — lost on restart, no TTL eviction |

### Recommendations
1. **Add `docker-compose.yml`** for local dev (PostgreSQL, ClickHouse, API, Frontend)
2. **Consolidate DB layer** — use `db_postgres.py` everywhere, remove inline psycopg2 in `routes_auth.py`
3. **Replace in-memory cache** with Redis for production (already have ClickHouse, Redis is cheap)
4. **Fix port default** in `db_postgres.py`: `5432` → `5433`

---

## 2. Security

### Strengths ✅
- **Secrets via env vars** — no hardcoded credentials (verified in commit `1903141`)
- **bcrypt password hashing** via passlib
- **JWT with refresh tokens** — proper access/refresh separation
- **Rate limiting** on auth endpoints (5/min login, 10/min register)
- **Security headers middleware** (X-Frame-Options, X-Content-Type-Options, etc.)
- **CORS configurable** via env var
- **Input validation** via Pydantic

### Issues ⚠️

| Issue | Severity | Location |
|-------|----------|----------|
| Legacy SHA256 fallback | High | `auth.py:verify_password()` |
| No password complexity validation | Medium | `auth.py:UserCreate` |
| Refresh token not invalidated on logout | Medium | No logout endpoint |
| No account lockout after failed attempts | Low | `routes_auth.py` |
| HSTS disabled | Low | `main.py` (commented out) |

### Critical: Legacy Hash Fallback

```python
# auth.py line 52-55
except Exception:
    import hashlib
    legacy_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return legacy_hash == hashed_password
```

**Risk**: If any old users have SHA256 hashes, they're validated without salt — vulnerable to rainbow tables.

**Fix**: Remove fallback OR force password reset for legacy users.

### Recommendations
1. **Remove SHA256 fallback** — force migration to bcrypt
2. **Add password policy**: min 8 chars (already), + require number/special char
3. **Implement `/api/auth/logout`** with refresh token revocation (store revoked tokens in Redis/DB)
4. **Add brute force protection**: lock account after 5 failed attempts for 15 min
5. **Enable HSTS** when serving over HTTPS

---

## 3. Code Quality

### Strengths ✅
- **Consistent patterns**: All routes follow same structure
- **Type hints**: Used throughout Python and TypeScript
- **Error handling**: Global exception handlers in FastAPI
- **Logging**: Structured logging with request correlation IDs
- **Retry logic**: Database operations use tenacity for resilience
- **Slow query logging**: Queries over 100ms are logged

### Issues ⚠️

| Issue | Severity | Location |
|-------|----------|----------|
| Raw SQL without ORM | Low | All DB files (acceptable, but manual) |
| No connection pooling | Medium | `db_postgres.py` — new connection per request |
| `datetime.utcnow()` deprecated | Low | Multiple files (use `datetime.now(UTC)`) |
| Broad exception catches | Low | `database.py` — catches all exceptions |

### Recommendations
1. **Add connection pooling**: Use `psycopg2.pool.ThreadedConnectionPool` or `asyncpg` with pool
2. **Replace `datetime.utcnow()`** with `datetime.now(timezone.utc)` (Python 3.12+ deprecation)
3. **Narrow exception handling** — catch specific exceptions, not bare `Exception`

---

## 4. Testing

### Current State
- **Integration test**: `api/test_api.py` — covers auth, SKUs, alerts, admin
- **Frontend test setup**: Vitest configured, `@testing-library/react` installed
- **No unit tests found**: `find` returned empty for `*.test.*` files

### Test Coverage Estimate
- Backend: ~20% (integration only)
- Frontend: ~0% (no test files)

### Missing Tests ⚠️

| Component | Tests Needed |
|-----------|--------------|
| `auth.py` | Unit tests for `hash_password`, `verify_password`, `create_access_token` |
| `database.py` | Unit tests for query methods (mock ClickHouse) |
| `db_postgres.py` | Unit tests for CRUD operations |
| Frontend services | Unit tests for API client, error handling |
| Frontend components | Component tests for Login, Dashboard, AlertFeed |

### Recommendations
1. **Add pytest fixtures** for database mocking
2. **Target 60% coverage** on critical paths (auth, payment-related if any)
3. **Add E2E tests** with Playwright for critical user flows
4. **Add pre-commit hooks** for test running

---

## 5. Documentation

### Strengths ✅
- **Excellent README**: Architecture diagram, badges, tech stack, API reference
- **`.env.example`**: Complete with all required vars and comments
- **Inline docstrings**: Functions documented in Python files
- **API docs**: FastAPI auto-generates `/docs` and `/redoc`

### Missing ⚠️
- **CONTRIBUTING.md**: No contribution guidelines
- **API changelog**: Version history not documented
- **Deployment guide**: No production deployment docs
- **Database schema docs**: SQL files exist but no ERD

### Recommendations
1. Add `docs/DEPLOYMENT.md` with production setup steps
2. Add `docs/SCHEMA.md` with ERD diagram
3. Add `CHANGELOG.md` following Keep a Changelog format

---

## 6. Operations & DevOps

### Current State
- **No containerization**: No Dockerfile or docker-compose.yml
- **No CI/CD pipeline visible**: (`.github/workflows` referenced but not in tree)
- **No health checks for dependencies**: Only ClickHouse health checked
- **No monitoring**: Prometheus instrumented but no scrape config

### Production Gaps ⚠️

| Gap | Impact |
|-----|--------|
| No container orchestration | Manual deployment, inconsistent environments |
| No database migrations | Schema changes require manual SQL |
| No backup strategy | Data loss risk |
| No alerting | Issues go unnoticed |

### Recommendations
1. **Add `docker-compose.yml`**:
   ```yaml
   services:
     api:
       build: ./api
       ports: ["8096:8096"]
       env_file: .env
       depends_on: [postgres, clickhouse]
     postgres:
       image: postgres:16
       volumes: [pgdata:/var/lib/postgresql/data]
     clickhouse:
       image: clickhouse/clickhouse-server:24
       volumes: [chdata:/var/lib/clickhouse]
     frontend:
       build: ./frontend-ts
       ports: ["3000:3000"]
   ```
2. **Add Alembic migrations** for PostgreSQL schema versioning
3. **Add GitHub Actions** for CI (lint, test, build)
4. **Add health endpoint** that checks both PostgreSQL and ClickHouse

---

## 7. Performance Considerations

### Good ✅
- **Caching layer** (even if in-memory)
- **Pagination** on all list endpoints
- **Slow query logging**
- **Rate limiting**

### Concerns ⚠️
- **No database indexes documented** — need to verify on price_history table
- **ClickHouse connection per query** — should use connection pool
- **Frontend bundle size** — not analyzed, could be large with Chart.js

### Recommendations
1. Verify indexes on `price_history(sku, scraped_at)` and `products(sku)`
2. Add bundle analysis to frontend build
3. Consider lazy-loading Chart.js only on dashboard

---

## 8. Summary of Action Items

### Critical (Do Now)
1. ❌ Remove SHA256 password fallback in `auth.py`
2. ❌ Fix port default in `db_postgres.py` (5432 → 5433)

### High Priority (This Sprint)
3. 📦 Add `docker-compose.yml` for local development
4. 🔐 Add logout endpoint with token revocation
5. 🧪 Add unit tests for auth module (target 60% coverage)
6. 🔗 Consolidate database connection code

### Medium Priority (Next Sprint)
7. 📊 Add connection pooling for PostgreSQL
8. 📝 Add `DEPLOYMENT.md` documentation
9. 🚀 Set up GitHub Actions CI pipeline
10. 🔒 Add account lockout after failed login attempts

### Low Priority (Backlog)
11. Replace in-memory cache with Redis
12. Add database migrations with Alembic
13. Frontend unit tests
14. Bundle size optimization

---

## Conclusion

The Noon E-Commerce project is **well-architected and security-conscious** for a market intelligence platform. The dual-database approach is appropriate, authentication is solid, and the codebase is clean and maintainable.

**Main gaps** are in operations (no containerization), testing (minimal coverage), and one critical security issue (SHA256 fallback). Addressing the critical items first, then building out the DevOps infrastructure, will bring this to production-ready status.

**Estimated effort to production-ready**: 2-3 developer-days.

---

*Report generated by Paposhkov — AI Dev Team Orchestrator*
