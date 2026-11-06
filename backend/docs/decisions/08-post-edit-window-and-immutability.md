# Decision Record 08: Post Edit Time Window & Content Immutability

**Decision:**
Enforce a strict 15-minute time window for post text edits (`post.created_at + timedelta(minutes=15)`), restricted strictly to the original author, while preserving absolute immutability on post structural metadata (`id`, `author_id`, `kind`, `created_at`, `reply_to_id`, `repost_of_id`).

**Options considered:**
1. *Unlimited edit window*: Allows authors to edit post content anytime. Rejected: in social discussion platforms, unlimited edits allow malicious authors to alter the meaning of popular posts or gaslight replies that responded to original statements.
2. *Client-only 15-minute timer*: Frontend hides the "Edit" button after 15 minutes. Rejected: trivial to bypass via Postman, cURL, or automated scripts directly hitting the `PATCH /posts/{id}` endpoint.
3. *Authoritative server-side UTC comparison (Chosen)*: The backend repository compares `datetime.now(timezone.utc)` against `post.created_at + timedelta(minutes=15)`. Rejects expired edits with HTTP `422 Unprocessable Entity` ("Posts cannot be edited after 15 minutes").

**Why this one:**
- **Integrity**: Enforces social conversation integrity by ensuring comments and replies cannot have their context altered hours or days later.
- **Security & Ownership**: Only the post author (`post.author_id == current_user.id`) can trigger the edit endpoint; non-authors receive `403 Forbidden`.
- **Defense-in-depth**: Both frontend UI (countdown/hiding edit button) and backend repository layers reject expired edits.

**Risks:**
- Clock drift between distributed application servers and PostgreSQL.
  *Mitigation*: All timestamps use UTC precision (`TIMESTAMP WITH TIME ZONE`) populated by PostgreSQL server-default `now()`.

**Verification:**
- `backend/app/repositories/postgres_repository.py::update_post_text`
- Unit verification: Post edited at T+10m succeeds; post edited at T+16m raises `ValidationError(422)`.
