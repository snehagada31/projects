import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import RightPanel from "./components/RightPanel.jsx";
import Tweet from "./components/Tweet.jsx";
import ReplyModal from "./components/ReplyModal.jsx";
import ImageLightbox from "./components/ImageLightbox.jsx";
import AuthModal from "./components/AuthModal.jsx";
import NotificationsView from "./components/NotificationsView.jsx";
import ProfileView from "./components/ProfileView.jsx";
import BookmarksView from "./components/BookmarksView.jsx";
import ArchiveView, {
  getArchivedPostIds,
  saveArchivedPostIds,
  getArchivedPostsData,
  saveArchivedPostsData,
} from "./components/ArchiveView.jsx";
import {
  fetchFeed,
  createPost,
  deletePost,
  fetchPostReplies,
  searchPosts,
  fetchUsers,
  followUser,
  unfollowUser,
  fetchMe,
  logoutUser,
  fetchUnreadCount,
  uploadPostImage,
} from "./api.js";

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("home");
  const [unreadCount, setUnreadCount] = useState(0);

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
  const [exploreUsers, setExploreUsers] = useState([]);
  const [loadingExploreUsers, setLoadingExploreUsers] = useState(false);
  const [searching, setSearching] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);

  const [composerText, setComposerText] = useState("");
  const [composerImage, setComposerImage] = useState("");
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [showImageUrlInput, setShowImageUrlInput] = useState(false);
  const [isPosting, setIsPosting] = useState(false);

  const fileInputRef = useRef(null);
  const feedStatusRef = useRef(null);

  // Load feed batch (pagination)
  const loadNextBatch = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFeed(cursor, 10);
      const archivedIds = new Set(getArchivedPostIds(currentUser?.id));
      setLoadedPosts((prev) => {
        const existingIds = new Set(prev.map((p) => p.id));
        const newOnes = data.posts.filter((p) => !existingIds.has(p.id) && !archivedIds.has(p.id));
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
  }, [cursor, loading, hasMore, currentUser?.id]);

  // Refresh feed from beginning (e.g., when logging in, switching account, or following someone)
  const refreshFeed = useCallback(async () => {
    setLoading(true);
    setError(null);
    setCursor(null);
    try {
      const data = await fetchFeed(null, 10);
      const archivedIds = new Set(getArchivedPostIds(currentUser?.id));
      setLoadedPosts((data.posts || []).filter((p) => !archivedIds.has(p.id)));
      setHasMore(data.has_more);
      setCursor(data.next_cursor ?? null);
    } catch (err) {
      console.error("Feed refresh failed:", err);
      setError("Could not connect to backend. Please make sure backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }, [currentUser?.id]);

  function handleArchiveFromFeed(postObj) {
    if (!currentUser) return;
    const currentPosts = getArchivedPostsData(currentUser.id);
    if (!currentPosts.some((p) => p.id === postObj.id)) {
      saveArchivedPostsData(currentUser.id, [postObj, ...currentPosts]);
    }
    const currentIds = getArchivedPostIds(currentUser.id);
    if (!currentIds.includes(postObj.id)) {
      saveArchivedPostIds(currentUser.id, [...currentIds, postObj.id]);
    }
    setLoadedPosts((prev) => prev.filter((p) => p.id !== postObj.id));
    alert("Post archived! You can view it anytime in your private Archive tab.");
  }

  // Update notification count
  const refreshUnreadCount = useCallback(async () => {
    try {
      const count = await fetchUnreadCount();
      setUnreadCount(count);
    } catch {
      // Ignored if unauthenticated
    }
  }, []);

  // On mount: check auth session, fetch initial feed, and fetch notifications count once
  useEffect(() => {
    async function init() {
      try {
        const me = await fetchMe();
        if (me) {
          setCurrentUser(me);
          try {
            const count = await fetchUnreadCount();
            setUnreadCount(count);
          } catch {}
        }
      } catch (e) {
        console.error("fetchMe error on init:", e);
      }
      refreshFeed();
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Periodically refresh notification badge every 10 seconds when logged in
  useEffect(() => {
    if (!currentUser?.id) return;
    refreshUnreadCount();
    const interval = setInterval(() => {
      refreshUnreadCount();
    }, 10000);
    return () => clearInterval(interval);
  }, [currentUser?.id, refreshUnreadCount]);

  // Infinite scroll observer
  useEffect(() => {
    if (activeTab !== "home") return;
    const el = feedStatusRef.current;
    if (!el || !hasMore || loading) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        loadNextBatch();
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadNextBatch, hasMore, loading, activeTab]);

  // Load explore users when on Explore tab
  const loadExploreUsers = useCallback(async () => {
    setLoadingExploreUsers(true);
    try {
      const users = await fetchUsers();
      setExploreUsers(users);
    } catch (err) {
      console.error("Failed to load explore users:", err);
    } finally {
      setLoadingExploreUsers(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "explore") {
      loadExploreUsers();
    }
  }, [activeTab, loadExploreUsers, currentUser]);

  // Pre-load replies for posts that have comments
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

  // Toggle follow user
  async function handleToggleFollowUser(user) {
    if (!currentUser) {
      setIsAuthModalOpen(true);
      return;
    }

    const isFollowing = user.following;
    // Optimistic update in matched users and explore users
    setMatchedUsers((prev) =>
      prev.map((u) => (u.id === user.id ? { ...u, following: !isFollowing } : u))
    );
    setExploreUsers((prev) =>
      prev.map((u) => (u.id === user.id ? { ...u, following: !isFollowing } : u))
    );

    try {
      if (isFollowing) {
        await unfollowUser(user.id);
      } else {
        await followUser(user.id);
      }
      // Refresh feed in background so new follows immediately populate personalized feed
      refreshFeed();
    } catch (err) {
      console.error("Failed to toggle follow:", err);
      setMatchedUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, following: isFollowing } : u))
      );
      setExploreUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, following: isFollowing } : u))
      );
    }
  }

  // Handle post creation with optional image
  async function handleCreatePost(e) {
    e.preventDefault();
    if (!currentUser) {
      setIsAuthModalOpen(true);
      return;
    }
    const rawText = composerText.trim();
    // If an image is provided without text, default caption so backend length validation succeeds
    const text = rawText || (composerImage ? "📷" : "");
    if (!text || isPosting) return;

    setIsPosting(true);
    try {
      const media = composerImage
        ? [
            {
              altText: rawText ? `Image for: ${rawText.slice(0, 40)}` : "Tweet image",
              smallUrl: composerImage,
              largeUrl: composerImage,
              width: 800,
              height: 600,
            },
          ]
        : null;

      const res = await createPost({ kind: "original", text, media });
      const item = res.item;
      const newPost = {
        id: item.id,
        authorId: item.author?.id || currentUser.id,
        author: item.author?.displayName || currentUser.displayName,
        handle: "@" + (item.author?.handle || currentUser.handle),
        authorAvatar: item.author?.avatar?.smallUrl || currentUser.avatar?.smallUrl,
        text: item.text,
        image: item.media?.[0]?.largeUrl || item.media?.[0]?.smallUrl || composerImage || null,
        like_count: 0,
        comment_count: 0,
        retweet_count: 0,
        liked_by_viewer: false,
        reposted_by_viewer: false,
        created_at: item.createdAt,
      };
      setLoadedPosts((prev) => [newPost, ...prev]);
      setComposerText("");
      setComposerImage("");
      setShowImageUrlInput(false);
    } catch (err) {
      alert("Failed to create post: " + err.message);
    } finally {
      setIsPosting(false);
    }
  }

  async function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploadingImage(true);
    try {
      const url = await uploadPostImage(file);
      setComposerImage(url);
      setShowImageUrlInput(false);
    } catch (err) {
      alert("Failed to upload image: " + err.message);
    } finally {
      setIsUploadingImage(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  // Handle post deletion
  async function handleDeletePost(postId) {
    if (!window.confirm("Are you sure you want to delete this post?")) return;
    try {
      await deletePost(postId);
      setLoadedPosts((prev) => prev.filter((p) => p.id !== postId));
    } catch (err) {
      alert("Failed to delete post: " + err.message);
    }
  }

  // Toggle replies expand / collapse
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
    if (!currentUser) {
      setIsAuthModalOpen(true);
      return;
    }
    setReplyingTo({ targetId: postId, handle });
    if (!expandedReplies[postId]) {
      toggleReplies(postId);
    }
  }

  // Submit reply
  async function submitReply(text) {
    const targetPostId = replyingTo?.targetId;
    if (!targetPostId) return;

    if (!currentUser) {
      setIsAuthModalOpen(true);
      return;
    }

    try {
      const res = await createPost({ kind: "reply", text, replyToId: targetPostId });
      const item = res.item;
      const newReply = {
        id: item.id,
        authorId: item.author?.id || currentUser.id,
        author: item.author?.displayName || currentUser.displayName,
        handle: "@" + (item.author?.handle || currentUser.handle),
        authorAvatar: item.author?.avatar?.smallUrl || currentUser.avatar?.smallUrl,
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

  // Handle reply deletion
  async function handleDeleteReply(postId, replyId) {
    if (!window.confirm("Are you sure you want to delete this reply?")) return;
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

  // Auth callbacks
  function handleAuthSuccess(user) {
    setCurrentUser(user);
    refreshFeed();
    refreshUnreadCount();
  }

  async function handleLogout() {
    await logoutUser();
    setCurrentUser(null);
    setUnreadCount(0);
    refreshFeed();
  }

  const visiblePosts = searchQuery.trim() && searchResults !== null ? searchResults : loadedPosts;

  return (
    <div className="app-layout">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
          if (tab === "home") {
            setSearchQuery("");
            setSearchResults(null);
          }
        }}
        currentUser={currentUser}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
        unreadCount={unreadCount}
      />

      {/* Main Content Area */}
      <main className="feed">
        {/* Dynamic Header */}
        <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "20px", fontWeight: "800" }}>
              {activeTab === "home" && (currentUser ? "Home · Following" : "Home · Global Feed")}
              {activeTab === "explore" && "Explore & Discover"}
              {activeTab === "notifications" && "Notifications"}
              {activeTab === "bookmarks" && "Bookmarks"}
              {activeTab === "profile" && "Profile"}
            </h1>
            {activeTab === "home" && (
              <span style={{ fontSize: "12px", color: "#71767b" }}>
                {currentUser
                  ? `Logged in as @${currentUser.handle} (Personalized feed)`
                  : "Guest mode (Public feed) — Sign in to interact"}
              </span>
            )}
          </div>
          {!currentUser && (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              style={{
                background: "#1d9bf0",
                color: "white",
                border: "none",
                borderRadius: "9999px",
                padding: "6px 14px",
                fontSize: "13px",
                fontWeight: "700",
                cursor: "pointer",
              }}
            >
              Sign In
            </button>
          )}
        </header>

        {/* ============================================================== */}
        {/* TAB: NOTIFICATIONS VIEW                                       */}
        {/* ============================================================== */}
        {activeTab === "notifications" && (
          currentUser ? (
            <NotificationsView onRefreshUnread={refreshUnreadCount} />
          ) : (
            <div style={{ padding: "40px 20px", textAlign: "center", color: "#71767b" }}>
              <h3>Sign in to see your notifications</h3>
              <p>Stay up to date with likes, reposts, replies, and new followers.</p>
              <button
                onClick={() => setIsAuthModalOpen(true)}
                style={{
                  marginTop: "16px",
                  background: "#1d9bf0",
                  color: "#fff",
                  border: "none",
                  borderRadius: "9999px",
                  padding: "10px 24px",
                  fontWeight: "bold",
                  cursor: "pointer",
                }}
              >
                Sign In / Select Account
              </button>
            </div>
          )
        )}

        {/* ============================================================== */}
        {/* TAB: ARCHIVE VIEW                                             */}
        {/* ============================================================== */}
        {activeTab === "archive" && (
          <ArchiveView
            currentUser={currentUser}
            onRequireAuth={() => setIsAuthModalOpen(true)}
            onImageClick={setLightboxImage}
            onPostUnarchived={() => refreshFeed()}
          />
        )}

        {/* ============================================================== */}
        {/* TAB: BOOKMARKS VIEW (PY-P1-02)                                */}
        {/* ============================================================== */}
        {activeTab === "bookmarks" && (
          <BookmarksView
            currentUser={currentUser}
            onRequireAuth={() => setIsAuthModalOpen(true)}
            onComment={openReplyModal}
            onImageClick={setLightboxImage}
          />
        )}

        {/* ============================================================== */}
        {/* TAB: PROFILE VIEW                                             */}
        {/* ============================================================== */}
        {activeTab === "profile" && (
          <ProfileView
            currentUser={currentUser}
            onUserUpdated={(updated) => setCurrentUser(updated)}
            onRequireAuth={() => setIsAuthModalOpen(true)}
            onComment={openReplyModal}
            onImageClick={setLightboxImage}
          />
        )}

        {/* ============================================================== */}
        {/* TAB: EXPLORE VIEW                                             */}
        {/* ============================================================== */}
        {activeTab === "explore" && (
          <div>
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #2f3336" }}>
              <input
                type="text"
                placeholder="Search people or posts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: "100%",
                  background: "#202327",
                  border: "1px solid #333",
                  borderRadius: "9999px",
                  padding: "10px 16px",
                  color: "#e7e9ea",
                  outline: "none",
                  fontSize: "15px",
                }}
              />
            </div>

            {/* People Discovery / Search Results */}
            <div style={{ padding: "16px", borderBottom: "1px solid #2f3336" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "12px", color: "#e7e9ea" }}>
                {searchQuery.trim() ? "Matching People" : "Discover Creators"}
              </h2>

              {loadingExploreUsers && <div style={{ color: "#71767b" }}>Loading users...</div>}

              {(searchQuery.trim() ? matchedUsers : exploreUsers).map((user) => (
                <div
                  key={user.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "12px 0",
                    borderBottom: "1px solid #222",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <img
                      src={
                        user.avatar?.smallUrl ||
                        `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(user.handle || user.displayName)}`
                      }
                      alt=""
                      style={{ width: "48px", height: "48px", borderRadius: "50%", background: "#222" }}
                    />
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "15px", color: "#e7e9ea" }}>
                        {user.displayName}
                        {currentUser?.id === user.id && (
                          <span style={{ marginLeft: "6px", fontSize: "11px", color: "#1d9bf0" }}>(You)</span>
                        )}
                      </div>
                      <div style={{ color: "#71767b", fontSize: "13px" }}>@{user.handle}</div>
                      {user.bio && <div style={{ color: "#e7e9ea", fontSize: "13px", marginTop: "4px" }}>{user.bio}</div>}
                    </div>
                  </div>

                  {currentUser?.id !== user.id && (
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
                  )}
                </div>
              ))}
            </div>

            {/* Post Search Results */}
            {searchQuery.trim() && searchResults && (
              <div style={{ padding: "16px 0" }}>
                <h2 style={{ fontSize: "18px", fontWeight: "700", padding: "0 16px 12px 16px", color: "#e7e9ea" }}>
                  Matching Posts ({searchResults.length})
                </h2>
                {searchResults.map((post) => (
                  <Tweet
                    key={post.id}
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
                    initialBookmarked={post.bookmarked_by_viewer}
                    replyToHandle={post.reply_to_handle}
                    currentUser={currentUser}
                    onRequireAuth={() => setIsAuthModalOpen(true)}
                    onArchive={handleArchiveFromFeed}
                    canDelete={
                      currentUser &&
                      (post.authorId === currentUser.id ||
                        post.handle === `@${currentUser.handle}` ||
                        post.handle === currentUser.handle)
                    }
                    onDelete={() => handleDeletePost(post.id)}
                    onComment={() => openReplyModal(post.id, post.handle)}
                    onImageClick={setLightboxImage}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB: HOME FEED                                                */}
        {/* ============================================================== */}
        {activeTab === "home" && (
          <>
            {/* Tweet Composer for Authenticated Users */}
            {currentUser ? (
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
                <div style={{ display: "flex", gap: "12px" }}>
                  <img
                    src={
                      currentUser.avatar?.smallUrl ||
                      `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser.handle}`
                    }
                    alt=""
                    style={{ width: "40px", height: "40px", borderRadius: "50%" }}
                  />
                  <div style={{ flex: 1 }}>
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

                    {/* Image Upload Status */}
                    {isUploadingImage && (
                      <div
                        style={{
                          padding: "16px",
                          textAlign: "center",
                          color: "#1d9bf0",
                          background: "#16181c",
                          borderRadius: "16px",
                          marginBottom: "10px",
                          border: "1px dashed #1d9bf0",
                          fontSize: "14px",
                        }}
                      >
                        ⏳ Uploading image from computer...
                      </div>
                    )}

                    {/* Image Preview inside Composer */}
                    {composerImage && (
                      <div
                        style={{
                          position: "relative",
                          marginBottom: "12px",
                          borderRadius: "16px",
                          overflow: "hidden",
                          maxHeight: "300px",
                          border: "1px solid #2f3336",
                        }}
                      >
                        <img
                          src={composerImage}
                          alt="Attached media"
                          style={{
                            width: "100%",
                            maxHeight: "300px",
                            objectFit: "cover",
                            display: "block",
                          }}
                        />
                        <button
                          type="button"
                          onClick={() => setComposerImage("")}
                          title="Remove image"
                          style={{
                            position: "absolute",
                            top: "8px",
                            right: "8px",
                            background: "rgba(15, 20, 25, 0.75)",
                            color: "#fff",
                            border: "none",
                            borderRadius: "50%",
                            width: "32px",
                            height: "32px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            cursor: "pointer",
                            fontSize: "16px",
                            backdropFilter: "blur(4px)",
                          }}
                        >
                          ✕
                        </button>
                      </div>
                    )}

                    {/* Optional URL Input Popover/Bar */}
                    {showImageUrlInput && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                          background: "#16181c",
                          padding: "12px",
                          borderRadius: "12px",
                          border: "1px solid #2f3336",
                          marginBottom: "12px",
                        }}
                      >
                        <div style={{ display: "flex", gap: "8px" }}>
                          <input
                            type="url"
                            placeholder="Paste image URL (https://...)"
                            value={composerImage}
                            onChange={(e) => setComposerImage(e.target.value)}
                            style={{
                              flex: 1,
                              background: "#000",
                              border: "1px solid #333",
                              borderRadius: "8px",
                              padding: "8px 12px",
                              color: "#fff",
                              fontSize: "14px",
                              outline: "none",
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => setShowImageUrlInput(false)}
                            style={{
                              background: "#1d9bf0",
                              color: "#fff",
                              border: "none",
                              borderRadius: "8px",
                              padding: "8px 14px",
                              cursor: "pointer",
                              fontSize: "13px",
                              fontWeight: "bold",
                            }}
                          >
                            Done
                          </button>
                        </div>
                        {/* Quick Presets */}
                        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
                          <span style={{ fontSize: "12px", color: "#71767b" }}>Quick sample:</span>
                          {[
                            { label: "🌄 Nature", url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800" },
                            { label: "💻 Tech", url: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800" },
                            { label: "☕ Coffee", url: "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800" },
                            { label: "🐱 Cat", url: "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800" },
                            { label: "🌃 City", url: "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?w=800" },
                          ].map((sample) => (
                            <button
                              key={sample.label}
                              type="button"
                              onClick={() => {
                                setComposerImage(sample.url);
                                setShowImageUrlInput(false);
                              }}
                              style={{
                                background: "#202327",
                                border: "1px solid #333",
                                borderRadius: "999px",
                                color: "#e7e9ea",
                                padding: "3px 10px",
                                fontSize: "12px",
                                cursor: "pointer",
                              }}
                            >
                              {sample.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Hidden File Input for Image Upload */}
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  onChange={handleFileSelect}
                  style={{ display: "none" }}
                />

                {/* Bottom Toolbar */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingLeft: "52px",
                  }}
                >
                  <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    {/* Add Image Button (File Picker) */}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      title="Upload image from computer"
                      disabled={isPosting || isUploadingImage}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "#1d9bf0",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "14px",
                        padding: "6px 10px",
                        borderRadius: "999px",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(29, 155, 240, 0.1)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <span style={{ fontSize: "16px" }}>🖼️</span>
                      <span style={{ fontSize: "13px", fontWeight: "600" }}>Upload Image</span>
                    </button>

                    {/* Image URL Button */}
                    <button
                      type="button"
                      onClick={() => setShowImageUrlInput(!showImageUrlInput)}
                      title="Add image via link or sample"
                      style={{
                        background: "transparent",
                        border: "none",
                        color: showImageUrlInput ? "#fff" : "#1d9bf0",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "14px",
                        padding: "6px 10px",
                        borderRadius: "999px",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(29, 155, 240, 0.1)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <span style={{ fontSize: "16px" }}>🔗</span>
                      <span style={{ fontSize: "13px", fontWeight: "600" }}>Image URL</span>
                    </button>
                  </div>

                  <button
                    type="submit"
                    disabled={(!composerText.trim() && !composerImage) || isPosting || isUploadingImage}
                    style={{
                      background: "#1d9bf0",
                      color: "white",
                      border: "none",
                      borderRadius: "9999px",
                      padding: "8px 22px",
                      fontSize: "15px",
                      fontWeight: "700",
                      cursor: (composerText.trim() || composerImage) && !isPosting && !isUploadingImage ? "pointer" : "default",
                      opacity: (composerText.trim() || composerImage) && !isPosting && !isUploadingImage ? 1 : 0.5,
                    }}
                  >
                    {isPosting ? "Posting..." : "Post"}
                  </button>
                </div>
              </form>
            ) : (
              /* Guest Banner */
              <div
                style={{
                  padding: "16px",
                  margin: "12px 16px",
                  background: "#16181c",
                  borderRadius: "16px",
                  border: "1px solid #2f3336",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{ fontWeight: "700", fontSize: "15px", color: "#e7e9ea" }}>
                    👋 Welcome! You are viewing the Public Feed in Guest Mode.
                  </div>
                  <div style={{ fontSize: "13px", color: "#71767b", marginTop: "4px" }}>
                    Sign in or select a demo account to like, repost, reply, and follow creators.
                  </div>
                </div>
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  style={{
                    background: "#eff3f4",
                    color: "#0f1419",
                    border: "none",
                    borderRadius: "9999px",
                    padding: "8px 18px",
                    fontSize: "14px",
                    fontWeight: "700",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  Sign In / Switch User
                </button>
              </div>
            )}

            {/* Posts feed */}
            <section className="feed-posts">
              {visiblePosts.map((post) => {
                const replies = repliesByPost[post.id] || [];
                const isExpanded = expandedReplies[post.id];

                return (
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
                      initialBookmarked={post.bookmarked_by_viewer}
                      replyToHandle={post.reply_to_handle}
                      currentUser={currentUser}
                      onRequireAuth={() => setIsAuthModalOpen(true)}
                      onArchive={handleArchiveFromFeed}
                      canDelete={
                        currentUser &&
                        (post.authorId === currentUser.id ||
                          post.handle === `@${currentUser.handle}` ||
                          post.handle === currentUser.handle)
                      }
                      onDelete={() => handleDeletePost(post.id)}
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
                          {isExpanded
                            ? "Hide replies"
                            : `View ${post.comment_count} ${post.comment_count === 1 ? "reply" : "replies"}`}
                        </button>
                      </div>
                    )}

                    {/* Rendered replies */}
                    {isExpanded && (
                      <div
                        className="post-replies"
                        style={{ paddingLeft: "40px", borderLeft: "2px solid #2f3336", marginLeft: "28px" }}
                      >
                        {replies.map((reply) => (
                          <Tweet
                            key={reply.id}
                            id={reply.id}
                            author={reply.author}
                            handle={reply.handle}
                            authorAvatar={reply.authorAvatar}
                            text={reply.text}
                            time={reply.created_at}
                            isReply
                            showActions={false}
                            currentUser={currentUser}
                            onRequireAuth={() => setIsAuthModalOpen(true)}
                            canDelete={
                              currentUser &&
                              (reply.authorId === currentUser.id ||
                                reply.handle === `@${currentUser.handle}` ||
                                reply.handle === currentUser.handle)
                            }
                            onDelete={() => handleDeleteReply(post.id, reply.id)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Empty State when personalized feed has 0 posts */}
              {!loading && visiblePosts.length === 0 && (
                <div style={{ padding: "40px 20px", textAlign: "center", color: "#71767b" }}>
                  <h3 style={{ color: "#e7e9ea", marginBottom: "8px" }}>Your feed is quiet!</h3>
                  <p style={{ maxWidth: "360px", margin: "0 auto 16px auto", lineHeight: "1.5" }}>
                    {currentUser
                      ? "You aren't following anyone with recent posts yet. Explore creators to follow and build your personalized feed."
                      : "No posts found in the public feed."}
                  </p>
                  <button
                    onClick={() => setActiveTab("explore")}
                    style={{
                      background: "#1d9bf0",
                      color: "white",
                      border: "none",
                      borderRadius: "9999px",
                      padding: "8px 20px",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    Discover People to Follow
                  </button>
                </div>
              )}

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
              {!loading && !error && (
                <p
                  ref={feedStatusRef}
                  className="feed-status"
                  style={{ textAlign: "center", padding: "16px", color: "#71767b" }}
                >
                  {hasMore ? "Scroll for more" : "You've reached the end"}
                </p>
              )}
            </section>
          </>
        )}
      </main>

      {/* Right Panel */}
      <RightPanel
        searchQuery={searchQuery}
        onSearchChange={(q) => {
          setSearchQuery(q);
          if (q.trim() && activeTab !== "explore") {
            setActiveTab("explore");
          }
        }}
        currentUser={currentUser}
        onRequireAuth={() => setIsAuthModalOpen(true)}
        onFollowChange={refreshFeed}
      />

      {/* Modals */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      <ReplyModal
        replyingTo={replyingTo}
        onClose={() => setReplyingTo(null)}
        onSubmit={submitReply}
      />

      <ImageLightbox src={lightboxImage} onClose={() => setLightboxImage(null)} />
    </div>
  );
}
