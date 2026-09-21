-- Two demonstrations required by the PRD:
-- 1. A real rollback: valid insert + invalid insert in one transaction,
--    neither survives.
-- 2. Concurrent duplicate-like race — run via TWO SEPARATE psql
--    processes to prove the database serializes them.

-- ============================================================
-- PART 1 — Transaction rollback
-- Run this as a single script. Expect: an error on the second INSERT,
-- then after ROLLBACK, the like count for post 001 is unchanged (2).
-- ============================================================
BEGIN;

INSERT INTO likes (user_id, post_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001');

SELECT count(*) AS likes_mid_transaction
FROM likes WHERE post_id = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001';
-- expect 3 here — the valid insert above IS visible within this transaction

-- Deliberately invalid — this user_id does not exist:
INSERT INTO likes (user_id, post_id)
VALUES ('99999999-9999-4999-8999-999999999999', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001');
-- expect: ERROR — foreign key violation

ROLLBACK;

SELECT count(*) AS likes_after_rollback
FROM likes WHERE post_id = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001';
-- expect 2 — back to the original count; the valid insert did NOT survive either


-- ============================================================
-- PART 2 — Concurrent duplicate-like race
-- This part CANNOT run as one script — it needs two separate psql
-- processes running at the same time. Run these two files:
--
--   Terminal 1: psql -d social_feed_test -f session_a.sql
--   Terminal 2 (within ~1 second): psql -d social_feed_test -f session_b.sql
--
-- session_a.sql:
--   BEGIN;
--   INSERT INTO likes (user_id, post_id) VALUES ('<user>', '<post>');
--   SELECT pg_sleep(3);
--   COMMIT;
--
-- session_b.sql:
--   SELECT pg_sleep(1);
--   BEGIN;
--   INSERT INTO likes (user_id, post_id) VALUES ('<user>', '<post>');  -- SAME pair
--   COMMIT;
--
-- Expected result: Session B's INSERT blocks (waits) once it hits the
-- row Session A already inserted-but-not-yet-committed. Once Session A
-- commits, Session B's blocked insert resumes, sees the now-committed
-- conflicting row, and fails with a unique constraint violation. Only
-- ONE row ever exists for that (user_id, post_id) pair — proven by:
--
--   SELECT count(*) FROM likes WHERE user_id='<user>' AND post_id='<post>';
--   -- returns 1, not 2, regardless of how close together the two
--   -- INSERT attempts were