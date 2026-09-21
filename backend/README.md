# Social Feed — Python/FastAPI Backend (Stage A)

Stage A of the Social Feed assignment: a fixture-backed FastAPI server implementing the shared API contract (see `00_Assignment_Brief_and_API_Contract.md`). No database yet — that's Stage B/C.

## Project structure

```
backend/
├── labs/raw_asgi/        # A1: raw ASGI server, no FastAPI
├── app/
│   ├── main.py            # application factory + lifespan
│   ├── config.py          # validated settings (env vars)
│   ├── models.py          # earlier illustrative OOP classes (Post/Comment/Like)
│   ├── api/                # routers: health, feed, posts, users
│   ├── schemas/            # Pydantic response models (camelCase contract)
│   ├── services/           # business logic — builds schema objects from raw data
│   ├── repositories/       # data access — the ONLY layer touching fixtures
│   ├── common/              # cursor encode/decode, error envelope, request ID, fake I/O
│   └── fixtures/            # deterministic fixed test data (6 users, 46 posts, etc.)
├── tests/                    # pytest suite (21 tests)
├── pyproject.toml
├── pytest.ini
└── .env.example
```

## Setup

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -e .
pip install -e ".[dev]"       # adds pytest, httpx, pytest-asyncio
```

Copy `.env.example` to `.env` and fill in real values (a real `.env` is never committed — see `.gitignore`):

```
PORT=8000
FRONTEND_ORIGIN=http://localhost:5173
DEMO_USER_ID=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1
SIMULATED_IO_MS=300
DATABASE_URL=postgres://...   # not used yet at Stage A — required later
```

`DEMO_USER_ID` must be a valid UUID matching one of the six fixed users in `app/fixtures/social_fixtures.py` — it's the "development identity" used to resolve `likedByViewer` in the absence of real authentication (see the brief's "Development identity" section).

## Running the server

```bash
cd backend
uvicorn app.main:app --reload
```

- Interactive docs: http://127.0.0.1:8000/docs
- Liveness: http://127.0.0.1:8000/health/live
- Feed: http://127.0.0.1:8000/feed?cursor=&limit=10
- Post detail: http://127.0.0.1:8000/posts/{id}
- User profile: http://127.0.0.1:8000/users/{id}

Use real IDs from `app/fixtures/social_fixtures.py` — all IDs are fixed/deterministic, not randomly generated, so the same data exists on every restart.

## Running the raw ASGI lab (A1) separately

```bash
cd backend/labs/raw_asgi
uvicorn app:app --lifespan off
```

`--lifespan off` is deliberate: this toy server has nothing to set up on startup (no database, no cache), so it explicitly skips the lifespan handshake instead of silently ignoring it. See `wsgi_vs_asgi.md` in that folder for the WSGI/ASGI comparison.

## Running the tests

```bash
cd backend
pytest tests/ -v
```

21 tests, covering:
- Feed pagination: default page size, three-page traversal with no duplicates/skips, the deliberate timestamp tie
- Query validation: invalid limit, limit over 50, duplicate params, legacy `page` param — all 400
- Post/user detail: valid lookups, malformed UUID (400) vs well-formed-but-missing UUID (404), repost `referencedPost`
- **Dependency override** (`test_dependency_override.py`): swaps the real repository for a fake one via `app.dependency_overrides`, proving routes never hardcode their data source
- **Concurrency** (`test_concurrency.py`): fires 3 requests simultaneously with `asyncio.gather`, asserts total time is close to one request's duration (not three), proving nonblocking overlap — not just "marked async"
- **Cancellation/cleanup** (`test_cancellation_cleanup.py`): forces an exception and a task cancellation inside `fake_io_operation`, asserts the cleanup log line still fires both times, then confirms the server still responds afterward

## Answering the mentor's required questions

**Where are inputs validated?**
`app/common/query_validation.py` (query params: cursor, limit, duplicate/unknown rejection) and the `_validate_post_id`/`_validate_user_id` functions in `app/api/posts.py` / `users.py` (path param UUID format).

**Where do product rules live?**
`app/services/post_service.py` — e.g. `postCount` counting originals only, `likedByViewer` resolving from the configured demo identity, not client input.

**Where is data accessed?**
`app/repositories/social_repository.py` exclusively. Routes and services never touch `app/fixtures/` directly — they go through the repository, which is what makes `test_dependency_override.py` possible.

**Which database constraint prevents duplicates?**
None yet — Stage A has no database. This becomes relevant in Stage B (modeling) and C (persistence), where a unique constraint (e.g. on `(follower_id, following_id)` for follows, or `(user_id, post_id)` for likes) would enforce it at the database level instead of only in application code.

**How does the cursor work?**
`app/common/cursor.py` encodes `{"v": 1, "createdAt": ..., "id": ...}` as base64url. `app/common/pagination.py` decodes it back to a `(created_at, id)` tuple and returns only items strictly "smaller" than that tuple (since the list is sorted `created_at DESC, id DESC`), reading `limit + 1` rows to determine `hasMore` without a separate count query.

**What happens when the database or a write fails?**
Not yet applicable — Stage A is read-only with no database. This will be answered concretely once Stage C adds real persistence and write endpoints (`SERVICE_UNAVAILABLE` / `CONFLICT` error codes are already defined in `app/common/errors.py`, ready for that stage).

## Known gaps at this stage (intentional, per PRD scope)

- No database — `DATABASE_URL` is accepted in config but unused.
- `/posts/{id}/replies`, `/users/{id}/media`, `/search/posts` are marked "Extension" for Stage A in the brief and are not yet built.
- The existing React frontend still points at an earlier, differently-shaped backend (snake_case fields) and has **not** been reconnected to this contract yet — the response shapes are genuinely incompatible (camelCase, nested `author`/`media` objects) and reconnecting is separate follow-up work, not done as part of Stage A's Must requirements.