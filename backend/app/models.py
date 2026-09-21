"""
Topic 12 — Post, Comment, Like classes.
"""


class Like:
    def __init__(self, user):
        self.user = user

    def __repr__(self):
        return f"Like(user={self.user!r})"

    def __eq__(self, other):
        return isinstance(other, Like) and self.user == other.user


class Comment:
    def __init__(self, author, text):
        self.author = author
        self.text = text

    def __repr__(self):
        return f"Comment(author={self.author!r}, text={self.text!r})"

    def __eq__(self, other):
        return isinstance(other, Comment) and self.author == other.author and self.text == other.text


class Post:
    def __init__(self, post_id, author, text, image=None):
        self.post_id = post_id
        self.author = author
        self.text = text
        self.image = image  # optional photo URL, None for text-only posts
        self.comments = []
        self.likes = []
        self.retweets = 0

    def __repr__(self):
        return f"Post(id={self.post_id}, author={self.author!r})"

    def __eq__(self, other):
        return isinstance(other, Post) and self.post_id == other.post_id

    def __len__(self):
        return len(self.comments)  # len(post) == comment count, not likes

    def to_dict(self):
        return {
            "id": self.post_id,
            "author": self.author,
            "text": self.text,
            "image": self.image,
            "comment_count": len(self),
            "like_count": len(self.likes),
            "retweet_count": self.retweets,
        }