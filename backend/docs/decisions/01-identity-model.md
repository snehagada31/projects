# Decision Record 01: Account Identity and Session Model

**Decision:**
Opaque Bearer Token backed by a PostgreSQL `user_sessions` table (with SHA-256 token hashing), coupled with bcrypt password hashing for credentials.

**Options considered:**
1. *Stateless JWT*: Fast to verify without DB lookup, but impossible to revoke immediately on logout or account compromise without a central revocation store.
2. *Cookie-based sessions*: Traditional browser-only approach; introduces CSRF complexity when supporting non-browser or mobile clients.
3. *Database-backed Bearer Token (Chosen)*: Client sends `Authorization: Bearer <token>`, server checks hash against `user_sessions`. Enables instant revocation, auditability of active sessions, and fits our single PostgreSQL persistence store.

**Why this one:**
The PRD explicitly requires revocable sessions upon logout and account deactivation. Storing a cryptographic hash (`SHA-256`) of the session token in PostgreSQL ensures that:
- Sessions can be revoked instantly by setting `revoked_at = now()`.
- Even if the database is read by an unauthorized party, stolen token hashes cannot be used to impersonate sessions.
- Credentials use `bcrypt` (slow salt-based hashing), preventing rainbow-table attacks.
- Login failures use a dummy hash check to prevent timing attacks / user enumeration.

**Risks:**
- Each authenticated request requires a fast indexed session lookup.
  *Mitigation*: An index on `user_sessions(token_hash) WHERE revoked_at IS NULL` keeps lookup latency under 1ms.
- High-concurrency CPU load from password hashing on the async event loop.
  *Mitigation*: Run bcrypt hashing via `asyncio.to_thread` to prevent blocking the async event loop.

**Test proving it:**
- `backend/tests/test_auth.py::test_session_revocation_on_logout`
- `backend/tests/test_auth.py::test_timing_and_enumeration_resistance`
