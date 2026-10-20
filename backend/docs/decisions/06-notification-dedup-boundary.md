# Decision Record 06: Notification Consistency, Atomicity, and Deduplication Boundary

**Decision:**
Same-transaction notification creation with database-enforced compound dedup keys, authoritative unread counts, and soft tombstoning for deleted content.

**Options considered:**
1. *Asynchronous message queue / event bus (Outbox / Kafka / Celery)*: Decouples notification delivery from HTTP request, but introduces eventual consistency, requires running background workers/brokers (violating P0 single-service constraint), and risks race conditions on read-your-own-writes.
2. *Application-level check-then-insert*: Checking `has_notified()` before inserting. Fails under concurrency: concurrent double-tap likes produce duplicate notifications.
3. *Same-transaction write with database compound uniqueness (Chosen)*:
   - Notifications are created within the exact same database transaction as the source action (like, follow, repost, reply).
   - If the source write rolls back or fails, PostgreSQL transaction rollback guarantees zero orphaned/ghost notifications.
   - Database enforces a `UNIQUE(dedup_key)` constraint. Concurrent retries converge on exactly one notification row via `ON CONFLICT (dedup_key) DO NOTHING`.

**Dedup Key Strategy:**
- Like: `like:{actor_id}:{post_id}`
- Follow: `follow:{actor_id}:{recipient_id}`
- Repost: `repost:{actor_id}:{post_id}`
- Reply: `reply:{reply_post_id}`

**Self-Action & Privacy Invariants:**
- Self-actions (`actor_id == recipient_id`) are unconditionally suppressed (no self-notifications).
- Notifications are strictly recipient-scoped (`recipient_id == current_user.id`). Any attempt to inspect or mark another user's notification as read is rejected with `403 FORBIDDEN` or `404 NOT_FOUND` (anti-IDOR).
- Deactivated actors are rendered safely as `[Deactivated User]`.
- Deleted posts retain the notification with `post_id = null` (tombstone) via foreign key `ON DELETE SET NULL`, preserving notification history without broken links.

**Test proving it:**
- `backend/tests/test_notifications.py::test_notification_created_on_like_follow_repost_reply`
- `backend/tests/test_notifications.py::test_self_actions_produce_no_notifications`
- `backend/tests/test_notifications.py::test_concurrent_like_retry_deduplication`
- `backend/tests/test_notifications.py::test_cross_user_notification_access_rejected`
- `backend/tests/test_notifications.py::test_mark_read_and_unread_counts`
- `backend/tests/test_notifications.py::test_source_rollback_leaves_no_orphaned_notification`
- `backend/tests/test_notifications.py::test_deleted_post_tombstone_in_notifications`
