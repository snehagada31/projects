import { useState, useEffect } from "react";
import Tweet from "./Tweet.jsx";
import { fetchBookmarks } from "../api.js";

export default function BookmarksView({ currentUser, onRequireAuth, onComment, onImageClick }) {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!currentUser?.id) return;
    loadBookmarks();
  }, [currentUser?.id]);

  async function loadBookmarks() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBookmarks();
      setBookmarks(data.posts || []);
    } catch (err) {
      console.error("Failed to load bookmarks:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!currentUser) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center", color: "#71767b" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔖</div>
        <h2 style={{ color: "#e7e9ea", marginBottom: "8px" }}>Save posts for later</h2>
        <p style={{ maxWidth: "340px", margin: "0 auto 20px auto", lineHeight: "1.5" }}>
          Don’t let the good ones fly away! Sign in to bookmark posts to easily find them again in the future.
        </p>
        <button
          onClick={onRequireAuth}
          style={{
            background: "#1d9bf0",
            color: "#fff",
            border: "none",
            borderRadius: "9999px",
            padding: "10px 24px",
            fontWeight: "bold",
            cursor: "pointer",
          }}
        >
          Sign In
        </button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ padding: "16px", borderBottom: "1px solid #2f3336" }}>
        <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "800", color: "#e7e9ea" }}>Bookmarks</h2>
        <span style={{ fontSize: "13px", color: "#71767b" }}>@{currentUser.handle}</span>
      </div>

      {loading && (
        <div style={{ padding: "30px", textAlign: "center", color: "#71767b" }}>
          Loading bookmarks...
        </div>
      )}

      {error && (
        <div style={{ padding: "20px", textAlign: "center", color: "#f4212e" }}>
          <p>{error}</p>
          <button
            onClick={loadBookmarks}
            style={{
              marginTop: "8px",
              background: "#1d9bf0",
              color: "#fff",
              border: "none",
              borderRadius: "9999px",
              padding: "6px 16px",
              cursor: "pointer",
            }}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && bookmarks.length === 0 && (
        <div style={{ padding: "50px 20px", textAlign: "center", color: "#71767b" }}>
          <div style={{ fontSize: "40px", marginBottom: "12px" }}>🔖</div>
          <h3 style={{ color: "#e7e9ea", marginBottom: "8px" }}>Save posts for later</h3>
          <p style={{ maxWidth: "360px", margin: "0 auto", lineHeight: "1.5" }}>
            Don’t let the good ones fly away! Bookmark posts to easily find them again in the future.
          </p>
        </div>
      )}

      {!loading && bookmarks.map((post) => (
        <div key={post.id} style={{ borderBottom: "1px solid #2f3336" }}>
          <Tweet
            id={post.id}
            authorId={post.authorId}
            author={post.author}
            handle={post.handle}
            authorAvatar={post.authorAvatar}
            text={post.text}
            image={post.image}
            time={post.created_at}
            initialComments={post.comment_count}
            initialRetweets={post.retweet_count}
            initialLikes={post.like_count}
            initialLiked={post.liked_by_viewer}
            initialRetweeted={post.reposted_by_viewer}
            initialBookmarked={true}
            replyToHandle={post.reply_to_handle}
            currentUser={currentUser}
            onRequireAuth={onRequireAuth}
            onComment={() => onComment && onComment(post.id, post.handle)}
            onImageClick={onImageClick}
          />
        </div>
      ))}
    </div>
  );
}
