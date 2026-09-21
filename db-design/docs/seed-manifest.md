# Seed Manifest

Real numbers, queried directly against the seeded database — not
computed by hand. Re-running the counts below on your own seeded
instance should reproduce these exactly, since every ID/timestamp in
`seed.sql` is fixed.

## Entity counts (minimums required by the brief, all met exactly)

| Entity | Count |
|---|---|
| users | 6 |
| originals | 30 |
| replies | 12 |
| reposts | 4 |
| media | 10 |
| likes | 15 |
| follows | 8 |

Verify with:
```sql
SELECT kind, count(*) FROM posts GROUP BY kind;
SELECT count(*) FROM users;
SELECT count(*) FROM post_media;
SELECT count(*) FROM likes;
SELECT count(*) FROM follows;
```

## Sample IDs to use when testing/demoing

- User: `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1` (handle: `asha`)
- Original with likes and a reply: `bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001`
- Original with ZERO likes: `bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb011`
- A repost: `bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb043` (reposts `...001`)
- Media-carrying original: `bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001` (2 images)
- User with NO media anywhere: `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5` (zaraahmed)

## Verified derived counts

Confirmed by direct query against the seeded database (not estimated):

| Metric | Value |
|---|---|
| User `...aaa1` (asha) following count | 2 |
| User `...aaa1` (asha) follower count | 2 |
| Post `...001` like count | 2 |
| Post `...001` direct reply count | 1 |

## The deliberate tie

Two originals share the exact same `created_at`:
`bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb005` and
`bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb006`, both at
`2026-08-13T23:00:00.000Z`. Verified:
```sql
SELECT id FROM posts WHERE created_at = '2026-08-13T23:00:00.000Z' AND kind='original';
-- returns exactly 2 rows: ...005 and ...006
```

## Idempotency, verified

Running `seed.sql` a second time against an already-seeded database
inserts **zero** additional rows (`INSERT 0 0` for every table) due to
`ON CONFLICT (...) DO NOTHING` on every insert — confirmed by running
it twice and checking `SELECT count(*) FROM posts` stayed at 46 both
times.