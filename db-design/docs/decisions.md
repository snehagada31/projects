# Design Decisions — Social Feed

## The big one: one `posts` table with a `kind` column, vs. three separate tables

**What I chose:** one `posts` table, with `kind` (`'original' | 'reply' | 'repost'`)
telling you which type a row is.

**The alternative I considered:** three separate tables —
`originals`, `replies`, `reposts` — each with only the columns that
type actually needs.

**Why I rejected the alternative:** the brief explicitly warns "class
inheritance does not require table inheritance" — and the reverse
warning applies just as much here: just because originals/replies/
reposts *feel* like different things doesn't mean they need physically
separate tables. Splitting them creates a real problem for the single
most important query in this whole app: **the home feed**. The feed
needs "all originals, reverse-chronological, paginated by
`(created_at, id)`." With one table, that's a single indexed query
filtered by `kind='original'`. With three tables, replies and reposts
sitting in different tables doesn't matter for the feed query itself
(it only wants originals) — but a reply's detail page needs to show
"which original is this replying to," and that original is sitting in
a *different table* than the reply row referencing it. Every such
lookup becomes a cross-table join instead of a simple self-join on one
table.

**The cost of my choice:** a `reply` row has `text` filled in but
`repost_of_id` always `NULL`; a `repost` row has `text` always `NULL`
but `repost_of_id` filled in. That's a few always-empty columns per
row — cheap, since PostgreSQL doesn't pay a real storage cost for
`NULL` columns. The `CHECK` constraint tying `kind` to which columns
must be null (documented in `data-dictionary.md`, enforced in
`schema.sql`) is what stops that flexibility from becoming a bug —
without it, nothing would stop someone from inserting a "reply" with
`repost_of_id` also filled in, which would be nonsense data.

**One-sentence version for the mentor:** *"Three tables would make the
one query I need most — replies pointing back to their original —
require a cross-table join every time, for a distinction (original vs
reply vs repost) that's really just one column's value, not a
structural difference in what a post fundamentally is."*

## Why `likes` and `follows` have composite primary keys, not surrogate `id` columns

A surrogate ID (`id SERIAL PRIMARY KEY`, unrelated to the actual data)
earns its place when something else in the system needs to reference
*this specific row* independently — e.g., `posts.id` is a surrogate ID
because `reply_to_id` needs to point at one specific post.

`likes` and `follows` have no such need — nothing in this contract ever
says "fetch like #47." The natural composite key
`(user_id, post_id)` for likes, `(follower_id, following_id)` for
follows, already does two jobs at once: it's the primary key **and**
it's what makes "no duplicate like from the same user on the same
post" enforceable for free, as a side effect of the key being a key,
rather than needing a separate `UNIQUE` constraint alongside an unused
surrogate ID.

## 1NF / 2NF / 3NF, in terms of this exact scenario

**1NF (no repeating groups):** a post does NOT have a
`likes: [user1, user2, user3]` column crammed into one field. Likes
live in their own table, one row per like — that's what makes "how
many people liked this" a `COUNT(*)` query instead of parsing a string.

**2NF (no partial dependency on part of a composite key):** in
`post_media`, every non-key column (`alt_text`, `width`, `height`,
`small_url`, `large_url`) depends on the *whole* row's identity
(`id`), not on just `post_id` alone — there's no column here that's
really "about the post" rather than "about this specific media row,"
so there's no 2NF violation hiding.

**3NF (no transitive dependency):** a post does **not** store the
author's `display_name` or `avatar_url` directly on the post row. If
it did, changing your display name would require updating every post
you've ever written — a copy of data that should only exist once, on
`users`. Instead, `posts.author_id` is the only link; the author's
current name/avatar is looked up fresh via the foreign key every time.

**The "no stored count that can silently disagree" rule** is really
this same normalization principle applied to counts specifically:
`like_count` is never a column stored on `posts` — it's always
`COUNT(*) FROM likes WHERE post_id = ...`. A stored counter is exactly
the kind of "copied, derivable data" 3NF warns against — it can drift
out of sync with the actual `likes` rows (e.g., if a delete fails to
also decrement the counter), whereas counting the real rows can never
be wrong.

## `ON DELETE` policy per foreign key

| Foreign key | Policy | Why |
|---|---|---|
| `posts.author_id → users.id` | `RESTRICT` | User deletion is out of scope per the brief; restricting means you can't accidentally delete a user who has posts without deciding what happens to them first |
| `posts.reply_to_id → posts.id` | `RESTRICT` | Deleting an original that has replies pointing at it would orphan those replies — restrict until an explicit deletion policy is designed |
| `posts.repost_of_id → posts.id` | `RESTRICT` | Same reasoning as replies |
| `post_media.post_id → posts.id` | `CASCADE` | Media has no independent meaning without its post — if a post is ever legitimately deleted, its images should go with it, not become orphaned rows |
| `likes.user_id → users.id`, `likes.post_id → posts.id` | `CASCADE` | A like has no meaning without both the user and the post existing — same reasoning as media |
| `follows.follower_id → users.id`, `follows.following_id → users.id` | `CASCADE` | Same reasoning — a follow relationship is meaningless if either user is gone |

**The pattern:** cascade for rows that are purely *dependent* data
(media, likes, follows — they only exist *because of* a post/user, and
have no standalone meaning), restrict for the core content rows
themselves (users, posts) where deletion needs to be a deliberate,
explicit decision, not an accidental side effect of deleting something
else.
