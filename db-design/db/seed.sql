-- Deterministic seed — same fixed IDs/data as app/fixtures/social_fixtures.py
-- in the Stage A Python app, so both stages describe the same imagined data.
-- Idempotent: ON CONFLICT DO NOTHING means re-running this never duplicates
-- rows — safe to run against a database that's already seeded.

BEGIN;

-- ---------------- users (6) ----------------
INSERT INTO users (id, handle, display_name, bio, avatar_small_url, avatar_large_url) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'asha', 'Asha', 'Building things, one commit at a time.', '/fixtures/asha-48.jpg', '/fixtures/asha-96.jpg'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'devpatel', 'Dev Patel', 'Backend and infra.', '/fixtures/dev-48.jpg', '/fixtures/dev-96.jpg'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'mayachen', 'Maya Chen', NULL, '/fixtures/maya-48.jpg', '/fixtures/maya-96.jpg'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'leomartins', 'Leo Martins', 'Design + frontend.', '/fixtures/leo-48.jpg', '/fixtures/leo-96.jpg'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'zaraahmed', 'Zara Ahmed', 'Learning in public.', '/fixtures/zara-48.jpg', '/fixtures/zara-96.jpg'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'kenjiw', 'Kenji Watanabe', NULL, '/fixtures/kenji-48.jpg', '/fixtures/kenji-96.jpg')
ON CONFLICT (id) DO NOTHING;

-- ---------------- originals (30) ----------------
-- author cycles through the 6 users; two originals (posts 005, 006)
-- deliberately share an identical created_at for the tie-breaker test.
INSERT INTO posts (id, author_id, kind, text, created_at) VALUES
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', 'Building a feed paginator with a generator today.', '2026-08-20T09:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'original', 'Anyone else find async easier once you stop thinking in loops?', '2026-08-20T10:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb003', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'original', 'Shipped the cursor pagination fix. Feels good.', '2026-08-20T11:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb004', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'original', 'Reading about the ASGI spec this morning.', '2026-08-19T12:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb005', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'original', 'Coffee first, code second.', '2026-08-13T23:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb006', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'original', 'Finally understand why lru_cache does not do TTL by itself.', '2026-08-13T23:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb007', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', 'Refactoring the repository layer today.', '2026-08-19T15:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb008', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'original', 'Small wins: tests are green again.', '2026-08-19T16:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb009', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'original', 'Trying out a new folder structure for the backend.', '2026-08-19T17:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb010', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'original', 'Debugging a race condition, send help.', '2026-08-19T18:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb011', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'original', 'Deployed to staging, crossing fingers.', '2026-08-18T09:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb012', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'original', 'Learned something new about Pydantic validators.', '2026-08-18T10:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb013', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', 'Weekend project: a tiny ASGI server from scratch.', '2026-08-18T11:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb014', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'original', 'Cursor-based pagination is more interesting than I expected.', '2026-08-18T12:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb015', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'original', 'Writing docs is somehow harder than writing code.', '2026-08-18T13:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb016', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'original', 'Today''s lesson: do not cache a coroutine object.', '2026-08-18T14:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb017', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'original', 'Migrations are done, on to seeding.', '2026-08-18T15:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb018', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'original', 'Trying to keep PRs small this week.', '2026-08-18T16:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb019', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', 'Async does not mean parallel, and that finally clicked.', '2026-08-18T17:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb020', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'original', 'New teammate started today, excited to onboard them.', '2026-08-18T18:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb021', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'original', 'Rewrote the error envelope for the third time.', '2026-08-17T09:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb022', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'original', 'Every bug is a lesson in disguise, eventually.', '2026-08-17T10:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb023', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'original', 'Testing the like/unlike rollback behavior.', '2026-08-17T11:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb024', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'original', 'Spent the morning reading the ASGI HTTP spec.', '2026-08-17T12:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb025', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'original', 'Pagination tie-breaks matter more than you would think.', '2026-08-17T13:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb026', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'original', 'Config validation at startup saved me twice this week.', '2026-08-17T14:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb027', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'original', 'Dependency injection finally clicked for me today.', '2026-08-17T15:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb028', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'original', 'Wrote my first repository interface using Protocol.', '2026-08-17T16:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb029', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'original', 'Two posts with the same timestamp, on purpose, for testing.', '2026-08-17T17:00:00.000Z'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb030', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'original', 'Last original in the fixture set. That is a wrap.', '2026-08-17T18:00:00.000Z')
ON CONFLICT (id) DO NOTHING;

-- ---------------- replies (12) ----------------
INSERT INTO posts (id, author_id, kind, text, created_at, reply_to_id) VALUES
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb031', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'reply', 'wait does that mean the whole feed never sits in memory at once?', '2026-08-21T10:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb032', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'reply', 'this is exactly what I needed today, thank you', '2026-08-21T11:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb033', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'reply', 'how does this compare to the older approach though?', '2026-08-21T12:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb003'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb034', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'reply', 'following this thread, need this for my own project too', '2026-08-21T13:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb004'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb035', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'reply', 'genuinely did not know this was possible until now', '2026-08-21T14:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb005'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb036', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'reply', 'same energy honestly', '2026-08-21T15:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb006'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb037', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'reply', 'bookmarking this for later', '2026-08-21T16:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb007'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb038', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'reply', 'can you do a follow-up on how this scales?', '2026-08-21T17:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb008'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb039', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'reply', 'this explanation finally made it click for me', '2026-08-21T18:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb009'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb040', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'reply', 'I hit the exact same bug last week', '2026-08-21T19:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb010'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb041', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'reply', 'solid breakdown, appreciated', '2026-08-21T20:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb011'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb042', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'reply', 'curious how you would test this', '2026-08-21T21:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb012')
ON CONFLICT (id) DO NOTHING;

-- ---------------- reposts (4) — note the two on the SAME original, DIFFERENT users ----------------
INSERT INTO posts (id, author_id, kind, text, created_at, repost_of_id) VALUES
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb043', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'repost', NULL, '2026-08-22T10:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb044', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'repost', NULL, '2026-08-22T11:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb003'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb045', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'repost', NULL, '2026-08-22T12:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb046', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'repost', NULL, '2026-08-22T13:00:00.000Z', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb007')
ON CONFLICT (id) DO NOTHING;

-- ---------------- media (10) — 5 originals get 2 images each ----------------
INSERT INTO post_media (id, post_id, alt_text, width, height, position, small_url, large_url) VALUES
('cccccccc-cccc-4ccc-8ccc-ccccccccc001', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001', 'Image 1 attached to post 001', 1200, 800, 0, '/fixtures/media-1-480.jpg', '/fixtures/media-1-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc002', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001', 'Image 2 attached to post 001', 1200, 800, 1, '/fixtures/media-2-480.jpg', '/fixtures/media-2-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc003', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002', 'Image 1 attached to post 002', 1200, 800, 0, '/fixtures/media-3-480.jpg', '/fixtures/media-3-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc004', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002', 'Image 2 attached to post 002', 1200, 800, 1, '/fixtures/media-4-480.jpg', '/fixtures/media-4-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc005', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb003', 'Image 1 attached to post 003', 1200, 800, 0, '/fixtures/media-5-480.jpg', '/fixtures/media-5-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc006', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb003', 'Image 2 attached to post 003', 1200, 800, 1, '/fixtures/media-6-480.jpg', '/fixtures/media-6-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc007', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb004', 'Image 1 attached to post 004', 1200, 800, 0, '/fixtures/media-7-480.jpg', '/fixtures/media-7-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc008', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb004', 'Image 2 attached to post 004', 1200, 800, 1, '/fixtures/media-8-480.jpg', '/fixtures/media-8-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc009', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb008', 'Image 1 attached to post 008', 1200, 800, 0, '/fixtures/media-9-480.jpg', '/fixtures/media-9-1200.jpg'),
('cccccccc-cccc-4ccc-8ccc-ccccccccc010', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb008', 'Image 2 attached to post 008', 1200, 800, 1, '/fixtures/media-10-480.jpg', '/fixtures/media-10-1200.jpg')
ON CONFLICT (id) DO NOTHING;

-- ---------------- likes (15) — post 001 liked (twice), post 011 has ZERO likes ----------------
INSERT INTO likes (user_id, post_id) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb003'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb004'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb005'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb006'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb007'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb008'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb009'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb010'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb031'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb032'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb033')
ON CONFLICT (user_id, post_id) DO NOTHING;

-- ---------------- follows (8) — directional, no self-follow, no duplicates ----------------
INSERT INTO follows (follower_id, following_id) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4')
ON CONFLICT (follower_id, following_id) DO NOTHING;

COMMIT;