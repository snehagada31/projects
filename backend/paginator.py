"""
Topic 11 — generator-based feed paginator.
Yields batches instead of returning the whole feed at once.
"""


def paginate_posts(posts, batch_size=10):
    for start in range(0, len(posts), batch_size):
        yield posts[start:start + batch_size]