# Decision Record 05: Owned-Content Lifecycle and Edit/Delete Policy

**Decision:**
Authenticated post creation tied strictly to the actor, author-only text edits with immutable post attributes (`kind`, `id`, `author_id`, `created_at` are immutable), and author-only cascading deletes.

**Options considered:**
1. *Tombstone posts on delete (`"[deleted]"` placeholder)*: Keeps row in DB with nullified text; required if supporting multi-level replies where child comments should remain visible.
2. *Cascading row removal (Chosen)*: V1 supports single-level replies to originals. Removing an original deletes its likes, media, reposts, and direct replies atomically in one transaction. Eliminates orphaned conversation threads.
3. *Mutable post metadata*: Allowing authors to change post kind (e.g., converting a reply to an original). Rejected: breaks relational invariants and shape checks.

**Authorization & Protection:**
- Only the author (`post.author_id == current_user.id`) may edit or delete a post.
- Non-author attempts are rejected with `403 FORBIDDEN`.
- Passing immutable fields (`author_id`, `id`, `kind`, `created_at`) to edit endpoint is rejected with `422 UNPROCESSABLE ENTITY` via Pydantic `extra="forbid"`.

**Test proving it:**
- `backend/tests/test_posts_lifecycle.py::test_author_can_edit_post`
- `backend/tests/test_posts_lifecycle.py::test_non_author_edit_rejected_with_403`
- `backend/tests/test_posts_lifecycle.py::test_author_can_delete_post`
- `backend/tests/test_posts_lifecycle.py::test_immutable_edit_fields_rejected_with_422`
