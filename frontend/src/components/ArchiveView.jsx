import { useState, useEffect } from "react";
import Tweet from "./Tweet.jsx";
import { fetchPostReplies } from "../api.js";

export function getArchivedPostIds(userId) {
  if (!userId) return [];
  try {
    const raw = localStorage.getItem(`social_archive_${userId}`);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveArchivedPostIds(userId, ids) {
  if (!userId) return;
  try {
    localStorage.setItem(`social_archive_${userId}`, JSON.stringify(ids));
  } catch (err) {
    console.error("Failed to save archived post IDs:", err);
  }
}

export function getArchivedPostsData(userId) {
  if (!userId) return [];
  try {
    const raw = localStorage.getItem(`social_archive_data_${userId}`);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveArchivedPostsData(userId, posts) {
  if (!userId) return;
  try {
    localStorage.setItem(`social_archive_data_${userId}`, JSON.stringify(posts));
  } catch (err) {
    console.error("Failed to save archived posts data:", err);
  }
}

export default function ArchiveView({ currentUser, onRequireAuth, onImageClick, onPostUnarchived }) {
  const [archivedPosts, setArchivedPosts] = useState([]);
  const [expandedComments, setExpandedComments] = useState({});
  const [commentsByPost, setCommentsByPost] = useState({});
  const [loadingComments, setLoadingComments] = useState({});

  useEffect(() => {
    if (!currentUser?.id) return;
    loadArchive();
  }, [currentUser?.id]);

  function loadArchive() {
    const posts = getArchivedPostsData(currentUser.id);
    setArchivedPosts(posts);
  }

  function handleUnarchive(postId) {
    if (!window.confirm("Unarchive this tweet? It will be restored to your public profile and feed.")) return;

    // Remove from archived data
    const updated = archivedPosts.filter((p) => p.id !== postId);
    setArchivedPosts(updated);
    saveArchivedPostsData(currentUser.id, updated);

    // Remove from archived IDs
    const currentIds = getArchivedPostIds(currentUser.id);
    saveArchivedPostIds(currentUser.id, currentIds.filter((id) => id !== postId));

    if (onPostUnarchived) onPostUnarchived(postId);
  }

  async function toggleComments(postId) {
    const isOpen = Boolean(expandedComments[postId]);
    setExpandedComments((prev) => ({ ...prev, [postId]: !isOpen }));

    if (!isOpen && !commentsByPost[postId]) {
      setLoadingComments((prev) => ({ ...prev, [postId]: true }));
      try {
        const data = await fetchPostReplies(postId);
        setCommentsByPost((prev) => ({ ...prev, [postId]: data.replies || [] }));
      } catch (err) {
        console.error("Failed to load archive comments:", err);
      } finally {
        setLoadingComments((prev) => ({ ...prev, [postId]: false }));
      }
    }
  }

  if (!currentUser) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center", color: "#71767b" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>📦</div>
        <h2 style={{ color: "#e7e9ea", marginBottom: "8px" }}>Private Post Archive</h2>
        <p style={{ maxWidth: "340px", margin: "0 auto 20px auto", lineHeight: "1.5" }}>
          Sign in to view your private archive. Only you can see posts and comments you have archived.
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
        <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "800", color: "#e7e9ea" }}>📦 Archive</h2>
        <span style={{ fontSize: "13px", color: "#71767b" }}>
          @{currentUser.handle} · Only you can see your archived posts and replies
        </span>
      </div>

      {archivedPosts.length === 0 ? (
        <div style={{ padding: "60px 20px", textAlign: "center", color: "#71767b" }}>
          <div style={{ fontSize: "48px", marginBottom: "12px" }}>📦</div>
          <h3 style={{ color: "#e7e9ea", marginBottom: "8px" }}>No archived posts</h3>
          <p style={{ maxWidth: "360px", margin: "0 auto", lineHeight: "1.5" }}>
            When you archive your tweets, they will appear here. All existing comments and replies remain preserved inside your private archive!
          </p>
        </div>
      ) : (
        archivedPosts.map((post) => {
          const isCommentsOpen = Boolean(expandedComments[post.id]);
          const comments = commentsByPost[post.id] || [];
          const isLoading = Boolean(loadingComments[post.id]);

          return (
            <div key={post.id} style={{ borderBottom: "1px solid #2f3336", paddingBottom: "12px" }}>
              <div style={{ padding: "8px 16px 0 16px", display: "flex", justifyContent: "flex-end" }}>
                <button
                  onClick={() => handleUnarchive(post.id)}
                  style={{
                    background: "#202327",
                    border: "1px solid #536471",
                    color: "#eff3f4",
                    borderRadius: "999px",
                    padding: "4px 12px",
                    fontSize: "12px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                  title="Restore post to your public feed"
                >
                  ↩️ Unarchive (Put back on feed)
                </button>
              </div>

              <Tweet
                id={post.id}
                authorId={post.authorId}
                author={post.author}
                handle={post.handle}
                authorAvatar={post.authorAvatar}
                text={post.text}
                image={post.image}
                time={post.created_at}
                initialLikes={post.like_count}
                initialComments={post.comment_count}
                initialRetweets={post.retweet_count}
                initialLiked={post.liked_by_viewer}
                initialRetweeted={post.reposted_by_viewer}
                initialBookmarked={post.bookmarked_by_viewer}
                currentUser={currentUser}
                onRequireAuth={onRequireAuth}
                onImageClick={onImageClick}
                showActions={true}
              />

              {/* Preserved Comments & Replies Section */}
              <div style={{ padding: "0 16px", marginTop: "-8px" }}>
                <button
                  onClick={() => toggleComments(post.id)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#1d9bf0",
                    fontSize: "13px",
                    fontWeight: "bold",
                    cursor: "pointer",
                    padding: "6px 0",
                  }}
                >
                  {isCommentsOpen ? "▲ Hide Comments & Replies" : `💬 Preserved Comments & Replies (${post.comment_count ?? 0})`}
                </button>

                {isCommentsOpen && (
                  <div style={{ background: "#16181c", borderRadius: "12px", padding: "12px", marginTop: "8px" }}>
                    {isLoading ? (
                      <p style={{ color: "#71767b", fontSize: "13px", margin: 0 }}>Loading comments...</p>
                    ) : comments.length === 0 ? (
                      <p style={{ color: "#71767b", fontSize: "13px", margin: 0 }}>No comments on this post.</p>
                    ) : (
                      comments.map((comment) => (
                        <div
                          key={comment.id}
                          style={{
                            padding: "8px 0",
                            borderBottom: "1px solid #2f3336",
                            display: "flex",
                            gap: "10px",
                          }}
                        >
                          <img
                            src={comment.authorAvatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${comment.handle}`}
                            alt=""
                            style={{ width: "32px", height: "32px", borderRadius: "50%" }}
                          />
                          <div>
                            <div style={{ fontSize: "13px" }}>
                              <strong style={{ color: "#fff" }}>{comment.author}</strong>{" "}
                              <span style={{ color: "#71767b" }}>{comment.handle}</span>
                            </div>
                            <p style={{ margin: "4px 0 0 0", fontSize: "14px", color: "#e7e9ea" }}>{comment.text}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
