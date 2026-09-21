-- Demonstrates both VALID inserts (succeed) and INVALID ones (correctly
-- rejected). Each negative test uses SAVEPOINT/ROLLBACK TO SAVEPOINT so
-- one expected failure doesn't abort the whole script — every check
-- after it still runs.

BEGIN;

-- ============================================================
-- TEST 1: duplicate handle -> should FAIL (unique constraint)
-- ============================================================
SAVEPOINT sp1;
INSERT INTO users (handle, display_name, avatar_small_url, avatar_large_url)
VALUES ('asha', 'Duplicate Asha', '/x.jpg', '/x.jpg');
ROLLBACK TO SAVEPOINT sp1;

-- ============================================================
-- TEST 2: orphan foreign key (author_id doesn't exist) -> should FAIL
-- ============================================================
SAVEPOINT sp2;
INSERT INTO posts (author_id, kind, text)
VALUES ('99999999-9999-4999-8999-999999999999', 'original', 'this author does not exist');
ROLLBACK TO SAVEPOINT sp2;

-- ============================================================
-- TEST 3: duplicate like (same user, same post twice) -> should FAIL
-- ============================================================
SAVEPOINT sp3;
INSERT INTO likes (user_id, post_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001');
ROLLBACK TO SAVEPOINT sp3;

-- ============================================================
-- TEST 4: self-follow -> should FAIL (CHECK constraint)
-- ============================================================
SAVEPOINT sp4;
INSERT INTO follows (follower_id, following_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1');
ROLLBACK TO SAVEPOINT sp4;

-- ============================================================
-- TEST 5: duplicate follow pair -> should FAIL
-- ============================================================
SAVEPOINT sp5;
INSERT INTO follows (follower_id, following_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2');
ROLLBACK TO SAVEPOINT sp5;

-- ============================================================
-- TEST 6: text over 280 code points -> should FAIL
-- ============================================================
SAVEPOINT sp6;
INSERT INTO posts (author_id, kind, text)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', repeat('x', 281));
ROLLBACK TO SAVEPOINT sp6;

-- ============================================================
-- TEST 7: repost WITH text -> should FAIL (kind_shape_check)
-- ============================================================
SAVEPOINT sp7;
INSERT INTO posts (author_id, kind, text, repost_of_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'repost', 'reposts cannot have text', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001');
ROLLBACK TO SAVEPOINT sp7;

-- ============================================================
-- TEST 8: reply pointing to a REPLY (not an original) -> should FAIL (trigger)
-- ============================================================
SAVEPOINT sp8;
INSERT INTO posts (author_id, kind, text, reply_to_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'reply', 'a reply to a reply, not allowed',
        'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb031');  -- ...031 is itself a REPLY, not an original
ROLLBACK TO SAVEPOINT sp8;

-- ============================================================
-- TEST 9: media on a REPLY (not an original) -> should FAIL (trigger)
-- ============================================================
SAVEPOINT sp9;
INSERT INTO post_media (post_id, alt_text, width, height, position, small_url, large_url)
VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb031', 'should not be allowed', 100, 100, 0, '/x.jpg', '/x.jpg');
ROLLBACK TO SAVEPOINT sp9;

-- ============================================================
-- TEST 10: 5th media row on a post that already has 2 -> should FAIL if
-- we push it to 5 total; demonstrating the LIMIT by adding 3 more to
-- post ...001 (which already has 2), the 3rd of these three hits the cap
-- ============================================================
SAVEPOINT sp10;
INSERT INTO post_media (post_id, alt_text, width, height, position, small_url, large_url)
VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001', 'third image', 100, 100, 2, '/x.jpg', '/x.jpg');
SAVEPOINT sp10b;
INSERT INTO post_media (post_id, alt_text, width, height, position, small_url, large_url)
VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001', 'fourth image', 100, 100, 3, '/x.jpg', '/x.jpg');
-- post ...001 now has 4 media rows (2 original + these 2) — at the cap
SAVEPOINT sp10c;
INSERT INTO post_media (post_id, alt_text, width, height, position, small_url, large_url)
VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001', 'fifth image - should fail', 100, 100, 0, '/x.jpg', '/x.jpg');
-- position 0 is already taken too, but the media LIMIT trigger fires first
ROLLBACK TO SAVEPOINT sp10;  -- rolls back all three of these test inserts together

-- ============================================================
-- TEST 11: duplicate repost (same user reposts same original twice) -> should FAIL
-- ============================================================
SAVEPOINT sp11;
INSERT INTO posts (author_id, kind, repost_of_id)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'repost', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001');
-- user ...aaa2 already reposted ...001 via post ...043
ROLLBACK TO SAVEPOINT sp11;

-- ============================================================
-- TEST 12 (positive case): a genuinely VALID original -> should SUCCEED
-- ============================================================
SAVEPOINT sp12;
INSERT INTO posts (author_id, kind, text)
VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', 'this is a perfectly valid new post');
-- no rollback here — this one should actually stick... but we roll back
-- the WHOLE outer transaction at the end anyway, to leave the seeded
-- database exactly as it was before this test file ran.

ROLLBACK;  -- undoes everything in this file, including the valid test-12 insert