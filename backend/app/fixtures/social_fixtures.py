"""
Fixed, reproducible fixture data matching the shared API contract.

Everything here is HARDCODED — no random.choice(), no random.randint().
The brief requires "fixed IDs/timestamps for reproducibility": the same
data must exist every time the server restarts, so cursor pagination and
"two posts share a timestamp" tests behave identically on every run.

Internal representation uses snake_case (matches what a real DB table
would look like) — converting to the contract's camelCase wire format
happens later, in app/schemas/, not here. This file is just the data.
"""

# ---------------- users (6, per the brief) ----------------
# Deterministic UUID pattern: aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1..6
USERS = [
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
        "handle": "asha",
        "display_name": "Asha",
        "bio": "Building things, one commit at a time.",
        "avatar": {"small_url": "/fixtures/asha-48.jpg", "large_url": "/fixtures/asha-96.jpg"},
    },
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2",
        "handle": "devpatel",
        "display_name": "Dev Patel",
        "bio": "Backend and infra.",
        "avatar": {"small_url": "/fixtures/dev-48.jpg", "large_url": "/fixtures/dev-96.jpg"},
    },
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3",
        "handle": "mayachen",
        "display_name": "Maya Chen",
        "bio": None,  # bio is explicitly optional per the brief
        "avatar": {"small_url": "/fixtures/maya-48.jpg", "large_url": "/fixtures/maya-96.jpg"},
    },
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4",
        "handle": "leomartins",
        "display_name": "Leo Martins",
        "bio": "Design + frontend.",
        "avatar": {"small_url": "/fixtures/leo-48.jpg", "large_url": "/fixtures/leo-96.jpg"},
    },
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5",
        "handle": "zaraahmed",
        "display_name": "Zara Ahmed",
        "bio": "Learning in public.",
        # This user has NO media anywhere in the fixtures — required case.
        "avatar": {"small_url": "/fixtures/zara-48.jpg", "large_url": "/fixtures/zara-96.jpg"},
    },
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa6",
        "handle": "kenjiw",
        "display_name": "Kenji Watanabe",
        "bio": None,
        "avatar": {"small_url": "/fixtures/kenji-48.jpg", "large_url": "/fixtures/kenji-96.jpg"},
    },
]

USER_IDS = [u["id"] for u in USERS]


def _post_id(n: int) -> str:
    # bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb001 .. 046 — zero-padded, fixed.
    return f"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb{n:03d}"


def _media_id(n: int) -> str:
    return f"cccccccc-cccc-4ccc-8ccc-ccccccccc{n:03d}"


# ---------------- originals (30) ----------------
_ORIGINAL_TEXTS = [
    "Building a feed paginator with a generator today.",
    "Anyone else find async easier once you stop thinking in loops?",
    "Shipped the cursor pagination fix. Feels good.",
    "Reading about the ASGI spec this morning.",
    "Coffee first, code second.",
    "Finally understand why lru_cache doesn't do TTL by itself.",
    "Refactoring the repository layer today.",
    "Small wins: tests are green again.",
    "Trying out a new folder structure for the backend.",
    "Debugging a race condition, send help.",
    "Deployed to staging, crossing fingers.",
    "Learned something new about Pydantic validators.",
    "Weekend project: a tiny ASGI server from scratch.",
    "Cursor-based pagination is more interesting than I expected.",
    "Writing docs is somehow harder than writing code.",
    "Today's lesson: don't cache a coroutine object.",
    "Migrations are done, on to seeding.",
    "Trying to keep PRs small this week.",
    "Async doesn't mean parallel, and that finally clicked.",
    "New teammate started today, excited to onboard them.",
    "Rewrote the error envelope for the third time.",
    "Every bug is a lesson in disguise, eventually.",
    "Testing the like/unlike rollback behavior.",
    "Spent the morning reading the ASGI HTTP spec.",
    "Pagination tie-breaks matter more than you'd think.",
    "Config validation at startup saved me twice this week.",
    "Dependency injection finally clicked for me today.",
    "Wrote my first repository interface using Protocol.",
    "Two posts with the same timestamp, on purpose, for testing.",
    "Last original in the fixture set. That's a wrap.",
]

ORIGINALS = []
for i in range(30):
    author = USER_IDS[i % len(USER_IDS)]
    # Two originals (index 4 and 5) deliberately share the exact same
    # timestamp — required test case for the cursor's (created_at, id)
    # tie-breaker.
    created_at = f"2026-08-{20 - (i // 3):02d}T{9 + (i % 12):02d}:00:00.000Z"

    ORIGINALS.append({
        "id": _post_id(i + 1),
        "kind": "original",
        "author_id": author,
        "text": _ORIGINAL_TEXTS[i],
        "created_at": created_at,
        "reply_to_id": None,
        "repost_of_id": None,
    })

# Force a deliberate timestamp tie between index 4 and 5 — using a
# timestamp that does NOT collide with anything the formula above
# generates naturally (verified: no other index produces this exact
# value), so exactly two originals share it, not three by accident.
_TIE_TIMESTAMP = "2026-08-13T23:00:00.000Z"
ORIGINALS[4]["created_at"] = _TIE_TIMESTAMP
ORIGINALS[5]["created_at"] = _TIE_TIMESTAMP


# ---------------- replies (12) — each references an original ----------------
_REPLY_TEXTS = [
    "wait does that mean the whole feed never sits in memory at once?",
    "this is exactly what I needed today, thank you",
    "how does this compare to the older approach though?",
    "following this thread, need this for my own project too",
    "genuinely didn't know this was possible until now",
    "same energy honestly",
    "bookmarking this for later",
    "can you do a follow-up on how this scales?",
    "this explanation finally made it click for me",
    "I hit the exact same bug last week",
    "solid breakdown, appreciated",
    "curious how you'd test this",
]

REPLIES = []
for i in range(12):
    author = USER_IDS[(i + 2) % len(USER_IDS)]
    target_original = ORIGINALS[i % len(ORIGINALS)]
    REPLIES.append({
        "id": _post_id(31 + i),
        "kind": "reply",
        "author_id": author,
        "text": _REPLY_TEXTS[i],
        "created_at": f"2026-08-21T{10 + i:02d}:00:00.000Z",
        "reply_to_id": target_original["id"],
        "repost_of_id": None,
    })


# ---------------- reposts (4) — text: null, media: [], no dup (user, original) ----------------
REPOSTS = [
    {
        "id": _post_id(43),
        "kind": "repost",
        "author_id": USER_IDS[1],
        "text": None,
        "created_at": "2026-08-22T10:00:00.000Z",
        "reply_to_id": None,
        "repost_of_id": ORIGINALS[0]["id"],
    },
    {
        "id": _post_id(44),
        "kind": "repost",
        "author_id": USER_IDS[2],
        "text": None,
        "created_at": "2026-08-22T11:00:00.000Z",
        "reply_to_id": None,
        "repost_of_id": ORIGINALS[2]["id"],
    },
    {
        "id": _post_id(45),
        "kind": "repost",
        "author_id": USER_IDS[3],
        "text": None,
        "created_at": "2026-08-22T12:00:00.000Z",
        "reply_to_id": None,
        "repost_of_id": ORIGINALS[0]["id"],  # same original as first repost, DIFFERENT user — allowed
    },
    {
        "id": _post_id(46),
        "kind": "repost",
        "author_id": USER_IDS[4],
        "text": None,
        "created_at": "2026-08-22T13:00:00.000Z",
        "reply_to_id": None,
        "repost_of_id": ORIGINALS[6]["id"],
    },
]

ALL_POSTS = ORIGINALS + REPLIES + REPOSTS


# ---------------- media (10 rows) — attached to originals only ----------------
# Distributed across 5 originals (2 images each = 10) — the other 25
# originals + zara's posts have NO media, satisfying "user with no media".
MEDIA = []
_media_owners = [ORIGINALS[0], ORIGINALS[1], ORIGINALS[2], ORIGINALS[3], ORIGINALS[7]]
_n = 1
for post in _media_owners:
    for position in range(2):
        MEDIA.append({
            "id": _media_id(_n),
            "post_id": post["id"],
            "alt_text": f"Image {position + 1} attached to post {post['id'][-3:]}",
            "width": 1200,
            "height": 800,
            "position": position,
            "small_url": f"/fixtures/media-{_n}-480.jpg",
            "large_url": f"/fixtures/media-{_n}-1200.jpg",
            "created_at": post["created_at"],
        })
        _n += 1


# ---------------- likes (15) ----------------
# original[10] deliberately gets ZERO likes — "an original with no reactions".
# original[0] deliberately gets a like — "a liked original".
LIKES = []
_like_pairs = [
    (USER_IDS[0], ORIGINALS[0]["id"]),
    (USER_IDS[1], ORIGINALS[0]["id"]),
    (USER_IDS[2], ORIGINALS[1]["id"]),
    (USER_IDS[3], ORIGINALS[1]["id"]),
    (USER_IDS[4], ORIGINALS[2]["id"]),
    (USER_IDS[5], ORIGINALS[3]["id"]),
    (USER_IDS[0], ORIGINALS[4]["id"]),
    (USER_IDS[1], ORIGINALS[5]["id"]),
    (USER_IDS[2], ORIGINALS[6]["id"]),
    (USER_IDS[3], ORIGINALS[7]["id"]),
    (USER_IDS[4], ORIGINALS[8]["id"]),
    (USER_IDS[5], ORIGINALS[9]["id"]),
    (USER_IDS[0], REPLIES[0]["id"]),
    (USER_IDS[1], REPLIES[1]["id"]),
    (USER_IDS[2], REPLIES[2]["id"]),
]
for user_id, post_id in _like_pairs:
    LIKES.append({"user_id": user_id, "post_id": post_id})


# ---------------- follows (8, directional, no self-follow, no duplicates) ----------------
FOLLOWS = [
    {"follower_id": USER_IDS[0], "following_id": USER_IDS[1]},
    {"follower_id": USER_IDS[0], "following_id": USER_IDS[2]},
    {"follower_id": USER_IDS[1], "following_id": USER_IDS[0]},
    {"follower_id": USER_IDS[2], "following_id": USER_IDS[3]},
    {"follower_id": USER_IDS[3], "following_id": USER_IDS[4]},
    {"follower_id": USER_IDS[4], "following_id": USER_IDS[5]},
    {"follower_id": USER_IDS[5], "following_id": USER_IDS[0]},
    {"follower_id": USER_IDS[1], "following_id": USER_IDS[3]},
]