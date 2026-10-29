# 🌐 Social Feed Platform (Python FastAPI + React)

A high-performance, full-stack social media feed platform built with **FastAPI** (asynchronous Python), **PostgreSQL** (via SQLAlchemy Async Engine), and a **React 18** SPA frontend with dark-mode UI.

---

## 🏗️ Architecture Overview

* **Backend**: FastAPI 0.115+, Python 3.11+ async/await, Pydantic v2 schemas.
* **Database**: PostgreSQL with connection pooling (`asyncpg`), Alembic database schema migrations.
* **Authentication**: Cryptographically secure 32-byte opaque session tokens (SHA-256 hashed in database, stored in browser `localStorage`).
* **Feed Architecture**: Keyset / cursor-based pagination `(created_at, post_id)` for scalable $O(1)$ data retrieval.
* **Frontend**: React 18, Vite, responsive Twitter/X-style dark interface.

---

## 🚀 Stages Breakdown (PY-01 to PY-07)

* **Stage 1 (PY-01) — Account & Session Identity**:
  * Registration & login with handle normalization and password verification.
  * Opaque session tokens with 24-hour TTL, instant logout revocation, and anti-timing enumeration defenses.
* **Stage 2 (PY-02) — High-Performance Feed & Cursors**:
  * Keyset cursor pagination encoding `(created_at, id)` preventing pagination drifts.
  * Unauthenticated public feeds and authenticated personalized feeds.
* **Stage 3 (PY-03) — Profile Management & Dynamic Counts**:
  * Real-time dynamic counts for posts, followers, and following.
  * Profile viewing and editing (display name, bio, avatars).
* **Stage 4 (PY-04) — Social Graph & Follow Relationships**:
  * Idempotent follow/unfollow operations.
  * Activity notifications triggered on interactions (likes, follows).
* **Stage 5 (PY-05) — Discovery & User Search**:
  * Case-insensitive prefix/substring search across user handles and names.
  * Smart recommendations and follow status detection.
* **Stage 6 (PY-06) — Bookmarks & Moderation Reporting**:
  * Private post bookmarking collection per user.
  * Moderation reporting system for post violations.
* **Stage 7 (PY-07) — Account Lifecycle (Soft Delete)**:
  * Safe account deactivation (`is_active = False`) preserving relational integrity.
  * Instant session revocation blocking future logins.

---

## 💻 Local Development Setup

### 1. Prerequisites
* Python 3.11+
* Node.js 18+
* PostgreSQL running locally (e.g. `localhost:5432`)

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## ☁️ Deployment Guide

### A. Deploy Database (PostgreSQL)
1. Create a free PostgreSQL database on [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or [Render](https://render.com).
2. Copy your PostgreSQL connection string:
   ```text
   postgresql+asyncpg://<user>:<password>@<host>/<database>?ssl=require
   ```

### B. Deploy Backend (Render / Railway)
1. Push your repository to **GitHub**.
2. Go to [Render.com](https://render.com) and create a **New Web Service**.
3. Connect your GitHub repository:
   * **Root Directory**: `backend`
   * **Build Command**: `pip install -r requirements.txt && alembic upgrade head && python -m app.db.seed`
   * **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables in Render:
   * `DATABASE_URL`: `postgresql+asyncpg://...` (from Step A)
   * `FRONTEND_ORIGIN`: `https://your-frontend-url.vercel.app` (your Vercel URL)
5. Deploy service and copy your backend URL (e.g. `https://social-backend.onrender.com`).

### C. Deploy Frontend (Vercel)
1. Go to [Vercel.com](https://vercel.com) and click **Add New > Project**.
2. Import your GitHub repository.
3. Configure the project:
   * **Root Directory**: Click edit and select `frontend`
   * **Framework Preset**: Vite
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist`
4. Add **Environment Variables**:
   * Name: `VITE_API_BASE_URL`
   * Value: `https://social-backend.onrender.com` (your Render backend URL, without trailing slash)
5. Click **Deploy**.

---

## 🔒 Security Best Practices Implemented
* Session tokens are hashed via SHA-256 before storing in the database.
* Passwords verified using constant-time comparison against timing enumeration attacks.
* Dynamic CORS origin protection.
* Soft-delete data protection avoiding cascading database anomalies.
