import { useState, useEffect } from "react";

// One component renders EVERY tweet on the page — the main tweet, static
// replies, loaded-from-backend posts, and user-submitted replies all pass
// through here with different props. This is the React equivalent of your
// old buildLoadedPost()/buildReplyArticle() functions — but instead of
// building HTML strings by hand, you describe what it should look like
// and React keeps the DOM in sync automatically.
// Turns the raw ISO datetime (e.g. "2026-08-25T09:14:00+05:30") into the
// human-friendly text X actually shows ("9:14 AM · Aug 25, 2026") — the
// ISO string still lives in the datetime="" attribute for machines/screen
// readers, this is just what's VISIBLE.
function formatTweetTime(isoString) {
  const d = new Date(isoString);
  const timeStr = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `${timeStr} · ${dateStr}`;
}

export default function Tweet({
  author,
  handle,
  text,
  image,
  time,
  initialComments = 0,
  initialRetweets = 0,
  initialLikes = 0,
  onComment,      // called when this tweet's comment button is clicked
  onDelete,       // only passed for user-submitted replies (shows a Delete button)
  onImageClick,   // called with the image URL when the photo is tapped
  isReply = false,
  showActions = true, // set false for tweets that shouldn't show like/retweet/comment/share
}) {
  // Each Tweet manages its OWN like/retweet state — no shared global
  // variable, no manually finding this specific button in the DOM later.
  // React re-renders just this component when its state changes.
  const [liked, setLiked] = useState(false);
  const [retweeted, setRetweeted] = useState(false);
  const [likeCount, setLikeCount] = useState(initialLikes);
  const [retweetCount, setRetweetCount] = useState(initialRetweets);
  const [likeMessage, setLikeMessage] = useState(null); // "Liked" / "Unliked", briefly shown

  // Clears the message automatically after 1.5s — acts like a toast.
  // Re-runs whenever likeMessage changes; the cleanup function cancels
  // the old timer if a new click happens before the previous one fires.
  useEffect(() => {
    if (!likeMessage) return;
    const timer = setTimeout(() => setLikeMessage(null), 1500);
    return () => clearTimeout(timer);
  }, [likeMessage]);

  function handleLike() {
    const nowLiked = !liked;
    setLiked(nowLiked);
    setLikeCount(likeCount + (nowLiked ? 1 : -1));
    setLikeMessage(nowLiked ? "Liked" : "Unliked");
  }

  function handleRetweet() {
    setRetweeted(!retweeted);
    setRetweetCount(retweetCount + (retweeted ? -1 : 1));
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
          onClick={() => onImageClick(image)}
          style={{ cursor: "pointer" }}
        />
      )}

      {time && <time dateTime={time}>{formatTweetTime(time)}</time>}

      {showActions && (
      <div className="tweet-actions">
        <button className="action-comment" aria-label="Reply" onClick={onComment}>
          💬 <span>{initialComments}</span>
        </button>
        <button
          className={`action-retweet${retweeted ? " retweeted" : ""}`}
          aria-label="Retweet"
          onClick={handleRetweet}
        >
          🔁 <span>{retweetCount}</span>
        </button>
        <span className="like-wrapper">
          <button
            className={`action-like${liked ? " liked" : ""}`}
            aria-label="Like"
            onClick={handleLike}
          >
            {liked ? "♥" : "♡"} <span>{likeCount}</span>
          </button>
          {likeMessage && <span className="like-toast">{likeMessage}</span>}
        </span>
        <button className="action-share" aria-label="Share" onClick={handleShare}>
          ↗
        </button>
      </div>
      )}

      {isReply && (
        <button className="delete-btn" onClick={onDelete}>
          Delete
        </button>
      )}
    </article>
  );
}
