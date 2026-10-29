import { useState, useEffect } from "react";
import { likePost, unlikePost, repostPost, unrepostPost, bookmarkPost, unbookmarkPost, editPost } from "../api.js";

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
  authorId,
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
  replyToHandle = null,
  showActions = true,
  currentUser = null,
  onRequireAuth = null,
  onArchive = null,
}) {
  const [liked, setLiked] = useState(initialLiked);
  const [retweeted, setRetweeted] = useState(initialRetweeted);
  const [bookmarked, setBookmarked] = useState(initialBookmarked);
  const [likeCount, setLikeCount] = useState(initialLikes);
  const [retweetCount, setRetweetCount] = useState(initialRetweets);
  const [toastMessage, setToastMessage] = useState(null);

  // Edit states
  const [isEditing, setIsEditing] = useState(false);
  const [currentText, setCurrentText] = useState(text || "");
  const [editText, setEditText] = useState(text || "");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  const cleanPostHandle = (handle || "").replace("@", "").toLowerCase();
  const cleanUserHandle = (currentUser?.handle || "").replace("@", "").toLowerCase();
  const isOwnPost = Boolean(
    currentUser && (
      (authorId && String(currentUser.id) === String(authorId)) ||
      (cleanPostHandle && cleanUserHandle && cleanPostHandle === cleanUserHandle)
    )
  );

  // Time window: allow editing only within 15 minutes of creation
  const isWithinEditWindow = time ? (Date.now() - new Date(time).getTime()) <= 15 * 60 * 1000 : true;

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
    setCurrentText(text || "");
    setEditText(text || "");
  }, [text]);

  useEffect(() => {
    if (!toastMessage) return;
    const timer = setTimeout(() => setToastMessage(null), 1800);
    return () => clearTimeout(timer);
  }, [toastMessage]);

  async function handleLike() {
    if (!currentUser && onRequireAuth) {
      onRequireAuth();
      return;
    }

    if (isOwnPost) {
      setToastMessage("You cannot like your own post");
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

    if (isOwnPost) {
      setToastMessage("You cannot repost your own post");
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

  async function handleSaveEdit(e) {
    e.preventDefault();
    if (!editText.trim()) return;
    setIsSavingEdit(true);
    try {
      await editPost(id, editText.trim());
      setCurrentText(editText.trim());
      setIsEditing(false);
      setToastMessage("Post updated!");
    } catch (err) {
      alert("Failed to edit post: " + err.message);
    } finally {
      setIsSavingEdit(false);
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

        {(canDelete || isOwnPost) && (
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            {isWithinEditWindow ? (
              <button
                onClick={() => setIsEditing(!isEditing)}
                title="Edit post (within 15m)"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#1d9bf0",
                  cursor: "pointer",
                  padding: "4px 6px",
                  fontSize: "13px",
                  borderRadius: "4px",
                }}
              >
                ✏️ Edit
              </button>
            ) : (
              <span
                title="Edit window expired (over 15 minutes since posting)"
                style={{ color: "#536471", fontSize: "12px", cursor: "help" }}
              >
                ⏳ Locked
              </span>
            )}

            {onArchive && (
              <button
                onClick={() => {
                  if (window.confirm("Archive this post? Only you will be able to see it in your private Archive.")) {
                    onArchive({
                      id,
                      authorId,
                      author,
                      handle,
                      authorAvatar,
                      text: currentText,
                      image,
                      created_at: time,
                      like_count: likeCount,
                      comment_count: initialComments,
                      retweet_count: retweetCount,
                      liked_by_viewer: liked,
                      reposted_by_viewer: retweeted,
                      bookmarked_by_viewer: bookmarked,
                    });
                  }
                }}
                title="Archive post at any time (moves to your private Archive)"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#71767b",
                  cursor: "pointer",
                  padding: "4px 6px",
                  fontSize: "13px",
                  borderRadius: "4px",
                }}
                onMouseEnter={(e) => (e.target.style.color = "#eff3f4")}
                onMouseLeave={(e) => (e.target.style.color = "#71767b")}
              >
                📦 Archive
              </button>
            )}

            {onDelete && (
              <button
                onClick={onDelete}
                title="Delete Post"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#71767b",
                  cursor: "pointer",
                  padding: "4px 6px",
                  fontSize: "13px",
                  borderRadius: "4px",
                }}
                onMouseEnter={(e) => (e.target.style.color = "#f4212e")}
                onMouseLeave={(e) => (e.target.style.color = "#71767b")}
              >
                🗑️ Delete
              </button>
            )}
          </div>
        )}
      </div>

      {replyToHandle && (
        <div style={{ fontSize: "13px", color: "#71767b", marginTop: "4px", marginBottom: "4px" }}>
          Replying to <span style={{ color: "#1d9bf0", fontWeight: "bold" }}>@{replyToHandle.replace("@", "")}</span>
        </div>
      )}

      {isEditing ? (
        <form onSubmit={handleSaveEdit} style={{ marginTop: "10px", marginBottom: "10px" }}>
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            rows={3}
            style={{
              width: "100%",
              background: "#000",
              border: "1px solid #1d9bf0",
              borderRadius: "8px",
              color: "#fff",
              padding: "8px",
              fontSize: "15px",
              resize: "none",
            }}
          />
          <div style={{ display: "flex", gap: "8px", marginTop: "6px", justifyContent: "flex-end" }}>
            <button
              type="button"
              onClick={() => { setIsEditing(false); setEditText(currentText); }}
              style={{
                background: "transparent",
                border: "1px solid #536471",
                color: "#71767b",
                padding: "4px 12px",
                borderRadius: "999px",
                cursor: "pointer",
                fontSize: "13px",
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSavingEdit || !editText.trim()}
              style={{
                background: "#1d9bf0",
                border: "none",
                color: "#fff",
                fontWeight: "bold",
                padding: "4px 14px",
                borderRadius: "999px",
                cursor: isSavingEdit ? "not-allowed" : "pointer",
                fontSize: "13px",
              }}
            >
              {isSavingEdit ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      ) : (
        <p style={{ marginTop: "10px", marginBottom: "10px", wordBreak: "break-word" }}>{currentText}</p>
      )}

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
              style={isOwnPost ? { opacity: 0.5, cursor: "not-allowed" } : {}}
              title={isOwnPost ? "You cannot repost your own post" : "Repost"}
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
              style={isOwnPost ? { opacity: 0.5, cursor: "not-allowed" } : {}}
              title={isOwnPost ? "You cannot like your own post" : "Like"}
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
