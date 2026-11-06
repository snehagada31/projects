# 🚀 Social Feed — FastAPI Backend Architecture

A high-performance, asynchronous REST API backend powering the Social Feed platform, built with **FastAPI**, **PostgreSQL** (via **SQLAlchemy 2.0 Async** + **asyncpg**), and **Pydantic v2**.

---

## 🏗️ Architecture & Core Components

```
backend/
├── alembic/                      # Database schema migrations
│   ├── versions/                 # 7 sequential version migrations
│   └── env.py                    # Async migration engine runner
├── app/
│   ├── main.py                   # App factory, lifespan, CORS, and Middlewares
│   ├── config.py                 # Pydantic BaseSettings environment validation
│   ├── api/                      # REST API Endpoints (Presentation Layer)
│   │   ├── auth.py               # Registration, Login, Logout, Sessions (IDOR safe)
│   │   ├── users.py              # Profiles, Follow graph, Search, Deactivation
│   │   ├── posts.py              # CRUD, 15m edit window, Likes, Reports, /trends
│   │   ├── feed.py               # Public and personalized keyset-paginated feeds
│   │   ├── notifications.py      # Activity alerts & preferences
│   │   └── health.py             # Liveness & readiness probes
│   ├── schemas/                  # Pydantic v2 DTO request/response models
│   ├── services/                 # Core business logic & rule validation
│   │   ├── auth_service.py       # Password verification & session management
│   │   └── post_service.py       # Post formatting & reply author resolution
│   ├── repositories/             # Persistence Layer (SQLAlchemy Async)
│   │   ├── postgres_repository.py# Authoritative PostgreSQL async queries & transactions
│   │   └── social_repository.py  # Repository protocol & in-memory fixture fallback
│   ├── db/                       # Database models & engine
│   │   ├── models.py             # Declarative SQLAlchemy models & SQL constraints
│   │   ├── session.py            # Async engine & sessionmaker pool
│   │   └── seed.py               # Idempotent fixture seeding runner
│   └── common/                   # Cross-cutting concerns
│       ├── request_id.py         # RequestIdMiddleware (X-Request-Id audit tracking)
│       ├── activity_logger.py    # Dual-sink audit logger (stdout + activity.log)
│       ├── errors.py             # AppError exception hierarchy
│       └── error_handlers.py     # Global exception handlers (422, 500 JSON envelopes)
├── logs/                         # Local disk log directory
│   └── activity.log              # Persistent local user audit trail
├── tests/                        # Comprehensive pytest test suite (21+ tests)
├── alembic.ini                   # Alembic configuration
└── requirements.txt              # Production dependencies
```

---

## 🔒 Security & Data Integrity Highlights

1. **Authentication & Token Hashing:**
   - Client receives a 32-byte cryptographically secure opaque token (`secrets.token_urlsafe(32)`).
   - In PostgreSQL, only the **`SHA-256 hash`** is stored (`user_sessions.token_hash`). Raw tokens are never stored.
   - Passwords hashed using **`bcrypt`** with salt rounds.

2. **Session Revocation & IDOR Protection:**
   - Specific session dismissal (`DELETE /auth/sessions/{id}`) strictly enforces ownership:
     `DELETE FROM user_sessions WHERE id = :session_id AND user_id = :current_user_id`
   - Bulk revocation endpoint (`POST /auth/sessions/revoke-others`) invalidates all other devices instantly.

3. **15-Minute Post Edit Lock:**
   - Post text edits (`PATCH /posts/{id}`) are restricted to the author and strictly bounded:
     `post.created_at + timedelta(minutes=15) >= now(utc)`.
   - Structural fields (`kind`, `id`, `author_id`, `created_at`) are immutable.

4. **Account Lifecycle & Soft-Delete:**
   - Account deactivation (`POST /users/me/deactivate`) sets `is_active = False` and revokes all active sessions with `revoked_at = NOW()`.
   - Preserves relational consistency while blocking further access.

5. **Atomic Operations with `session.flush()`:**
   - In `create_post()` ([`postgres_repository.py:181`](app/repositories/postgres_repository.py)), `session.flush()` queries PostgreSQL to generate `new_post.id` inside the ongoing transaction, allowing reply notifications to reference the post ID before atomic `session.commit()`.

---

## 🗄️ Database & Alembic Migrations

Migrations live in `alembic/versions/` and are tracked in PostgreSQL via the **`alembic_version`** table:

1. `a62c769b5f6c`: Initial schema (`users`, `posts`, `post_media`, `likes`, `follows`).
2. `8b08f98031ea`: Added `password_hash` & `user_sessions`.
3. `de324b9397d4`: Created `notifications` table with unique `dedup_key`.
4. `f1e2d3c4b5a6`: Created `bookmarks` table with composite PK `(user_id, post_id)`.
5. `a1b2c3d4e5f6`: Created `user_notification_preferences` table.
6. `b2c3d4e5f6a1`: Created `post_reports` moderation table.
7. `089a1f8a60c3`: Added `is_active` boolean to `users` for deactivation.

---

## 🛠️ Local Setup & Commands

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed initial test accounts (Asha, Dev, Maya, Leo, Zara, Kenji)
python -m app.db.seed

# Start development server
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Docs (Swagger UI):** `http://localhost:8000/docs`
- **Liveness Probe:** `http://localhost:8000/health/live`
- **Trending Topics & Hashtags:** `http://localhost:8000/trends`
