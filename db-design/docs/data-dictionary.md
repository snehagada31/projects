# Data Dictionary — Social Feed

Type choices explained once, up front, instead of repeated per row:

- **UUID for every public ID** — per the brief: public IDs are UUID
  strings, not auto-incrementing integers. This avoids leaking "how many
  rows exist" (an integer ID like `47` tells an attacker roughly how
  many posts exist total) and means IDs never collide across tables or
  need central coordination.
- **`timestamptz(3)`** — timezone-aware timestamp, millisecond
  precision. The brief requires millisecond precision specifically so
  the cursor's `(created_at, id)` tuple round-trips exactly between the
  database and the API — a timestamp truncated to whole seconds could
  make two genuinely-different rows look identical to the cursor logic.
- **`text` over `varchar(n)`** — PostgreSQL's `text` has no meaningful
  performance difference from `varchar(n)`, and uses no storage penalty;
  length limits (like the 1–280 code point rule) are enforced with a
  `CHECK` constraint instead, which is more flexible than baking the
  limit into the column type.

## `users`

| Column | Meaning | Type | Required | Default | Key/Constraint | Example |
|---|---|---|---|---|---|---|
| `id` | Public user identifier | `uuid` | yes | `gen_random_uuid()` | PK | `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1` |
| `handle` | Unique lowercase username | `text` | yes | — | UNIQUE, `CHECK (handle = lower(handle))` | `asha` |
| `display_name` | Shown name | `text` | yes | — | — | `Asha` |
| `bio` | Optional profile text | `text` | no | `NULL` | — | `Building things, one commit at a time.` |
| `avatar_small_url` | Small avatar variant | `text` | yes | — | — | `/fixtures/asha-48.jpg` |
| `avatar_large_url` | Large avatar variant | `text` | yes | — | — | `/fixtures/asha-96.jpg` |
| `created_at` | Account creation time | `timestamptz(3)` | yes | `now()` | — | `2026-01-01T00:00:00.000Z` |

## `posts`

| Column | Meaning | Type | Required | Default | Key/Constraint | Example |
|---|---|---|---|---|---|---|
| `id` | Public post identifier | `uuid` | yes | `gen_random_uuid()` | PK | `bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001` |
| `author_id` | Who wrote/reposted this | `uuid` | yes | — | FK → `users.id` | — |
| `kind` | Discriminator: what TYPE of post this is | `text` | yes | — | `CHECK (kind IN ('original','reply','repost'))` | `original` |
| `text` | Post body | `text` | conditional | `NULL` | `NULL` for repost; 1–280 code points for original/reply (see `decisions.md`) | `My first database-backed post` |
| `created_at` | When posted | `timestamptz(3)` | yes | `now()` | — | `2026-09-01T10:00:00.000Z` |
| `reply_to_id` | The original this replies to | `uuid` | conditional | `NULL` | FK → `posts.id`; non-null only when `kind='reply'` | `NULL` for an original |
| `repost_of_id` | The original this reposts | `uuid` | conditional | `NULL` | FK → `posts.id`; non-null only when `kind='repost'` | `NULL` for an original |

**Why one table with a `kind` column, not three separate tables (`originals`, `replies`, `reposts`)?** See `decisions.md` — this is the specific "alternative physical model" tradeoff the mentor checkpoint asks about.

## `post_media`

| Column | Meaning | Type | Required | Default | Key/Constraint | Example |
|---|---|---|---|---|---|---|
| `id` | Public media identifier | `uuid` | yes | `gen_random_uuid()` | PK | `cccccccc-cccc-4ccc-8ccc-ccccccccc001` |
| `post_id` | Which post this belongs to | `uuid` | yes | — | FK → `posts.id` | — |
| `alt_text` | Accessibility description | `text` | yes | — | `CHECK (length(trim(alt_text)) > 0)` | `A desk with a laptop` |
| `width` | Image width in pixels | `int` | yes | — | `CHECK (width > 0)` | `1200` |
| `height` | Image height in pixels | `int` | yes | — | `CHECK (height > 0)` | `800` |
| `position` | Display order within the post | `int` | yes | — | `CHECK (position BETWEEN 0 AND 3)`, UNIQUE with `post_id` | `0` |
| `small_url` | Small variant URL | `text` | yes | — | `CHECK (length(small_url) > 0)` | `/fixtures/desk-480.jpg` |
| `large_url` | Large variant URL | `text` | yes | — | `CHECK (length(large_url) > 0)` | `/fixtures/desk-1200.jpg` |
| `created_at` | When this media row was created | `timestamptz(3)` | yes | `now()` | — | `2026-09-01T10:00:00.000Z` |

## `likes`

| Column | Meaning | Type | Required | Default | Key/Constraint | Example |
|---|---|---|---|---|---|---|
| `user_id` | Who liked | `uuid` | yes | — | PK (composite), FK → `users.id` | — |
| `post_id` | What was liked | `uuid` | yes | — | PK (composite), FK → `posts.id` | — |
| `created_at` | When liked | `timestamptz(3)` | yes | `now()` | — | `2026-09-01T10:05:00.000Z` |

**No surrogate `id` column here.** The composite primary key
`(user_id, post_id)` already uniquely identifies a like — there's no
scenario in this scenario where something else needs to reference "this
specific like row" independently. Adding a surrogate ID would be an
unused extra column. (Contrast with `posts`, where a surrogate `id` is
genuinely needed — other rows reference a specific post via
`reply_to_id`/`repost_of_id`.)

## `follows`

| Column | Meaning | Type | Required | Default | Key/Constraint | Example |
|---|---|---|---|---|---|---|
| `follower_id` | The one doing the following | `uuid` | yes | — | PK (composite), FK → `users.id` | — |
| `following_id` | The one being followed | `uuid` | yes | — | PK (composite), FK → `users.id` | — |
| `created_at` | When the follow happened | `timestamptz(3)` | yes | `now()` | — | `2026-09-01T10:10:00.000Z` |

Same reasoning as `likes` — no surrogate ID needed, composite PK
`(follower_id, following_id)` is sufficient and prevents duplicate
follow pairs automatically (see `decisions.md`).
