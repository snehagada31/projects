# 🌐 Social Feed Platform (Python FastAPI + React + PostgreSQL)

A high-performance, full-stack social media feed platform inspired by Twitter/X, engineered with **FastAPI** (asynchronous Python 3.11+), **PostgreSQL** (via **SQLAlchemy 2.0 Async** + **asyncpg**), and a responsive **React 18** SPA frontend with dark-mode UI.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────┐                 ┌──────────────────────────────────────┐
│       React 18 SPA (Vite)       │                 │         FastAPI Backend Server       │
│   (Vercel Cloud / Localhost)    │  REST API / JSON│       (Render Cloud / Localhost)     │
│                                 │◄───────────────►│                                      │
│ • Dark Mode UI (Twitter-style)  │  Bearer Tokens  │ • Middlewares (CORS, RequestId)      │
│ • Real-time Live Breaking News  │  Base64 Avatars │ • Pydantic v2 Schema Validation      │
│ • Password Visibility Toggle    │                 │ • 15-Minute Post Edit Lock           │
│ • Keyset Cursor Feed Scrolling  │                 │ • SHA-256 Token Session Store        │
│ • Mobile Responsive Layout      │                 │ • Dual-Sink Audit Activity Logger    │
└─────────────────────────────────┘                 └──────────────────┬───────────────────┘
                                                                       │ SQLAlchemy 2.0 (asyncpg)
                                                                       ▼
                                                    ┌──────────────────────────────────────┐
                                                    │         PostgreSQL Database          │
                                                    │     (Managed via Alembic Migrations) │
                                                    │                                      │
                                                    │ • 7 Version Migrations               │
                                                    │ • CHECK Constraints & Foreign Keys   │
                                                    │ • Composite Primary Keys             │
                                                    │ • TEXT Columns for Base64 Avatars    │
                                                    └──────────────────────────────────────┘
```

---

## ✨ Key Features & Engineering Highlights

### 1. 🔐 Cryptographic Authentication & Multi-Device Sessions
* **Opaque Bearer Tokens:** Tokens are generated with 32 bytes of cryptographically secure entropy (`secrets.token_urlsafe(32)`).
* **SHA-256 Database Hashing:** The raw token is sent to the client once; PostgreSQL stores only the **SHA-256 one-way hash** (`user_sessions.token_hash`). A compromised database dump reveals zero active tokens.
* **Multi-Device Support:** Users can be logged in concurrently across laptop and phone. Each session has independent UUID tracking, expiration timestamps, and an **"Active Now"** badge on the caller's current device.
* **IDOR Protection:** The session revocation endpoint (`DELETE /auth/sessions/{id}`) strictly binds to the caller: `WHERE id = :session_id AND user_id = :current_user_id`, completely preventing Insecure Direct Object Reference attacks.
* **Bulk Revocation:** A one-click **"Revoke All Other Sessions"** endpoint (`POST /auth/sessions/revoke-others`) instantly invalidates all foreign devices while keeping the active device logged in.
* **Password Visibility Toggle:** The login and registration modal includes an accessible SVG eye toggle to switch between `type="password"` and `type="text"`.

### 2. 📷 Profile Avatars & Base64 Storage in Database
* **Base64 Photo Upload:** Users can select any local image from their device in their Profile. The browser utilizes `FileReader.readAsDataURL(file)` to convert the image into a Base64 string (`data:image/jpeg;base64,...`).
* **PostgreSQL `TEXT` Column:** `users.avatar_small_url` and `users.avatar_large_url` are typed as PostgreSQL **`TEXT`** (which allows up to 1 GB of character data), allowing the database to store full Base64 image strings natively without truncation or requiring third-party S3 bucket configurations.
* **Hybrid Support:** The system seamlessly resolves remote CDN URLs (e.g. DiceBear SVG generator), local static fixture paths, or custom Base64 uploaded images.

### 3. ⚡ Live Breaking News & Trending Topics Panel
* **3-Tier Resilient Engine:**
  1. **Primary (Live Public News API):** Fetches real-time front-page tech and world news directly from Algolia Hacker News (`https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=6`). Operates with zero API keys and open CORS.
  2. **Secondary (Backend DB Hashtags):** A `/trends` endpoint in FastAPI that scans recent posts in PostgreSQL with regex `#[A-Za-z0-9_]+`, ranks them by frequency using Python `Counter`, and returns trending hashtags.
  3. **Tertiary (Curated Fallbacks):** Resilient default news topics ensuring the UI never breaks even during total offline conditions.
* **Interactive UI:** Features a blue **`● LIVE NEWS`** badge, engagement stats (points/comments), and direct links that open the real live article in a new tab.

### 4. 📝 15-Minute Post Edit Lock & Content Lifecycle
* **15-Minute Window:** When an author edits a post (`PATCH /posts/{id}`), the backend enforces:
  ```python
  if post.created_at + timedelta(minutes=15) < datetime.now(timezone.utc):
      raise ValidationError("Posts cannot be edited after 15 minutes", status_code=422)
  ```
* **Immutability:** Structural attributes (`kind`, `id`, `author_id`, `created_at`) cannot be altered. Attempts to submit them are rejected with `422 Unprocessable Entity` via Pydantic `extra="forbid"`.
* **Atomic Replies via `session.flush()`:** Inside `create_post()` ([`postgres_repository.py:181`](backend/app/repositories/postgres_repository.py#L181)), `session.flush()` queries PostgreSQL to generate the post's UUID inside the ongoing transaction, allowing reply notifications to immediately reference that ID before committing atomically.

### 5. 🗃️ User-Scoped Archive & Feed Filtering
* **Private Archive:** Users can archive their own posts. Archived IDs are persisted per-user in `localStorage` (`archive_ids_${currentUser.id}`).
* **Dynamic Feed Filtering:** Posts flagged as archived are filtered out of the active home feed and displayed exclusively in the private Archive tab.
* **Refreshes & De-duplication:** Feed refreshes retain the archived state, preventing archived items from leaking back into the feed.

### 6. 🛑 Account Deactivation (Soft Delete)
* **Lifecycle Endpoint:** `POST /users/me/deactivate`
* **Under the Hood:**
  1. Sets `users.is_active = False` in PostgreSQL.
  2. Sets `revoked_at = NOW()` on all active rows in `user_sessions` for that user.
  3. Immediately rejects all further API requests from that user with `401 Unauthorized` / `403 Forbidden`.

### 7. 📜 Dual-Sink Activity Audit Logger
* **Implementation:** [`backend/app/common/activity_logger.py`](backend/app/common/activity_logger.py)
* **Audit Trail:** Logs user actions (e.g., `@asha liked @devpatel's post`) formatted with ISO UTC timestamps.
* **Dual Sinks:** Simultaneously streams to `sys.stdout` (for cloud platform aggregation like Render/Docker) and writes to disk at `backend/logs/activity.log`.

---

## 🛡️ Middlewares & Cross-Cutting Concerns

Located in [`backend/app/main.py`](backend/app/main.py):

1. **`CORSMiddleware`:**
   Configured with explicit development origins (`http://localhost:5173`, `http://localhost:3000`) and a regex whitelist matching all Vercel deployment URLs (`allow_origin_regex=r"https:\/\/.*\.vercel\.app"`), enabling seamless client-server communication.
2. **`RequestIdMiddleware`:**
   Attaches a unique UUID (`X-Request-Id`) to every HTTP request and response header. Logs method, path, HTTP status, and duration in milliseconds without logging private credentials or connection strings.
3. **Global Exception Envelopes:**
   Custom error handlers capture `AppError`, Pydantic `RequestValidationError`, and unexpected exceptions, ensuring all responses follow a predictable JSON error contract (`{"error": {"code": "...", "message": "..."}}`).

---

## 🗄️ Database Schema & Alembic Migrations

PostgreSQL schema is versioned sequentially using **Alembic** (`backend/alembic/versions/`). Tracking is recorded in the PostgreSQL table **`alembic_version`**:

| Migration Revision | Description | Tables / Columns Altered |
| :--- | :--- | :--- |
| **`a62c769b5f6c`** | Initial schema | Creates `users`, `posts`, `post_media`, `likes`, `follows`. |
| **`8b08f98031ea`** | Password & Sessions | Adds `password_hash` to `users` and creates `user_sessions`. |
| **`de324b9397d4`** | Notifications | Creates `notifications` table with unique `dedup_key`. |
| **`f1e2d3c4b5a6`** | Bookmarks | Creates `bookmarks` table with composite PK `(user_id, post_id)`. |
| **`a1b2c3d4e5f6`** | Preferences | Creates `user_notification_preferences` table. |
| **`b2c3d4e5f6a1`** | Reports | Creates `post_reports` moderation table. |
| **`089a1f8a60c3`** | Deactivation | Adds `is_active` boolean column to `users`. |

### Database Constraints Deep-Dive:
* **`posts.author_id` (`RESTRICT`) vs `likes.user_id` (`CASCADE`):** Likes can vanish automatically when a user is deleted, but posts represent shared conversational history and cannot be deleted silently.
* **Post Shape Constraint (`CHECK`):** Ensures `kind IN ('original', 'reply', 'repost')` and enforces that `reply_to_id` is only present when `kind = 'reply'`, and `repost_of_id` is only present when `kind = 'repost'`.
* **Media Constraint:** `post_media.position BETWEEN 0 AND 3` with `UniqueConstraint("post_id", "position")` limits each post to at most 4 unique images.
* **No Self-Follow Constraint:** `CheckConstraint("follower_id <> following_id")`.

---

## 📂 Architecture Decision Records (ADRs)

Detailed architectural justifications are documented in [`backend/docs/decisions/`](backend/docs/decisions/):

* **[ADR 01: Account Identity and Session Model](backend/docs/decisions/01-identity-model.md)**: Database-backed opaque bearer tokens vs stateless JWTs.
* **[ADR 02: Profile Management and Account Deactivation](backend/docs/decisions/02-profile-and-deactivation.md)**: Soft-delete strategy and session invalidation.
* **[ADR 03: Social Graph and Privacy Boundary](backend/docs/decisions/03-follow-graph-and-privacy.md)**: Follow relationships and visibility boundaries.
* **[ADR 04: High-Performance Personalized Feed](backend/docs/decisions/04-personalized-feed.md)**: Keyset cursor pagination `(created_at, id)` vs offset pagination.
* **[ADR 05: Owned-Content Lifecycle and Edit/Delete Policy](backend/docs/decisions/05-owned-content-lifecycle.md)**: Cascading deletions and Last-Write-Wins concurrency.
* **[ADR 06: Notification Deduplication Boundary](backend/docs/decisions/06-notification-dedup-boundary.md)**: Unique `dedup_key` constraint preventing spam.
* **[ADR 07: Permission Matrix and Authorization Boundaries](backend/docs/decisions/07-permission-matrix.md)**: Access control across all endpoints.
* **[ADR 08: Post Edit Window & Content Immutability](backend/docs/decisions/08-post-edit-window-and-immutability.md)**: 15-minute edit time limit enforcement.
* **[ADR 09: Media and Base64 Avatar Storage Architecture](backend/docs/decisions/09-media-and-base64-storage.md)**: Storing Base64 data URLs in PostgreSQL `TEXT` columns.
* **[ADR 10: Multi-Device Session Management and IDOR Protection](backend/docs/decisions/10-multi-session-security-and-idor.md)**: Owner-scoped revocation queries.
* **[ADR 11: Real-Time Trending News & Live API Resilience](backend/docs/decisions/11-live-trending-news-and-resilience.md)**: 3-tier news fallback architecture.

---

## 💻 Local Development Setup

### 1. Prerequisites
* Python 3.11+
* Node.js 18+
* PostgreSQL running locally (default: `localhost:5432`)

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# Activate virtual environment:
# Windows (PowerShell):
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies:
pip install -r requirements.txt

# Run migrations to build tables and constraints:
alembic upgrade head

# Seed initial mock data (Asha, Dev, Maya, Leo, Zara, Kenji):
python -m app.db.seed

# Start the development server:
uvicorn app.main:app --reload --port 8000
```
* Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
* Liveness Healthcheck: `http://localhost:8000/health/live`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## ☁️ Production Deployment Guide

### A. Database (PostgreSQL)
1. Provision a free PostgreSQL instance on [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or [Render](https://render.com).
2. Obtain your connection string:
   ```text
   postgresql+asyncpg://<username>:<password>@<host>/<database>?ssl=require
   ```

### B. Backend Deployment (Render)
1. Connect your GitHub repository to **Render** as a **Web Service**.
2. Configure settings:
   * **Root Directory:** `backend`
   * **Build Command:** `pip install -r requirements.txt && alembic upgrade head && python -m app.db.seed`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment Variables:
   * `DATABASE_URL`: Your cloud PostgreSQL URL (starting with `postgresql+asyncpg://`).
   * `FRONTEND_ORIGIN`: Your production Vercel URL (e.g. `https://your-app.vercel.app`).

### C. Frontend Deployment (Vercel)
1. Import your GitHub repository into **Vercel**.
2. Configure settings:
   * **Root Directory:** `frontend`
   * **Framework Preset:** `Vite`
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
3. Environment Variables:
   * `VITE_API_BASE_URL`: Your live backend Render URL (e.g. `https://your-backend.onrender.com`).
4. Click **Deploy**.
