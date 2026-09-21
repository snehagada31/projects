# Async Session Boundaries — FastAPI & SQLAlchemy 2.0

This document explains the lifecycle of SQLAlchemy's `AsyncSession` across requests, the transaction boundaries during failures, and how the social feed remains bounded.

---

## 1. Why `len(post)` is not a license to load all comments

In the earlier Topic 12 OOP exercise, Python objects could implement `__len__` or store a list of comments directly:
```python
class Post:
    def __init__(self, comments=None):
        self.comments = comments or []
    def __len__(self):
        return len(self.comments)
```
In a relational database, accessing comments or reactions by loading the entire list into memory would turn a simple count into an `O(N)` memory and network disaster. 

- **At the database boundary**: Like counts and reply counts are computed using SQL aggregation:
  ```sql
  SELECT COUNT(*) FROM posts WHERE reply_to_id = :post_id;
  ```
- **At the repository boundary**: Repositories return bounded scalars (`get_reply_count`, `get_like_count`) or grouped aggregate batches across a page of IDs. No rows of comments or likes are transferred just to count them.
- **Bounding the feed**: The feed query selects only `limit + 1` rows using a strict tuple filter `(created_at, id) < (:created_at, :id)`. The extra record determines `hasMore` and `nextCursor`.

---

## 2. Request Timeline: Successful GET /feed

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant FastAPI as FastAPI Route
    participant DI as Depends(get_db_session)
    participant Session as AsyncSession
    participant Repo as PostgresSocialRepository
    participant DB as PostgreSQL

    Client->>FastAPI: GET /feed?limit=10
    FastAPI->>DI: Request dependency resolution
    DI->>Session: async with async_session_factory()
    Session-->>FastAPI: Yield session scoped to request
    FastAPI->>Repo: list_original_feed(cursor, limit=10)
    Repo->>Session: execute(SELECT ... ORDER BY created_at DESC, id DESC LIMIT 11)
    Session->>DB: Send SQL over asyncpg connection
    DB-->>Session: Return 11 rows
    Session-->>Repo: Result rows
    Repo->>FastAPI: Convert 10 items to Pydantic schemas, derive nextCursor & hasMore
    FastAPI-->>Client: 200 OK (JSON response)
    FastAPI->>Session: Exit async with context (Auto Close & Return Connection to Pool)
```

---

## 3. Failed Transaction Timeline: Integrity Violation & Rollback

When creating a reply or repost that violates relational invariants or duplicates an existing repost:

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant FastAPI as FastAPI Route
    participant Service as PostService
    participant Session as AsyncSession
    participant DB as PostgreSQL

    Client->>FastAPI: POST /posts (duplicate repost)
    FastAPI->>Service: create_repost(author_id, repost_of_id)
    Service->>Session: async with session.begin():
    Note over Session,DB: BEGIN Transaction
    Service->>Session: session.add(repost_instance)
    Service->>Session: session.flush()
    Session->>DB: INSERT INTO posts (author_id, repost_of_id, kind='repost')
    DB-->>Session: ERROR: duplicate key value violates unique constraint "unique_user_repost"
    Session-->>Service: Raise IntegrityError
    Note over Service,Session: Caught IntegrityError
    Session->>DB: ROLLBACK Transaction
    DB-->>Session: Rollback complete (no partial row survives)
    Session->>Session: Exit transaction context
    Service->>FastAPI: Raise ConflictError(409, "user has already reposted this original post")
    FastAPI-->>Client: 409 Conflict Error Envelope
```

---

## Key Rules Followed:
1. **Never share sessions across concurrent tasks**: Each HTTP request receives its own session via FastAPI dependency injection.
2. **Commit / Rollback at the Service boundary**: Repositories execute queries; transactions are managed explicitly around discrete business actions.
3. **expire_on_commit=False**: Attributes accessed after commit do not trigger unexpected lazy loads after the session is closed.
