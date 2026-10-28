import { useState, useEffect } from "react";
import { likePost, unlikePost, repostPost, unrepostPost, bookmarkPost, unbookmarkPost } from "../api.js";

function formatTweetTime(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return "";
  const timeStr = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `${timeStr} · ${dateStr}`;
}

export default function Tweet({
  id,
  author,
  handle,
  authorAvatar,
  text,
  image,
  time,
  initialComments = 0,
  initialRetweets = 0,
  initialLikes = 0,
  initialLiked = false,
  initialRetweeted = false,
  initialBookmarked = false,
  onComment,
  onDelete,
  canDelete = false,
  onImageClick,
  isReply = false,
  showActions = true,
  currentUser = null,
  onRequireAuth = null,
}) {
  const [liked, setLiked] = useState(initialLiked);
  const [retweeted, setRetweeted] = useState(initialRetweeted);
  const [bookmarked, setBookmarked] = useState(initialBookmarked);
  const [likeCount, setLikeCount] = useState(initialLikes);
  const [retweetCount, setRetweetCount] = useState(initialRetweets);
  const [toastMessage, setToastMessage] = useState(null);

  useEffect(() => {
    setLiked(initialLiked);
  }, [initialLiked]);

  useEffect(() => {
    setRetweeted(initialRetweeted);
  }, [initialRetweeted]);

  useEffect(() => {
    setBookmarked(initialBookmarked);
  }, [initialBookmarked]);

  useEffect(() => {
    setLikeCount(initialLikes);
  }, [initialLikes]);

  useEffect(() => {
    setRetweetCount(initialRetweets);
  }, [initialRetweets]);

  useEffect(() => {
    if (!toastMessage) return;
    const timer = setTimeout(() => setToastMessage(null), 1500);
    return () => clearTimeout(timer);
  }, [toastMessage]);

  async function handleLike() {
    if (!currentUser && onRequireAuth) {
      onRequireAuth();
      return;
    }

    const nowLiked = !liked;
    setLiked(nowLiked);
    setLikeCount((prev) => prev + (nowLiked ? 1 : -1));
    setToastMessage(nowLiked ? "Liked" : "Unliked");

    if (!id) return;

    try {
      if (nowLiked) {
        const res = await likePost(id);
        setLikeCount(res.likeCount ?? res.like_count);
        setLiked(res.likedByViewer ?? res.liked_by_viewer ?? true);
      } else {
        const res = await unlikePost(id);
        setLikeCount(res.likeCount ?? res.like_count);
        setLiked(res.likedByViewer ?? res.liked_by_viewer ?? false);
      }
    } catch (err) {
      console.error("Failed to update like on backend:", err);
      // Rollback optimistic update
      setLiked(!nowLiked);
      setLikeCount((prev) => prev + (nowLiked ? -1 : 1));
      setToastMessage(err.message || "Error updating like");
    }
  }

  async function handleRetweet() {
    if (!currentUser && onRequireAuth) {
      onRequireAuth();
      return;
    }

    const nowRetweeted = !retweeted;
    setRetweeted(nowRetweeted);
    setRetweetCount((prev) => prev + (nowRetweeted ? 1 : -1));
    setToastMessage(nowRetweeted ? "Reposted" : "Undo Repost");

    if (!id) return;

    try {
      if (nowRetweeted) {
        const res = await repostPost(id);
        setRetweetCount(res.retweetCount ?? res.retweet_count);
        setRetweeted(res.repostedByViewer ?? res.reposted_by_viewer ?? true);
      } else {
        const res = await unrepostPost(id);
        setRetweetCount(res.retweetCount ?? res.retweet_count);
        setRetweeted(res.repostedByViewer ?? res.reposted_by_viewer ?? false);
      }
    } catch (err) {
      console.error("Failed to update repost on backend:", err);
      // Rollback optimistic update
      setRetweeted(!nowRetweeted);
      setRetweetCount((prev) => prev + (nowRetweeted ? -1 : 1));
      setToastMessage(err.message || "Error updating repost");
    }
  }

  async function handleComment() {
    if (!currentUser && onRequireAuth) {
      onRequireAuth();
      return;
    }
    if (onComment) onComment();
  }

  async function handleBookmark() {
    if (!currentUser && onRequireAuth) {
      onRequireAuth();
      return;
    }

    const nowBookmarked = !bookmarked;
    setBookmarked(nowBookmarked);
    setToastMessage(nowBookmarked ? "Saved to Bookmarks" : "Removed from Bookmarks");

    if (!id) return;

    try {
      if (nowBookmarked) {
        await bookmarkPost(id);
      } else {
        await unbookmarkPost(id);
      }
    } catch (err) {
      console.error("Failed to update bookmark:", err);
      setBookmarked(!nowBookmarked);
      setToastMessage(err.message || "Error updating bookmark");
    }
  }

  async function handleShare() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert("Link copied!");
    } catch {
      alert("Couldn't copy link");
    }
  }

  const avatarSrc =
    authorAvatar ||
    `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(handle || author)}`;

  return (
    <article className={`tweet${isReply ? " tweet--reply" : ""}`}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div className="tweet-author">
          <img className="avatar" src={avatarSrc} alt="" />
          <div className="tweet-author-info">
            <span>{author}</span>
            <span>{handle}</span>
          </div>
        </div>

        {canDelete && onDelete && (
          <button
            onClick={onDelete}
            title="Delete Post"
            style={{
              background: "transparent",
              border: "none",
              color: "#71767b",
              cursor: "pointer",
              padding: "4px 8px",
              fontSize: "14px",
              borderRadius: "4px",
            }}
            onMouseEnter={(e) => (e.target.style.color = "#f4212e")}
            onMouseLeave={(e) => (e.target.style.color = "#71767b")}
          >
            🗑️ Delete
          </button>
        )}
      </div>

      <p style={{ marginTop: "10px", marginBottom: "10px", wordBreak: "break-word" }}>{text}</p>

      {image && (
        <img
          className="tweet-photo"
          src={image}
          alt=""
          onClick={() => onImageClick && onImageClick(image)}
          style={{ cursor: "pointer" }}
        />
      )}

      {time && <time dateTime={time}>{formatTweetTime(time)}</time>}

      {showActions && (
        <div className="tweet-actions">
          <button className="action-comment" aria-label="Reply" onClick={handleComment}>
            💬 <span>{initialComments}</span>
          </button>
          <span className="like-wrapper">
            <button
              className={`action-retweet${retweeted ? " retweeted" : ""}`}
              aria-label="Repost"
              onClick={handleRetweet}
            >
              🔁 <span>{retweetCount}</span>
            </button>
            {toastMessage && !liked && <span className="like-toast">{toastMessage}</span>}
          </span>
          <span className="like-wrapper">
            <button
              className={`action-like${liked ? " liked" : ""}`}
              aria-label="Like"
              onClick={handleLike}
            >
              {liked ? "♥" : "♡"} <span>{likeCount}</span>
            </button>
            {toastMessage && liked && <span className="like-toast">{toastMessage}</span>}
          </span>
          <button
            className={`action-bookmark${bookmarked ? " bookmarked" : ""}`}
            aria-label="Bookmark"
            onClick={handleBookmark}
            style={{
              background: "transparent",
              border: "none",
              color: bookmarked ? "#1d9bf0" : "inherit",
              cursor: "pointer",
              fontSize: "16px",
            }}
            title={bookmarked ? "Remove Bookmark" : "Bookmark"}
          >
            {bookmarked ? "🔖" : "🏷️"}
          </button>
          <button className="action-share" aria-label="Share" onClick={handleShare}>
            ↗
          </button>
        </div>
      )}
    </article>
  );
}
