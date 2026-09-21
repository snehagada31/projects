import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import RightPanel from "./components/RightPanel.jsx";
import Tweet from "./components/Tweet.jsx";
import ReplyModal from "./components/ReplyModal.jsx";
import ImageLightbox from "./components/ImageLightbox.jsx";
import { fetchFeed, createPost, deletePost, fetchPostReplies, searchPosts, fetchUsers, followUser, unfollowUser } from "./api.js";

export default function App() {
  const [loadedPosts, setLoadedPosts] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [repliesByPost, setRepliesByPost] = useState({});
  const [expandedReplies, setExpandedReplies] = useState({});
  const [loadingReplies, setLoadingReplies] = useState({});

  const [replyingTo, setReplyingTo] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [matchedUsers, setMatchedUsers] = useState([]);
  const [searching, setSearching] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);

  const [composerText, setComposerText] = useState("");
  const [isPosting, setIsPosting] = useState(false);

  const feedStatusRef = useRef(null);

  const loadNextBatch = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFeed(cursor, 10);
      setLoadedPosts((prev) => {
        const existingIds = new Set(prev.map((p) => p.id));
        const newOnes = data.posts.filter((p) => !existingIds.has(p.id));
        return [...prev, ...newOnes];
      });
      setHasMore(data.has_more);
      setCursor(data.next_cursor ?? null);
    } catch (err) {
      console.error("Feed fetch failed:", err);
      setError("Could not connect to backend. Please make sure backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }, [cursor, loading, hasMore]);

  useEffect(() => {
    const el = feedStatusRef.current;
    if (!el || !hasMore) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        loadNextBatch();
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadNextBatch, hasMore]);

  useEffect(() => {
    loadNextBatch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Pre-load replies for posts that have comments so seed.sql comments show up
  useEffect(() => {
    loadedPosts.forEach((post) => {
      if (post.comment_count > 0 && !repliesByPost[post.id] && !loadingReplies[post.id]) {
        fetchPostReplies(post.id)
          .then((data) => {
            setRepliesByPost((prev) => ({ ...prev, [post.id]: data.replies }));
            setExpandedReplies((prev) => ({ ...prev, [post.id]: true }));
          })
          .catch((err) => console.error("Failed to load initial replies:", err));
      }
    });
  }, [loadedPosts, repliesByPost, loadingReplies]);

  // Search people and posts
  useEffect(() => {
    const q = searchQuery.trim();
    if (!q) {
      setSearchResults(null);
      setMatchedUsers([]);
      return;
    }

    let isCurrent = true;
    setSearching(true);
    const debounce = setTimeout(async () => {
      try {
        const [users, postsRes] = await Promise.all([
          fetchUsers(q).catch(() => []),
          searchPosts(q).catch(() => ({ posts: [] })),
        ]);
        if (isCurrent) {
          setMatchedUsers(users);
          setSearchResults(postsRes.posts || []);
        }
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        if (isCurrent) setSearching(false);
      }
    }, 200);

    return () => {
      isCurrent = false;
      clearTimeout(debounce);
    };
  }, [searchQuery]);

  async function handleToggleFollowUser(user) {
    const isFollowing = user.following;
    setMatchedUsers((prev) =>
      prev.map((u) => (u.id === user.id ? { ...u, following: !isFollowing } : u))
    );
    try {
      if (isFollowing) {
        await unfollowUser(user.id);
      } else {
        await followUser(user.id);
      }
    } catch (err) {
      console.error("Failed to toggle follow:", err);
      setMatchedUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, following: isFollowing } : u))
      );
    }
  }

  async function handleCreatePost(e) {
    e.preventDefault();
    const text = composerText.trim();
    if (!text || isPosting) return;

    setIsPosting(true);
    try {
      const res = await createPost({ kind: "original", text });
      const item = res.item;
      const newPost = {
        id: item.id,
        author: item.author?.displayName || "Asha",
        handle: "@" + (item.author?.handle || "asha"),
        text: item.text,
        image: item.media?.[0]?.largeUrl || null,
        like_count: 0,
        comment_count: 0,
        retweet_count: 0,
        liked_by_viewer: false,
        reposted_by_viewer: false,
        created_at: item.createdAt,
      };
      setLoadedPosts((prev) => [newPost, ...prev]);
      setComposerText("");
    } catch (err) {
      alert("Failed to create post: " + err.message);
    } finally {
      setIsPosting(false);
    }
  }

  async function toggleReplies(postId) {
    if (expandedReplies[postId]) {
      setExpandedReplies((prev) => ({ ...prev, [postId]: false }));
      return;
    }

    if (repliesByPost[postId]) {
      setExpandedReplies((prev) => ({ ...prev, [postId]: true }));
      return;
    }

    setLoadingReplies((prev) => ({ ...prev, [postId]: true }));
    try {
      const data = await fetchPostReplies(postId);
      setRepliesByPost((prev) => ({ ...prev, [postId]: data.replies }));
      setExpandedReplies((prev) => ({ ...prev, [postId]: true }));
    } catch (err) {
      console.error("Failed to load replies:", err);
    } finally {
      setLoadingReplies((prev) => ({ ...prev, [postId]: false }));
    }
  }

  function openReplyModal(postId, handle) {
    setReplyingTo({ targetId: postId, handle });
    if (!expandedReplies[postId]) {
      toggleReplies(postId);
    }
  }

  async function submitReply(text) {
    const targetPostId = replyingTo?.targetId;
    if (!targetPostId) return;

    try {
      const res = await createPost({ kind: "reply", text, replyToId: targetPostId });
      const item = res.item;
      const newReply = {
        id: item.id,
        author: item.author?.displayName || "Asha",
        handle: "@" + (item.author?.handle || "asha"),
        text: item.text,
        created_at: item.createdAt,
      };

      setRepliesByPost((prev) => ({
        ...prev,
        [targetPostId]: [newReply, ...(prev[targetPostId] || [])],
      }));
      setExpandedReplies((prev) => ({ ...prev, [targetPostId]: true }));
      setLoadedPosts((prev) =>
        prev.map((p) =>
          p.id === targetPostId ? { ...p, comment_count: p.comment_count + 1 } : p
        )
      );
    } catch (e) {
      console.error("Failed to persist reply to backend:", e);
      alert("Failed to create reply: " + e.message);
    } finally {
      setReplyingTo(null);
    }
  }

  async function handleDeleteReply(postId, replyId) {
    try {
      await deletePost(replyId);
      setRepliesByPost((prev) => ({
        ...prev,
        [postId]: (prev[postId] || []).filter((r) => r.id !== replyId),
      }));
      setLoadedPosts((prev) =>
        prev.map((p) =>
          p.id === postId ? { ...p, comment_count: Math.max(0, p.comment_count - 1) } : p
        )
      );
    } catch (err) {
      console.error("Failed to delete reply:", err);
      alert("Failed to delete reply: " + err.message);
    }
  }

  const visiblePosts = searchResults !== null ? searchResults : loadedPosts;

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="feed">
        <header>
          <button aria-label="Go back">&larr;</button>
          <h1>Feed</h1>
        </header>

        {/* Tweet Composer */}
        <form
          onSubmit={handleCreatePost}
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "10px",
            padding: "16px",
            borderBottom: "1px solid #2f3336",
          }}
        >
          <textarea
            value={composerText}
            onChange={(e) => setComposerText(e.target.value)}
            placeholder="What is happening?!"
            maxLength={280}
            rows={3}
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#e7e9ea",
              fontSize: "18px",
              resize: "none",
              fontFamily: "inherit",
            }}
          />
          <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center" }}>
            <button
              type="submit"
              disabled={!composerText.trim() || isPosting}
              style={{
                background: "#1d9bf0",
                color: "white",
                border: "none",
                borderRadius: "9999px",
                padding: "8px 20px",
                fontSize: "15px",
                fontWeight: "700",
                cursor: composerText.trim() && !isPosting ? "pointer" : "default",
                opacity: composerText.trim() && !isPosting ? 1 : 0.5,
              }}
            >
              {isPosting ? "Posting..." : "Post"}
            </button>
          </div>
        </form>

        {/* Search header */}
        {searchQuery.trim() && (
          <div style={{ padding: "12px 16px", color: "#71767b", fontSize: "14px", borderBottom: "1px solid #2f3336" }}>
            {searching ? "Searching..." : `Results for "${searchQuery}"`}
          </div>
        )}

        {/* Search Results: People / Persons */}
        {searchQuery.trim() && matchedUsers.length > 0 && (
          <div style={{ borderBottom: "1px solid #2f3336", padding: "16px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "12px", color: "#e7e9ea" }}>People</h2>
            {matchedUsers.map((user) => (
              <div
                key={user.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "10px 0",
                  borderBottom: "1px solid #222",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <img
                    src={user.avatar?.smallUrl || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(user.displayName)}`}
                    alt=""
                    style={{ width: "48px", height: "48px", borderRadius: "50%" }}
                  />
                  <div>
                    <div style={{ fontWeight: "700", fontSize: "16px", color: "#e7e9ea" }}>{user.displayName}</div>
                    <div style={{ color: "#71767b", fontSize: "14px" }}>@{user.handle}</div>
                    {user.bio && <div style={{ color: "#e7e9ea", fontSize: "13px", marginTop: "4px" }}>{user.bio}</div>}
                  </div>
                </div>
                <button
                  onClick={() => handleToggleFollowUser(user)}
                  style={{
                    background: user.following ? "transparent" : "#eff3f4",
                    color: user.following ? "#eff3f4" : "#0f1419",
                    border: user.following ? "1px solid #536471" : "none",
                    borderRadius: "9999px",
                    padding: "6px 18px",
                    fontWeight: "700",
                    fontSize: "14px",
                    cursor: "pointer",
                  }}
                >
                  {user.following ? "Following" : "Follow"}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Posts feed */}
        <section className="feed-posts">
          {searchQuery.trim() && (
            <div style={{ padding: "12px 16px 4px 16px", fontWeight: "700", color: "#71767b", fontSize: "14px" }}>
              Posts
            </div>
          )}

          {visiblePosts.map((post) => {
            const replies = repliesByPost[post.id] || [];
            const isExpanded = expandedReplies[post.id];

            return (
              <div key={post.id} style={{ borderBottom: "1px solid #2f3336" }}>
                <Tweet
                  id={post.id}
                  author={post.author}
                  handle={post.handle}
                  text={post.text}
                  image={post.image}
                  time={post.created_at}
                  initialComments={post.comment_count}
                  initialRetweets={post.retweet_count}
                  initialLikes={post.like_count}
                  initialLiked={post.liked_by_viewer}
                  initialRetweeted={post.reposted_by_viewer}
                  onComment={() => openReplyModal(post.id, post.handle)}
                  onImageClick={setLightboxImage}
                />

                {/* Reply toggle button if replies exist */}
                {post.comment_count > 0 && (
                  <div style={{ paddingLeft: "68px", paddingBottom: "8px" }}>
                    <button
                      onClick={() => toggleReplies(post.id)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "#1d9bf0",
                        fontSize: "13px",
                        cursor: "pointer",
                        padding: "0",
                      }}
                    >
                      {isExpanded ? "Hide replies" : `View ${post.comment_count} ${post.comment_count === 1 ? "reply" : "replies"}`}
                    </button>
                  </div>
                )}

                {/* Rendered replies */}
                {isExpanded && (
                  <div className="post-replies" style={{ paddingLeft: "40px", borderLeft: "2px solid #2f3336", marginLeft: "28px" }}>
                    {replies.map((reply) => (
                      <Tweet
                        key={reply.id}
                        id={reply.id}
                        author={reply.author}
                        handle={reply.handle}
                        text={reply.text}
                        time={reply.created_at}
                        isReply
                        showActions={false}
                        onDelete={() => handleDeleteReply(post.id, reply.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Skeleton while loading */}
          {loading && (
            <div style={{ padding: "20px", textAlign: "center", color: "#71767b" }}>
              Loading posts...
            </div>
          )}

          {/* Controlled Error with Retry button */}
          {error && (
            <div style={{ padding: "20px", textAlign: "center", color: "#f4212e" }}>
              <p style={{ marginBottom: "10px" }}>{error}</p>
              <button
                onClick={loadNextBatch}
                style={{
                  background: "#1d9bf0",
                  color: "white",
                  border: "none",
                  borderRadius: "9999px",
                  padding: "8px 20px",
                  cursor: "pointer",
                  fontWeight: "bold",
                }}
              >
                Retry
              </button>
            </div>
          )}

          {/* Infinite scroll observer target */}
          {!loading && !error && !searchQuery.trim() && (
            <p ref={feedStatusRef} className="feed-status" style={{ textAlign: "center", padding: "16px", color: "#71767b" }}>
              {hasMore ? "Scroll for more" : "You've reached the end"}
            </p>
          )}
        </section>
      </main>

      <RightPanel searchQuery={searchQuery} onSearchChange={setSearchQuery} />

      <ReplyModal
        replyingTo={replyingTo}
        onClose={() => setReplyingTo(null)}
        onSubmit={submitReply}
      />

      <ImageLightbox src={lightboxImage} onClose={() => setLightboxImage(null)} />
    </div>
  );
}