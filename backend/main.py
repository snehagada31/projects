
"""
Topic 14 — FastAPI backend for the infinite-scroll feed.
Imports and wires together models.py, paginator.py, cache.py.

Run:
    pip install fastapi uvicorn --break-system-packages
    uvicorn main:app --reload

Then: http://127.0.0.1:8000/feed?cursor=0&limit=10
"""

import asyncio
import random
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from models import Post, Like
from paginator import paginate_posts
from cache import cache_feed

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NAMES = [
    "Maya Chen", "Dev Patel", "Alex Rivera", "Priya Nair", "Jordan Lee",
    "Sam Okafor", "Riya Kapoor", "Leo Martins", "Zara Ahmed", "Kenji Watanabe",
]

COMMENT_TEXTS = [
    "wait this actually makes sense now, thanks for breaking it down",
    "I always got confused between these two, good explanation",
    "following this thread, need this for my own project too",
    "isn't this basically what a cursor does in SQL as well?",
    "tried this today and it worked first try lol",
    "can you do a follow up on how this scales with more users?",
    "this is the cleanest explanation I've seen for this",
    "genuinely didn't know this was possible until now",
    "bookmarking this for later, solid breakdown",
    "how does this compare to the older approach though?",
]


def make_mock_posts(n=100):
    posts = []
    for i in range(1, n + 1):
        author = random.choice(NAMES)
        text = random.choice(COMMENT_TEXTS)

        # ~1 in 4 posts gets a photo attached, picsum gives a stable image per seed
        image = f"https://picsum.photos/seed/{i}/500/300" if random.random() < 0.25 else None

        post = Post(post_id=i, author=author, text=text, image=image)
        post.retweets = random.randint(0, 15)

        for _ in range(random.randint(0, 40)):
            post.likes.append(Like(user=f"user{random.randint(1, 999)}"))

        posts.append(post)
    return posts


MOCK_POSTS = make_mock_posts(100)


@cache_feed(ttl=30)
async def fetch_posts(cursor: int, limit: int):
    # This whole function body only runs on a cache MISS — cache_feed
    # skips it entirely on a HIT. So shuffling here means: the feed only
    # reshuffles when the cache actually expires (every 30s), not on
    # every single request. This is what keeps cache hit/miss behavior
    # fully intact AND makes the feed visibly change over time.
    if cursor == 0:
        random.shuffle(MOCK_POSTS)

    await asyncio.sleep(0.3)  # simulated I/O latency — this is why async matters

    for batch in paginate_posts(MOCK_POSTS[cursor:], batch_size=limit):
        return [post.to_dict() for post in batch]
    return []


@app.get("/feed")
async def get_feed(cursor: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50)):
    posts = await fetch_posts(cursor, limit)
    next_cursor = cursor + limit if (cursor + limit) < len(MOCK_POSTS) else None

    return {
        "posts": posts,
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
    }