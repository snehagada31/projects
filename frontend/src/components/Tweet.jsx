import { useState, useEffect } from "react";
import { likePost, unlikePost, repostPost, unrepostPost } from "../api.js";

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
  text,
  image,
  time,
  initialComments = 0,
  initialRetweets = 0,
  initialLikes = 0,
  initialLiked = false,
  initialRetweeted = false,
  onComment,
  onDelete,
  onImageClick,
  isReply = false,
  showActions = true,
}) {
  const [liked, setLiked] = useState(initialLiked);
  const [retweeted, setRetweeted] = useState(initialRetweeted);
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
      setToastMessage("Error updating like");
    }
  }

  async function handleRetweet() {
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
      setToastMessage("Error updating repost");
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

  return (
    <article className={`tweet${isReply ? " tweet--reply" : ""}`}>
      <div className="tweet-author">
        <img
          className="avatar"
          src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(author)}`}
          alt=""
        />
        <div className="tweet-author-info">
          <span>{author}</span>
          <span>{handle}</span>
        </div>
      </div>

      <p>{text}</p>

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
          <button className="action-comment" aria-label="Reply" onClick={onComment}>
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
          <button className="action-share" aria-label="Share" onClick={handleShare}>
            ↗
          </button>
        </div>
      )}

      {isReply && onDelete && (
        <button className="delete-btn" onClick={onDelete}>
          Delete
        </button>
      )}
    </article>
  );
}
