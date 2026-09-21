-- Social Feed — Stage B database schema
-- Matches docs/erd.md, docs/data-dictionary.md, docs/constraints.md exactly.

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for gen_random_uuid()

-- ============================================================
-- users
-- ============================================================
CREATE TABLE users (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle             TEXT NOT NULL UNIQUE,
    display_name       TEXT NOT NULL,
    bio                TEXT,
    avatar_small_url   TEXT NOT NULL,
    avatar_large_url   TEXT NOT NULL,
    created_at         TIMESTAMPTZ(3) NOT NULL DEFAULT now(),

    CONSTRAINT handle_is_lowercase CHECK (handle = lower(handle)),
    CONSTRAINT handle_not_empty CHECK (length(trim(handle)) > 0)
);

-- ============================================================
-- posts (originals, replies, reposts — one table, kind discriminator)
-- ============================================================
CREATE TABLE posts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    kind           TEXT NOT NULL,
    text           TEXT,
    created_at     TIMESTAMPTZ(3) NOT NULL DEFAULT now(),
    reply_to_id    UUID REFERENCES posts(id) ON DELETE RESTRICT,
    repost_of_id   UUID REFERENCES posts(id) ON DELETE RESTRICT,

    CONSTRAINT kind_is_valid CHECK (kind IN ('original', 'reply', 'repost')),

    -- ties kind to which columns must/must not be null — single-row check
    CONSTRAINT kind_shape_check CHECK (
        (kind = 'original' AND text IS NOT NULL AND reply_to_id IS NULL AND repost_of_id IS NULL)
        OR (kind = 'reply' AND text IS NOT NULL AND reply_to_id IS NOT NULL AND repost_of_id IS NULL)
        OR (kind = 'repost' AND text IS NULL AND reply_to_id IS NULL AND repost_of_id IS NOT NULL)
    ),

    CONSTRAINT text_length_check CHECK (
        text IS NULL OR char_length(text) BETWEEN 1 AND 280
    )
);

-- no user can repost the same original twice
CREATE UNIQUE INDEX repost_uniqueness
    ON posts (author_id, repost_of_id)
    WHERE kind = 'repost';

-- ============================================================
-- post_media
-- ============================================================
CREATE TABLE post_media (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id      UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    alt_text     TEXT NOT NULL,
    width        INT NOT NULL,
    height       INT NOT NULL,
    position     INT NOT NULL,
    small_url    TEXT NOT NULL,
    large_url    TEXT NOT NULL,
    created_at   TIMESTAMPTZ(3) NOT NULL DEFAULT now(),

    CONSTRAINT width_positive CHECK (width > 0),
    CONSTRAINT height_positive CHECK (height > 0),
    CONSTRAINT alt_text_present CHECK (length(trim(alt_text)) > 0),
    CONSTRAINT small_url_present CHECK (length(small_url) > 0),
    CONSTRAINT large_url_present CHECK (length(large_url) > 0),
    CONSTRAINT position_in_range CHECK (position BETWEEN 0 AND 3),

    CONSTRAINT unique_position_per_post UNIQUE (post_id, position)
);

-- ============================================================
-- likes (composite PK — no surrogate id, see decisions.md)
-- ============================================================
CREATE TABLE likes (
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id      UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ(3) NOT NULL DEFAULT now(),

    PRIMARY KEY (user_id, post_id)
);

-- ============================================================
-- follows (composite PK, directional, no self-follow)
-- ============================================================
CREATE TABLE follows (
    follower_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at     TIMESTAMPTZ(3) NOT NULL DEFAULT now(),

    PRIMARY KEY (follower_id, following_id),
    CONSTRAINT no_self_follow CHECK (follower_id <> following_id)
);

-- ============================================================
-- Triggers — for the two rules a plain CHECK cannot express
-- (see docs/constraints.md for why each one specifically needs this)
-- ============================================================

-- reply_to_id / repost_of_id must point at an ORIGINAL, never a reply/repost
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

-- media: only on originals, max 4 per post
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

-- ============================================================
-- Indexes for the actual access paths (Deliverable 5 — added here
-- since schema creation is the natural place for them)
-- ============================================================

-- feed ordering: originals, reverse-chronological, with the tie-breaker
CREATE INDEX idx_posts_feed_order
    ON posts (created_at DESC, id DESC)
    WHERE kind = 'original';

-- replies to one original, same ordering
CREATE INDEX idx_posts_reply_lookup
    ON posts (reply_to_id, created_at DESC, id DESC)
    WHERE kind = 'reply';

-- profile media: newest-media-first per user's posts
CREATE INDEX idx_media_by_post
    ON post_media (post_id, created_at DESC, id DESC);

-- follow lookups both directions
CREATE INDEX idx_follows_follower ON follows (follower_id);
CREATE INDEX idx_follows_following ON follows (following_id);

-- Note: PRIMARY KEY and UNIQUE constraints above (users.handle,
-- likes composite PK, follows composite PK, post_media unique position,
-- posts.id, users.id) already create their own indexes automatically —
-- not duplicated here.