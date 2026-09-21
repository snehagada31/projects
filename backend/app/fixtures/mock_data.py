"""
Same mock data your current main.py generates — just relocated so
repositories/routes don't build it inline. This is what "fixture
repository" means in the PRD: a repository backed by fixed, known data,
as opposed to a real database.
"""

import random
from app.models import Post, Like

NAMES = [
    "Maya Chen", "Dev Patel", "Alex Rivera", "Priya Nair", "Jordan Lee",
    "Sam Okafor", "Riya Kapoor", "Leo Martins", "Zara Ahmed", "Kenji Watanabe",
]

COMMENT_TEXTS = [
    "wait this actually makes sense now, thanks for breaking it down",
    "I always got confused between these two, good explanation",
    "following this thread, need this for my own project too",
]


def make_mock_posts(n=100):
    posts = []
    for i in range(1, n + 1):
        author = random.choice(NAMES)
        text = random.choice(COMMENT_TEXTS)
        post = Post(post_id=i, author=author, text=text)
        for _ in range(random.randint(0, 40)):
            post.likes.append(Like(user=f"user{random.randint(1, 999)}"))
        posts.append(post)
    return posts


MOCK_POSTS = make_mock_posts(100)