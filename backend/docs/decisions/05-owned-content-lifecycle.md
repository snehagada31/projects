# Decision Record 05: Owned-Content Lifecycle and Edit/Delete Policy

**Decision:**
Authenticated post creation tied strictly to the actor, author-only text edits with immutable post attributes (`kind`, `id`, `author_id`, `created_at` are immutable), Last-Write-Wins (LWW) edit conflict resolution, and author-only cascading deletes.

**Options considered:**
1. *Tombstone posts on delete (`"[deleted]"` placeholder)*: Keeps row in DB with nullified text; required if supporting deep multi-level comment trees where child comments should remain visible.
2. *Cascading row removal (Chosen)*: V1 supports single-level replies to originals. Removing an original deletes its likes, media, reposts, and direct replies atomically in one transaction. Eliminates orphaned conversation threads and avoids soft-delete query filter leakage.
3. *Mutable post metadata*: Allowing authors to change post kind (e.g., converting a reply to an original). Rejected: breaks relational invariants and shape checks.

**Authorization & Protection:**
- Only the author (`post.author_id == current_user.id`) may edit or delete a post.
- Non-author attempts are rejected with `403 FORBIDDEN`.
- Passing immutable fields (`author_id`, `id`, `kind`, `created_at`) to edit endpoint is rejected with `422 UNPROCESSABLE ENTITY` via Pydantic `extra="forbid"`.
- Deactivated accounts cannot edit or delete posts (`401 UNAUTHORIZED`).

**Deletion Behavior Across 9 Surfaces:**

| Surface | Behavior When Post is Deleted | Justification |
|---|---|---|
| 1. Detail (`GET /posts/{id}`) | Returns `404 NOT_FOUND` | Content is permanently removed |
| 2. Feed (`GET /feed`) | Post immediately omitted from paginated feed | Read join excludes non-existent rows |
| 3. Search (`GET /search/posts`) | Post immediately omitted from search results | Keyword query excludes non-existent rows |
| 4. Replies list (`GET /posts/{id}/replies`) | Returns `404 NOT_FOUND` | Target parent no longer exists |
| 5. Direct replies | Cascaded deletion removes reply rows | Prevents orphaned replies pointing to deleted parent |
| 6. Reposts | Cascaded deletion removes repost rows | Prevents broken repost cards pointing to missing original |
| 7. Likes | Cascaded deletion removes associated likes | Prevents like count leaks and dangling foreign keys |
| 8. Profile post count | Author's `postCount` decremented immediately | Derived authoritative aggregate count |
| 9. Repeated delete (`DELETE /posts/{id}`) | Returns `404 NOT_FOUND` safely | Idempotent / retry-safe without unexpected state change |

**Edit Conflict Policy:**
- Concurrent edits by multiple author sessions (e.g. phone vs. laptop) resolve via PostgreSQL row-level locks and Last-Write-Wins.
- Database state deterministically reflects the latest committed write with zero text corruption.

**Tests proving it:**
- `backend/tests/test_posts_lifecycle.py::test_author_can_edit_post`
- `backend/tests/test_posts_lifecycle.py::test_non_author_edit_rejected_with_403`
- `backend/tests/test_posts_lifecycle.py::test_immutable_edit_fields_rejected_with_422`
- `backend/tests/test_posts_lifecycle.py::test_author_delete_and_non_author_delete`
- `backend/tests/test_posts_lifecycle.py::test_delete_one_post_checks_all_9_surfaces`
- `backend/tests/test_posts_lifecycle.py::test_two_session_concurrent_edit_race`
