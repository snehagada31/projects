-- Ten SQL use cases required by the PRD. Each is parameterized (shown
-- with $1, $2... placeholders as PostgreSQL prepared statements would
-- use them), with a literal example substituted below each for direct
-- testing against the seed data.

-- ============================================================
-- 1. HOME FEED — originals + author, newest first, limit+1, page 1 and continuation
-- Params: $1 = limit, $2 = cursor created_at (NULL for page 1), $3 = cursor id
-- ============================================================
-- Page 1 (no cursor):
SELECT p.id, p.text, p.created_at, u.id AS author_id, u.handle, u.display_name
FROM posts p
JOIN users u ON u.id = p.author_id
WHERE p.kind = 'original'
ORDER BY p.created_at DESC, p.id DESC
LIMIT 11;  -- limit+1, to derive hasMore without a separate count query

-- Continuation (using the 10th row's tuple as the cursor):
-- SELECT p.id, p.text, p.created_at, u.id AS author_id, u.handle, u.display_name
-- FROM posts p JOIN users u ON u.id = p.author_id
-- WHERE p.kind = 'original' AND (p.created_at, p.id) < ($2, $3)
-- ORDER BY p.created_at DESC, p.id DESC LIMIT $1 + 1;


-- ============================================================
-- 2. POST DETAIL — one post, author, target reference, accurate counts
-- Params: $1 = post id
-- ============================================================
SELECT
    p.id, p.kind, p.text, p.created_at, p.reply_to_id, p.repost_of_id,
    u.id AS author_id, u.handle, u.display_name,
    (SELECT count(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
    (SELECT count(*) FROM posts r WHERE r.reply_to_id = p.id) AS reply_count
FROM posts p
JOIN users u ON u.id = p.author_id
WHERE p.id = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001';


-- ============================================================
-- 3. DIRECT REPLIES — replies to one original, stable order + continuation
-- Params: $1 = original post id, $2 = limit
-- ============================================================
SELECT p.id, p.text, p.created_at, u.handle, u.display_name
FROM posts p
JOIN users u ON u.id = p.author_id
WHERE p.reply_to_id = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001'
ORDER BY p.created_at DESC, p.id DESC
LIMIT 11;


-- ============================================================
-- 4. PROFILE MEDIA — images for one user's originals, stable cursor
-- Params: $1 = user id, $2 = limit
-- ============================================================
SELECT pm.id, pm.post_id, pm.created_at, pm.position, pm.alt_text,
       pm.width, pm.height, pm.small_url, pm.large_url
FROM post_media pm
JOIN posts p ON p.id = pm.post_id
WHERE p.author_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
ORDER BY pm.created_at DESC, pm.id DESC
LIMIT 11;


-- ============================================================
-- 5. PROFILE STATISTICS — originals/followers/following counts, incl. zero
-- Params: $1 = user id
-- Uses LEFT JOIN + subqueries, not INNER JOIN, so a user with zero of
-- something still gets a row with 0, not no row at all.
-- ============================================================
SELECT
    u.id, u.handle, u.display_name,
    (SELECT count(*) FROM posts p WHERE p.author_id = u.id AND p.kind = 'original') AS post_count,
    (SELECT count(*) FROM follows f WHERE f.following_id = u.id) AS follower_count,
    (SELECT count(*) FROM follows f WHERE f.follower_id = u.id) AS following_count
FROM users u
WHERE u.id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1';


-- ============================================================
-- 6. LIKE TOTALS — counts for a BATCH of post IDs, including zero-liked
-- Params: $1 = array of post ids
-- Why a batch query, not one-per-post: avoids N+1 queries when rendering
-- a whole feed page. LEFT JOIN keeps zero-liked posts in the result.
-- ============================================================
SELECT p.id AS post_id, count(l.post_id) AS like_count
FROM unnest(ARRAY[
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001',
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002',
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb011'  -- deliberately zero-liked
]::uuid[]) AS p(id)
LEFT JOIN likes l ON l.post_id = p.id
GROUP BY p.id
ORDER BY p.id;


-- ============================================================
-- 7. VIEWER STATE — which of a batch of posts the demo user liked, in ONE query
-- Params: $1 = demo user id, $2 = array of post ids
-- The trick: LEFT JOIN + IS NOT NULL, not a separate query per post.
-- ============================================================
SELECT p.id AS post_id, (l.user_id IS NOT NULL) AS liked_by_viewer
FROM unnest(ARRAY[
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001',
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb002',
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb011'
]::uuid[]) AS p(id)
LEFT JOIN likes l ON l.post_id = p.id AND l.user_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
ORDER BY p.id;


-- ============================================================
-- 8. FOLLOWING-FEED EXERCISE — originals by followed authors only
-- Params: $1 = viewer user id, $2 = limit
-- Difference from the core /feed endpoint: core feed is ALL originals
-- from EVERY user, unfiltered. This query adds a JOIN through `follows`
-- to restrict to just the authors the viewer follows — a genuinely
-- different, smaller result set, not just a filtered view of the same
-- data. DISTINCT is not needed here (unlike a naive multi-table feed
-- join might need) because each post has exactly one author, so this
-- join can never multiply rows.
-- ============================================================
SELECT p.id, p.text, p.created_at, u.handle
FROM posts p
JOIN users u ON u.id = p.author_id
JOIN follows f ON f.following_id = p.author_id
WHERE p.kind = 'original' AND f.follower_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
ORDER BY p.created_at DESC, p.id DESC
LIMIT 11;


-- ============================================================
-- 9. SEARCH — case-insensitive literal substring, escaped %/_, no-match case
-- Params: $1 = search text
-- ILIKE with escaped wildcards means a literal "%" or "_" typed by the
-- user is treated as a plain character, not a SQL wildcard.
-- ============================================================
SELECT p.id, p.text, p.created_at, u.handle
FROM posts p
JOIN users u ON u.id = p.author_id
WHERE p.kind = 'original'
  AND p.text ILIKE '%' || replace(replace('cursor', '%', '\%'), '_', '\_') || '%' ESCAPE '\'
ORDER BY p.created_at DESC, p.id DESC
LIMIT 11;

-- No-match example (should return zero rows, not an error):
SELECT p.id FROM posts p
WHERE p.kind = 'original'
  AND p.text ILIKE '%' || replace(replace('zzzznonexistentzzzz', '%', '\%'), '_', '\_') || '%' ESCAPE '\';


-- ============================================================
-- 10. REPOST LOOKUP — a user's reposts + each original's author, no duplicated text
-- Params: $1 = user id
-- The repost row itself has text=NULL (per kind_shape_check) — the
-- ORIGINAL's text is joined in fresh each time, never copied onto the
-- repost row itself. That's the "no duplicated original text" the
-- brief asks about.
-- ============================================================
SELECT
    repost.id AS repost_id, repost.created_at AS reposted_at,
    original.id AS original_id, original.text AS original_text,
    orig_author.handle AS original_author_handle
FROM posts repost
JOIN posts original ON original.id = repost.repost_of_id
JOIN users orig_author ON orig_author.id = original.author_id
WHERE repost.kind = 'repost' AND repost.author_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2'
ORDER BY repost.created_at DESC;