import { useState, useEffect } from "react";
import { fetchUserProfile, updateMyProfile, fetchUserPosts, deletePost } from "../api.js";
import Tweet from "./Tweet.jsx";
import {
  getArchivedPostIds,
  saveArchivedPostIds,
  getArchivedPostsData,
  saveArchivedPostsData,
} from "./ArchiveView.jsx";

export default function ProfileView({
  currentUser,
  onUserUpdated,
  onRequireAuth,
  onComment,
  onImageClick,
}) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Sub-tab: "posts" | "replies"
  const [activeSubTab, setActiveSubTab] = useState("posts");
  const [userPosts, setUserPosts] = useState([]);
  const [loadingPosts, setLoadingPosts] = useState(false);

  useEffect(() => {
    if (!currentUser?.id) return;
    loadProfile();
  }, [currentUser?.id]);

  useEffect(() => {
    if (!currentUser?.id) return;
    loadUserPosts();
  }, [currentUser?.id, activeSubTab]);

  async function loadProfile() {
    if (!profile) setLoading(true);
    try {
      const data = await fetchUserProfile(currentUser.id);
      const item = data.item;
      setProfile(item);
      setDisplayName(item.displayName || "");
      setBio(item.bio || "");
    } catch (err) {
      console.error("Failed to load profile:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadUserPosts() {
    setLoadingPosts(true);
    try {
      const kind = activeSubTab === "replies" ? "reply" : "original";
      const posts = await fetchUserPosts(currentUser.id, kind);
      const archivedIds = new Set(getArchivedPostIds(currentUser.id));
      setUserPosts(posts.filter((p) => !archivedIds.has(p.id)));
    } catch (err) {
      console.error("Failed to load user posts:", err);
    } finally {
      setLoadingPosts(false);
    }
  }

  function handleArchivePost(postObj) {
    if (!currentUser) return;
    const currentPosts = getArchivedPostsData(currentUser.id);
    if (!currentPosts.some((p) => p.id === postObj.id)) {
      saveArchivedPostsData(currentUser.id, [postObj, ...currentPosts]);
    }
    const currentIds = getArchivedPostIds(currentUser.id);
    if (!currentIds.includes(postObj.id)) {
      saveArchivedPostIds(currentUser.id, [...currentIds, postObj.id]);
    }
    setUserPosts((prev) => prev.filter((p) => p.id !== postObj.id));
    alert("Post archived! You can view it anytime in your private Archive tab.");
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const data = await updateMyProfile({ displayName, bio });
      const updated = data.item;
      setProfile(updated);
      setEditing(false);
      if (onUserUpdated) onUserUpdated(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDeletePost(postId) {
    if (!window.confirm("Are you sure you want to delete this post?")) return;
    try {
      await deletePost(postId);
      setUserPosts((prev) => prev.filter((p) => p.id !== postId));
      // update postCount locally
      setProfile((prev) => prev ? { ...prev, postCount: Math.max(0, (prev.postCount || 1) - 1) } : prev);
    } catch (err) {
      alert("Failed to delete post: " + err.message);
    }
  }

  if (!currentUser) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center", color: "#71767b" }}>
        <h3>Sign In to View Your Profile</h3>
        <p>Manage your account, bio, and view your posts and followers.</p>
        <button
          onClick={onRequireAuth}
          style={{
            background: "#1d9bf0",
            color: "#fff",
            border: "none",
            padding: "10px 20px",
            borderRadius: "999px",
            fontWeight: "bold",
            cursor: "pointer",
            marginTop: "12px",
          }}
        >
          Sign In Now
        </button>
      </div>
    );
  }

  if (loading) {
    return <p style={{ padding: "20px", color: "#71767b" }}>Loading profile...</p>;
  }

  const avatarUrl =
    profile?.avatar?.largeUrl ||
    `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser.handle}`;

  return (
    <div style={{ padding: "16px" }}>
      {/* Banner */}
      <div
        style={{
          height: "140px",
          backgroundColor: "#333639",
          borderRadius: "12px",
          position: "relative",
          marginBottom: "60px",
        }}
      >
        <img
          src={avatarUrl}
          alt=""
          style={{
            width: "100px",
            height: "100px",
            borderRadius: "50%",
            border: "4px solid #000",
            position: "absolute",
            bottom: "-40px",
            left: "20px",
            background: "#000",
          }}
        />
        <div style={{ position: "absolute", bottom: "-40px", right: "20px" }}>
          {!editing ? (
            <button
              onClick={() => setEditing(true)}
              style={{
                background: "transparent",
                border: "1px solid #536471",
                color: "#fff",
                fontWeight: "bold",
                borderRadius: "999px",
                padding: "8px 16px",
                cursor: "pointer",
              }}
            >
              Edit Profile
            </button>
          ) : (
            <button
              onClick={() => setEditing(false)}
              style={{
                background: "transparent",
                border: "1px solid #536471",
                color: "#71767b",
                borderRadius: "999px",
                padding: "8px 16px",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ color: "#f4212e", marginBottom: "12px", fontSize: "14px" }}>
          Error: {error}
        </div>
      )}

      {editing ? (
        <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
          <div>
            <label style={{ fontSize: "13px", color: "#71767b" }}>Display Name</label>
            <input
              type="text"
              required
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              style={{
                width: "100%",
                padding: "8px",
                background: "#000",
                border: "1px solid #333",
                borderRadius: "6px",
                color: "#fff",
                marginTop: "4px",
              }}
            />
          </div>
          <div>
            <label style={{ fontSize: "13px", color: "#71767b" }}>Bio</label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              style={{
                width: "100%",
                padding: "8px",
                background: "#000",
                border: "1px solid #333",
                borderRadius: "6px",
                color: "#fff",
                marginTop: "4px",
              }}
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            style={{
              background: "#1d9bf0",
              color: "#fff",
              border: "none",
              borderRadius: "999px",
              padding: "10px",
              fontWeight: "bold",
              cursor: saving ? "not-allowed" : "pointer",
            }}
          >
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </form>
      ) : (
        <div style={{ marginBottom: "20px" }}>
          <h2 style={{ margin: "0 0 2px 0", fontSize: "22px" }}>{profile?.displayName}</h2>
          <span style={{ color: "#71767b", fontSize: "14px" }}>@{profile?.handle}</span>
          <p style={{ marginTop: "12px", fontSize: "15px", lineHeight: "1.4" }}>
            {profile?.bio || <span style={{ color: "#71767b", fontStyle: "italic" }}>No bio yet. Click "Edit Profile" to add one!</span>}
          </p>

          <div style={{ display: "flex", gap: "20px", marginTop: "16px", fontSize: "14px", color: "#71767b" }}>
            <span>
              <strong style={{ color: "#fff" }}>{profile?.followingCount ?? 0}</strong> Following
            </span>
            <span>
              <strong style={{ color: "#fff" }}>{profile?.followerCount ?? 0}</strong> Followers
            </span>
            <span>
              <strong style={{ color: "#fff" }}>{profile?.postCount ?? 0}</strong> Posts
            </span>
          </div>
        </div>
      )}

      {/* Sub-tabs: Posts / Replies */}
      <div style={{ display: "flex", borderBottom: "1px solid #2f3336", marginTop: "24px", marginBottom: "8px" }}>
        <button
          onClick={() => setActiveSubTab("posts")}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            borderBottom: activeSubTab === "posts" ? "4px solid #1d9bf0" : "4px solid transparent",
            color: activeSubTab === "posts" ? "#fff" : "#71767b",
            fontWeight: "bold",
            padding: "12px",
            cursor: "pointer",
            fontSize: "15px",
          }}
        >
          Posts ({profile?.postCount ?? userPosts.length})
        </button>
        <button
          onClick={() => setActiveSubTab("replies")}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            borderBottom: activeSubTab === "replies" ? "4px solid #1d9bf0" : "4px solid transparent",
            color: activeSubTab === "replies" ? "#fff" : "#71767b",
            fontWeight: "bold",
            padding: "12px",
            cursor: "pointer",
            fontSize: "15px",
          }}
        >
          Replies
        </button>
      </div>

      {/* User Posts List */}
      <div>
        {loadingPosts ? (
          <p style={{ textAlign: "center", color: "#71767b", padding: "20px" }}>Loading {activeSubTab}...</p>
        ) : userPosts.length === 0 ? (
          <div style={{ textAlign: "center", color: "#71767b", padding: "40px 20px" }}>
            <p style={{ fontSize: "16px", fontWeight: "bold", color: "#e7e9ea" }}>
              {activeSubTab === "posts" ? "No posts yet" : "No replies yet"}
            </p>
            <p style={{ fontSize: "14px", marginTop: "4px" }}>
              {activeSubTab === "posts"
                ? "When you publish tweets, they will appear here on your profile."
                : "Replies and comments you post will appear here."}
            </p>
          </div>
        ) : (
          userPosts.map((post) => (
            <div key={post.id} style={{ borderBottom: "1px solid #2f3336" }}>
              {activeSubTab === "replies" && (
                <div style={{ padding: "8px 16px 0 16px", fontSize: "13px", color: "#71767b", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>💬</span>
                  <span>
                    <strong style={{ color: "#e7e9ea" }}>{currentUser.displayName}</strong> replied to{" "}
                    <span style={{ color: "#1d9bf0", fontWeight: "bold" }}>
                      @{post.reply_to_handle ? post.reply_to_handle.replace("@", "") : "user"}
                    </span>
                  </span>
                </div>
              )}
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
                replyToHandle={post.reply_to_handle}
                isReply={activeSubTab === "replies"}
                canDelete={true}
                onDelete={() => handleDeletePost(post.id)}
                onComment={onComment ? () => onComment(post) : null}
                onImageClick={onImageClick}
                currentUser={currentUser}
                onRequireAuth={onRequireAuth}
                onArchive={handleArchivePost}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
