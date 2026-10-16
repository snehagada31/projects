# Decision Record 02: Owned Profile and Account State

**Decision:**
Allowlist-based profile updates using Pydantic `extra="forbid"`, immutable handles, and soft account deactivation (`is_active = false`).

**Options considered:**
1. *Mutable handle with historical redirection table*: Allows users to change handles, but requires tracking old handles to redirect `@mentions` and prevents handle recycling.
2. *Immutable handle (Chosen)*: Handles remain permanent identifiers chosen at registration. Eliminates broken citations, URL tampering, and `@mention` ambiguity.
3. *Hard delete on deactivation*: Purges user rows from DB; causes orphaned posts, broken threads, and foreign key cascades.
4. *Soft deactivation (Chosen)*: Flag `is_active = false`. Preserves referential integrity for existing posts while hiding profile and revoking sessions.

**Field Access Matrix (PRD Checkpoint):**

| Field | Read Access | Write Access | Edit Rule |
|---|---|---|---|
| `id` | Public | None | **Immutable** (system-assigned UUID) |
| `handle` | Public | None | **Immutable** (assigned at registration) |
| `display_name` | Public | Owner only | 1–100 chars, non-empty, trimmed |
| `bio` | Public | Owner only | Up to 280 chars |
| `avatar_small_url` | Public | Owner only | Valid non-empty URL |
| `avatar_large_url` | Public | Owner only | Valid non-empty URL |
| `password_hash` | Private (None) | Owner only (auth) | Never exposed in any public response |
| `is_active` | Public state | Owner only | Boolean toggle (`POST /users/me/deactivate`) |
| `created_at` | Public | None | **Immutable** timestamp |
| `post_count` | Public | None | **Derived / Computed** at read time |
| `follower_count`| Public | None | **Derived / Computed** at read time |
| `following_count`| Public | None | **Derived / Computed** at read time |

**Conflict & Concurrency Policy:**
- Strict `extra="forbid"` on `ProfileUpdateRequest`: Any attempt to pass immutable fields (`id`, `handle`, `created_at`, `follower_count`) or unknown fields is rejected with `422 Unprocessable Entity`.
- Cross-user update guard: `PATCH /users/{id}` where `{id} != actor.id` is rejected with `403 FORBIDDEN`.

**Test proving it:**
- `backend/tests/test_profile.py::test_cross_user_update_rejected_with_403`
- `backend/tests/test_profile.py::test_immutable_fields_rejected_with_422`
- `backend/tests/test_profile.py::test_account_deactivation`
