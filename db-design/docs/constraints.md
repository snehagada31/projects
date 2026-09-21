# Constraints and Normalization — Social Feed

Every product rule from the brief, mapped to its actual enforcement
mechanism. Three categories, used deliberately, not interchangeably:

- **DB constraint** — `PRIMARY KEY` / `UNIQUE` / `FOREIGN KEY` / `CHECK`
  on a single row or a simple composite. PostgreSQL enforces this
  automatically, always, no matter what inserts the row.
- **Trigger** — for rules that need to look at *other* rows (a plain
  `CHECK` in PostgreSQL cannot query another table). Used sparingly —
  only where a `CHECK` genuinely cannot express the rule.
- **Application-level** — validated in service code before the INSERT
  is even attempted. Used where the rule is about *input shape*
  (trimming whitespace) rather than a *relational* invariant.

## The enforcement table

| Rule | Mechanism | Where / How |
|---|---|---|
| Unique normalized user handle | DB constraint | `UNIQUE(handle)` + `CHECK (handle = lower(handle))` |
| Every author/like/media/follow/reference points to an existing row | DB constraint | `FOREIGN KEY` on every reference column |
| One user can like a given post once | DB constraint | Composite `PRIMARY KEY (user_id, post_id)` on `likes` |
| No duplicate follow pair or self-follow | DB constraint | Composite `PRIMARY KEY (follower_id, following_id)` + `CHECK (follower_id <> following_id)` |
| Original/reply text trimmed, 1–280 code points | App-level (trim) + DB constraint (length) | App trims before INSERT; `CHECK` backstops the length rule even if app validation is bypassed |
| Repost has no new text, only a repost target | DB constraint | One `CHECK` tying `kind` to which columns must be null (below) |
| Reply/repost target must be an original | **Trigger** | `CHECK` can't see another row's `kind` — see `check_reference_kind()` below |
| No user can repost the same original twice | DB constraint | Partial `UNIQUE` index: `(author_id, repost_of_id) WHERE kind='repost'` |
| Media belongs only to an original, max four | **Trigger** | Needs both a cross-table kind check AND a row count — see `check_media_limit()` below |
| Image dimensions positive, nonempty URLs, alt text present | DB constraint | Simple single-row `CHECK`s |
| Each media position unique within a post, 0–3 | DB constraint | `UNIQUE(post_id, position)` + `CHECK (position BETWEEN 0 AND 3)` |
| Like/reply/follower counts are accurate | N/A — never stored | Always `COUNT(*)` at read time (see `decisions.md`'s 3NF section) — there is no counter column to keep in sync, so there's nothing to enforce here |

## The `kind`/text/reference combination check (single-row — plain CHECK works)

```sql
ALTER TABLE posts ADD CONSTRAINT kind_shape_check CHECK (
    (kind = 'original' AND text IS NOT NULL AND reply_to_id IS NULL AND repost_of_id IS NULL)
    OR (kind = 'reply' AND text IS NOT NULL AND reply_to_id IS NOT NULL AND repost_of_id IS NULL)
    OR (kind = 'repost' AND text IS NULL AND reply_to_id IS NULL AND repost_of_id IS NOT NULL)
);
```

This is a plain `CHECK` because everything it looks at lives on the
*same row* — it never needs to query another table.

## Why two rules genuinely need triggers, not just CHECK

**`check_reference_kind()`** — a reply's `reply_to_id` (or a repost's
`repost_of_id`) must point at a post whose `kind = 'original'`. A
foreign key only proves *that row exists* — it says nothing about
*what kind* of row it is. Checking "what kind is the target" requires
looking at a different row than the one being inserted, which plain
`CHECK` cannot do in PostgreSQL.

```sql
CREATE OR REPLACE FUNCTION check_reference_kind() RETURNS TRIGGER AS $$
DECLARE
    target_id UUID;
    target_kind TEXT;
BEGIN
    target_id := COALESCE(NEW.reply_to_id, NEW.repost_of_id);
    IF target_id IS NOT NULL THEN
        SELECT kind INTO target_kind FROM posts WHERE id = target_id;
        IF target_kind IS DISTINCT FROM 'original' THEN
            RAISE EXCEPTION 'reply_to_id/repost_of_id must reference an original post, got kind=%', target_kind;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_reference_kind
    BEFORE INSERT OR UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION check_reference_kind();
```

This is exactly the "reply-to-a-reply is rejected" rule from the brief
— without this trigger, nothing would stop someone from making a reply
whose `reply_to_id` points at *another reply*, since the foreign key
alone is satisfied either way.

**`check_media_limit()`** — a post can have at most 4 media rows, and
only if it's an original. Both parts require looking beyond the single
row being inserted: "only an original" needs to check the parent
post's `kind`; "max four" needs to *count* the sibling rows that
already exist. Neither of those is expressible in a plain `CHECK`.

```sql
CREATE OR REPLACE FUNCTION check_media_limit() RETURNS TRIGGER AS $$
DECLARE
    parent_kind TEXT;
    existing_count INT;
BEGIN
    SELECT kind INTO parent_kind FROM posts WHERE id = NEW.post_id;
    IF parent_kind IS DISTINCT FROM 'original' THEN
        RAISE EXCEPTION 'media can only be attached to an original post, got kind=%', parent_kind;
    END IF;

    SELECT COUNT(*) INTO existing_count FROM post_media WHERE post_id = NEW.post_id;
    IF existing_count >= 4 THEN
        RAISE EXCEPTION 'post % already has the maximum of 4 media rows', NEW.post_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_media_limit
    BEFORE INSERT ON post_media
    FOR EACH ROW EXECUTE FUNCTION check_media_limit();
```

**Why not just a trigger for everything, to be safe?** The PRD warns
against exactly that: "do not invent triggers for every rule just to
increase the schema's size." Every other rule in the table above is
either a single-row fact (a `CHECK` handles it natively, faster, with
less code to maintain) or a genuine key/uniqueness relationship (a
`PRIMARY KEY`/`UNIQUE` constraint handles it — and is also how
PostgreSQL builds an index for free, which a trigger wouldn't give
you). Triggers are reserved for the two cases above, where the rule
*structurally cannot* be expressed any other way.

## The "trimmed" part of the text rule, specifically

`CHECK` can verify *length* (`char_length(text) BETWEEN 1 AND 280`)
easily — but "trimmed" (no leading/trailing whitespace) is really an
*input normalization* concern, not a relational invariant. The
application trims the text before ever attempting the INSERT; the
database's job here is just the backstop length check, not policing
whitespace formatting. (A `CHECK (text = btrim(text))` could be added
for extra safety, but it's redundant if the application layer already
guarantees this on every write path — documented here as a deliberate
choice, not an oversight.)
