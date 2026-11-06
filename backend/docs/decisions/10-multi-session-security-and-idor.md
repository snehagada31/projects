# Decision Record 10: Multi-Device Session Management and IDOR Protection

**Decision:**
Support concurrent multi-device logins per user account via the `user_sessions` table, provide distinct client identification (`This Device (Current)` vs `Other Logged-in Device`), and strictly enforce ownership checks on session revocation to eliminate Insecure Direct Object Reference (IDOR) vulnerabilities.

**Options considered:**
1. *Single session enforcement*: Logging in from a laptop automatically invalidates any existing phone session. Rejected: poor user experience in modern social apps where users expect to stay logged in across both their phone and laptop simultaneously.
2. *Unscoped session deletion (`DELETE /auth/sessions/{id}`)*: Simply deletes the row by `id`. Rejected: critical IDOR vulnerability where an authenticated user could scrape or guess another user's session UUID and terminate their session without permission.
3. *Owner-scoped session revocation with "Revoke Others" capability (Chosen)*:
   - Specific session revocation queries by both ID and User ID:
     `DELETE FROM user_sessions WHERE id = :session_id AND user_id = :current_user_id`
   - Bulk revocation endpoint (`POST /auth/sessions/revoke-others`) invalidates all other active sessions except the caller's active token.

**Why this one:**
- **Security & Authorization**: Completely eliminates IDOR; if User A submits User B's session UUID to `DELETE /auth/sessions/{id}`, 0 rows match and the API returns `404 Not Found` or `403 Forbidden`.
- **Account Control & Anti-Hijacking**: If an account is shared or compromised, the legitimate user can click "Revoke all other active sessions" to immediately kick out all other logged-in devices while keeping their own current session intact.
- **Client Transparency**: Session metadata (`created_at`, `expires_at`, active status) is displayed in the user profile with a clear "Active Now" indicator for the caller's current device.

**Risks:**
- Accumulation of expired or revoked session rows in PostgreSQL.
  *Mitigation*: Queries explicitly filter `revoked_at IS NULL AND expires_at > now()`, indexed by `token_hash`.

**Verification:**
- `backend/app/api/auth.py::revoke_session_by_id`
- `backend/app/repositories/postgres_repository.py::revoke_session_by_id`
- `backend/app/repositories/postgres_repository.py::revoke_other_sessions`
