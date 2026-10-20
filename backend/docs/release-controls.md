# Release Controls, Security & Migration Guide (Stage 7 / PY-P0-07)

## 1. Forward Migration Path from V1 to V2

### Database Migrations Applied:
1. `8b08f98031ea_add_password_hash_and_user_sessions.py`:
   - Adds nullable `password_hash` column to `users`.
   - Creates `user_sessions` table with indexes on `token_hash` and `user_id`.
2. `089a1f8a60c3_add_is_active_to_users.py`:
   - Adds `is_active` boolean column with default `true` to `users`.
3. `de324b9397d4_create_notifications_table.py`:
   - Creates `notifications` table with compound `dedup_key UNIQUE` constraint and foreign key cascades.

### Upgrading from V1 Database:
```bash
# Apply all forward migrations
alembic upgrade head
```

### Handling Legacy V1 Users without Passwords:
- Existing V1 seeded users have `password_hash = NULL`.
- They cannot sign in via `/auth/login` until they set a credential.
- Legacy users can claim their account or test accounts can be initialized with seed passwords.
- Public read access to their profiles and past posts remains 100% functional.

---

## 2. Configuration & Security Hardening

| Setting | Production Recommendation | Justification |
|---|---|---|
| `DATABASE_URL` | SSL-enabled connection string (`postgresql+asyncpg://...`) | Prevents plaintext credential transport over the network |
| `FRONTEND_ORIGIN` | Explicit trusted domain (e.g. `https://social.example.com`) | Never use `*` wildcard when credentials (`allow_credentials=True`) are enabled |
| Session Token TTL | 24 Hours (`SESSION_TTL_HOURS = 24`) | Bounds exposure window if a client token is compromised |
| Password Hashing | `bcrypt` with `asyncio.to_thread` | Prevents event-loop freezing while resisting brute-force attacks |
| Error Envelope | V1 standard `{"error": {"code": "...", "message": "..."}, "requestId": "..."}` | Consistent client error handling without leaking stack traces or SQL internals |

---

## 3. Observability & Tracing via Request IDs
- Every request passing through `RequestIdMiddleware` receives an `X-Request-Id` response header.
- If the incoming client supplies `X-Request-Id`, it is preserved; otherwise a new UUID is generated.
- Allows tracing allowed vs denied requests across log streams.

---

## 4. Rollback Considerations
- If a deployment must be rolled back:
  ```bash
  alembic downgrade -1
  ```
- Rolling back `de324b9397d4` drops the `notifications` table cleanly without touching `posts`, `users`, or `likes`.
- Rolling back `089a1f8a60c3` removes `is_active`.
- Backward compatibility: V1 public endpoints continue working without code changes.

---

## 5. Known Limitations
- Real-time WebSocket delivery is deferred to P2 per PRD scope.
- Notifications are pull-based via `GET /notifications` and `GET /notifications/unread-count`.
- Full recommendation ranking and search fuzzy matching are deferred to P2.
