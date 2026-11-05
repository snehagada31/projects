import { useState, useEffect, useRef } from "react";
import {
  fetchUserProfile,
  updateMyProfile,
  fetchUserPosts,
  deletePost,
  fetchActiveSessions,
  revokeSession,
  revokeOtherSessions,
  deactivateAccount,
} from "../api.js";
import Tweet from "./Tweet.jsx";
import {
  getArchivedPostIds,
  saveArchivedPostIds,
  getArchivedPostsData,
  saveArchivedPostsData,
} from "./ArchiveView.jsx";

function formatSessionDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  if (isNaN(d.getTime())) return isoStr;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function ProfileView({
  currentUser,
  onUserUpdated,
  onRequireAuth,
  onComment,
  onImageClick,
  onLogout,
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

  // Active Sessions Modal (corner ☰ button)
  const [showSessionsModal, setShowSessionsModal] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [revokingSessionId, setRevokingSessionId] = useState(null);
  const [revokingOthers, setRevokingOthers] = useState(false);
  const [deactivating, setDeactivating] = useState(false);

  const avatarInputRef = useRef(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  async function handleAvatarUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Please select a valid image file (JPG, PNG, WebP).");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert("File is too large. Please select an image under 5MB.");
      return;
    }

    setUploadingAvatar(true);
    const reader = new FileReader();
    reader.onloadend = async () => {
      try {
        const base64String = reader.result;
        const res = await updateMyProfile({
          avatar_small_url: base64String,
          avatar_large_url: base64String,
        });
        const updated = res.item;
        setProfile(updated);
        if (onUserUpdated) onUserUpdated(updated);
        alert("Avatar uploaded successfully! Saved as Base64 string in database.");
      } catch (err) {
        console.error("Avatar upload failed:", err);
        alert("Failed to upload avatar: " + err.message);
      } finally {
        setUploadingAvatar(false);
        if (avatarInputRef.current) avatarInputRef.current.value = "";
      }
    };
    reader.readAsDataURL(file);
  }

  useEffect(() => {
    if (!currentUser?.id) return;
    loadProfile();
  }, [currentUser?.id]);

  useEffect(() => {
    if (!currentUser?.id) return;
    loadUserPosts();
  }, [currentUser?.id, activeSubTab]);

  useEffect(() => {
    if (!currentUser?.id || !showSessionsModal) return;
    loadSessions();
  }, [currentUser?.id, showSessionsModal]);

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

  async function loadSessions() {
    setLoadingSessions(true);
    try {
      const data = await fetchActiveSessions();
      setSessions(data);
    } catch (err) {
      console.error("Failed to load active sessions:", err);
    } finally {
      setLoadingSessions(false);
    }
  }

  async function handleRevokeSession(sessionId, isCurrent) {
    if (isCurrent) {
      if (!window.confirm("Dismiss your current session? You will be immediately logged out.")) return;
    } else {
      if (!window.confirm("Are you sure you want to dismiss this session? That device will be immediately signed out.")) return;
    }

    setRevokingSessionId(sessionId);
    try {
      await revokeSession(sessionId);
      if (isCurrent) {
        if (onLogout) {
          await onLogout();
        } else {
          window.location.reload();
        }
      } else {
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        alert("Session dismissed successfully.");
      }
    } catch (err) {
      alert("Failed to dismiss session: " + err.message);
    } finally {
      setRevokingSessionId(null);
    }
  }

  async function handleRevokeOtherSessions() {
    if (!window.confirm("Are you sure you want to dismiss all other active sessions? All other devices will be signed out immediately.")) return;
    setRevokingOthers(true);
    try {
      await revokeOtherSessions();
      setSessions((prev) => prev.filter((s) => s.is_current || s.isCurrent));
      alert("All other sessions have been dismissed.");
    } catch (err) {
      alert("Failed to dismiss other sessions: " + err.message);
    } finally {
      setRevokingOthers(false);
    }
  }

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

  async function handleDeactivate() {
    const confirmed = window.confirm(
      "Are you sure you want to deactivate your account?\n\nYour profile will be hidden, all your login sessions will be dismissed, and you will be signed out immediately."
    );
    if (!confirmed) return;

    setDeactivating(true);
    try {
      await deactivateAccount();
      alert("Your account has been successfully deactivated.");
      if (onLogout) {
        onLogout();
      } else {
        localStorage.removeItem("social_auth_token");
        window.location.reload();
      }
    } catch (err) {
      alert("Failed to deactivate account: " + err.message);
    } finally {
      setDeactivating(false);
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

  const fallbackAvatar = `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser.handle}`;
  const avatarUrl =
    profile?.avatar?.largeUrl && !profile.avatar.largeUrl.startsWith("/fixtures")
      ? profile.avatar.largeUrl
      : fallbackAvatar;

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
        <div
          style={{
            position: "absolute",
            bottom: "-40px",
            left: "20px",
            width: "100px",
            height: "100px",
          }}
        >
          <img
            src={avatarUrl}
            onError={(e) => {
              e.currentTarget.onerror = null;
              e.currentTarget.src = fallbackAvatar;
            }}
            alt="Profile Avatar"
            style={{
              width: "100px",
              height: "100px",
              borderRadius: "50%",
              border: "4px solid #000",
              background: "#000",
              objectFit: "cover",
              display: "block",
            }}
          />
          <button
            type="button"
            onClick={() => avatarInputRef.current?.click()}
            disabled={uploadingAvatar}
            title="Upload new profile photo (Base64 in DB)"
            style={{
              position: "absolute",
              bottom: "0px",
              right: "0px",
              background: "#1d9bf0",
              border: "2px solid #000",
              borderRadius: "50%",
              width: "32px",
              height: "32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: uploadingAvatar ? "not-allowed" : "pointer",
              color: "#fff",
              fontSize: "14px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.6)",
            }}
          >
            {uploadingAvatar ? "⏳" : "📷"}
          </button>
        </div>

        <input
          type="file"
          ref={avatarInputRef}
          accept="image/*"
          style={{ display: "none" }}
          onChange={handleAvatarUpload}
        />

        <div style={{ position: "absolute", bottom: "-40px", right: "20px", display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            type="button"
            onClick={() => avatarInputRef.current?.click()}
            disabled={uploadingAvatar}
            title="Upload profile picture (Saved as Base64 in PostgreSQL)"
            style={{
              background: "#1d9bf0",
              border: "none",
              color: "#fff",
              fontWeight: "bold",
              borderRadius: "999px",
              padding: "8px 16px",
              cursor: uploadingAvatar ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "13px",
            }}
          >
            <span>📷</span>
            <span>{uploadingAvatar ? "Uploading..." : "Upload Photo"}</span>
          </button>

          <button
            onClick={() => setShowSessionsModal(true)}
            title="Active Login Sessions (Manage Devices)"
            style={{
              background: "#16181c",
              border: "1px solid #536471",
              color: "#e7e9ea",
              fontWeight: "600",
              borderRadius: "999px",
              padding: "8px 14px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "13px",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#1d9bf0")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#536471")}
          >
            <span style={{ fontSize: "16px", lineHeight: 1 }}>☰</span>
            <span>Sessions</span>
          </button>

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

          <div
            style={{
              marginTop: "16px",
              paddingTop: "16px",
              borderTop: "1px solid #2f3336",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div>
              <div style={{ color: "#f4212e", fontWeight: "600", fontSize: "14px" }}>Deactivate Account</div>
              <div style={{ color: "#71767b", fontSize: "12px" }}>Disable your profile and log out of all devices.</div>
            </div>
            <button
              type="button"
              onClick={handleDeactivate}
              disabled={deactivating}
              style={{
                background: "transparent",
                border: "1px solid #f4212e",
                color: "#f4212e",
                borderRadius: "999px",
                padding: "6px 14px",
                fontWeight: "600",
                fontSize: "13px",
                cursor: deactivating ? "not-allowed" : "pointer",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(244, 33, 46, 0.1)")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
            >
              {deactivating ? "Deactivating..." : "Deactivate Account"}
            </button>
          </div>
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

      {/* Sub-tabs: Posts / Replies / Reposts */}
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

      {/* User Posts / Replies List */}
      <div>
        {loadingPosts ? (
          <p style={{ textAlign: "center", color: "#71767b", padding: "20px" }}>Loading {activeSubTab}...</p>
        ) : (userPosts.filter((p) => !new Set(getArchivedPostIds(currentUser?.id)).has(p.id))).length === 0 ? (
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
          userPosts
            .filter((p) => !new Set(getArchivedPostIds(currentUser?.id)).has(p.id))
            .map((post) => (
            <div key={post.id} style={{ borderBottom: "1px solid #2f3336" }}>
              {activeSubTab === "replies" && (
                <div style={{ padding: "8px 16px 0 16px", fontSize: "13px", color: "#71767b", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>💬</span>
                  <span>
                    <strong style={{ color: "#e7e9ea" }}>{currentUser.displayName}</strong> replied to{" "}
                    <span style={{ color: "#1d9bf0", fontWeight: "bold" }}>
                      {post.replyToName && post.replyToHandle
                        ? `${post.replyToName} (@${post.replyToHandle.replace("@", "")})`
                        : post.replyToHandle
                        ? `@${post.replyToHandle.replace("@", "")}`
                        : post.reply_to_handle
                        ? `@${post.reply_to_handle.replace("@", "")}`
                        : (post.replyToName || "a post")}
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
                replyToHandle={post.replyToHandle || post.reply_to_handle}
                replyToName={post.replyToName || post.reply_to_name}
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

      {/* ========================================================= */}
      {/* CORNER ACTIVE SESSIONS MODAL (Opened via top ☰ button)     */}
      {/* ========================================================= */}
      {showSessionsModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.75)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
          onClick={() => setShowSessionsModal(false)}
        >
          <div
            style={{
              background: "#000",
              border: "1px solid #2f3336",
              borderRadius: "16px",
              width: "100%",
              maxWidth: "560px",
              maxHeight: "85vh",
              overflowY: "auto",
              padding: "24px",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "20px" }}>☰</span>
                <h2 style={{ margin: 0, fontSize: "20px", color: "#e7e9ea" }}>Active Login Sessions</h2>
              </div>
              <button
                onClick={() => setShowSessionsModal(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#71767b",
                  fontSize: "20px",
                  cursor: "pointer",
                  borderRadius: "50%",
                  width: "32px",
                  height: "32px",
                }}
              >
                ✕
              </button>
            </div>

            <p style={{ margin: "0 0 16px 0", fontSize: "13px", color: "#71767b", lineHeight: "1.4" }}>
              These devices and browsers currently have active access to your account. You can dismiss any session you do not recognize, or dismiss all other devices at once.
            </p>

            {sessions.filter((s) => !(s.is_current || s.isCurrent)).length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <button
                  onClick={handleRevokeOtherSessions}
                  disabled={revokingOthers}
                  style={{
                    background: "#f4212e",
                    color: "#fff",
                    border: "none",
                    borderRadius: "9999px",
                    padding: "8px 16px",
                    fontWeight: "bold",
                    fontSize: "13px",
                    cursor: revokingOthers ? "not-allowed" : "pointer",
                  }}
                >
                  {revokingOthers ? "Dismissing..." : "Dismiss All Other Sessions"}
                </button>
              </div>
            )}

            {loadingSessions ? (
              <p style={{ textAlign: "center", color: "#71767b", padding: "20px" }}>Loading active sessions...</p>
            ) : sessions.length === 0 ? (
              <div style={{ textAlign: "center", color: "#71767b", padding: "30px 20px" }}>
                <p>No active sessions found.</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {sessions.map((sess) => {
                  const isCurrent = Boolean(sess.is_current || sess.isCurrent);
                  return (
                    <div
                      key={sess.id}
                      style={{
                        background: "#16181c",
                        border: isCurrent ? "1px solid #1d9bf0" : "1px solid #2f3336",
                        borderRadius: "12px",
                        padding: "16px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: "12px",
                        flexWrap: "wrap",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <div
                          style={{
                            width: "42px",
                            height: "42px",
                            borderRadius: "50%",
                            background: isCurrent ? "rgba(29, 155, 240, 0.15)" : "#222",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "20px",
                          }}
                        >
                          {isCurrent ? "💻" : "📱"}
                        </div>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                            <span style={{ fontWeight: "bold", color: "#e7e9ea", fontSize: "15px" }}>
                              {isCurrent ? "This Device (Current Session)" : "Other Logged-in Device"}
                            </span>
                            {isCurrent && (
                              <span
                                style={{
                                  background: "#00ba7c",
                                  color: "#000",
                                  fontSize: "11px",
                                  fontWeight: "bold",
                                  padding: "2px 8px",
                                  borderRadius: "999px",
                                }}
                              >
                                ACTIVE NOW
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: "13px", color: "#71767b", marginTop: "4px" }}>
                            Signed in: <span style={{ color: "#d9d9d9" }}>{formatSessionDate(sess.created_at || sess.createdAt)}</span>
                          </div>
                          <div style={{ fontSize: "12px", color: "#536471", marginTop: "2px" }}>
                            Expires: {formatSessionDate(sess.expires_at || sess.expiresAt)} · Session: {sess.id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleRevokeSession(sess.id, isCurrent)}
                        disabled={revokingSessionId === sess.id}
                        style={{
                          background: "transparent",
                          border: "1px solid #f4212e",
                          color: "#f4212e",
                          borderRadius: "9999px",
                          padding: "6px 14px",
                          fontSize: "13px",
                          fontWeight: "bold",
                          cursor: revokingSessionId === sess.id ? "not-allowed" : "pointer",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = "rgba(244, 33, 46, 0.1)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                      >
                        {revokingSessionId === sess.id
                          ? "Dismissing..."
                          : isCurrent
                          ? "Dismiss & Log Out"
                          : "Dismiss / Revoke"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Account Danger Zone: Deactivate */}
            <div
              style={{
                marginTop: "24px",
                paddingTop: "16px",
                borderTop: "1px solid #2f3336",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "8px",
              }}
            >
              <div>
                <div style={{ color: "#f4212e", fontWeight: "600", fontSize: "14px" }}>Deactivate Account</div>
                <div style={{ color: "#71767b", fontSize: "12px" }}>Disable your profile and revoke all sessions.</div>
              </div>
              <button
                type="button"
                onClick={handleDeactivate}
                disabled={deactivating}
                style={{
                  background: "rgba(244, 33, 46, 0.1)",
                  border: "1px solid #f4212e",
                  color: "#f4212e",
                  borderRadius: "999px",
                  padding: "6px 14px",
                  fontWeight: "600",
                  cursor: deactivating ? "not-allowed" : "pointer",
                  fontSize: "13px",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(244, 33, 46, 0.2)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "rgba(244, 33, 46, 0.1)")}
              >
                {deactivating ? "Deactivating..." : "Deactivate Account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
