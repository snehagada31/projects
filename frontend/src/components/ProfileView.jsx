import { useState, useEffect } from "react";
import { fetchUserProfile, updateMyProfile } from "../api.js";

export default function ProfileView({ currentUser, onUserUpdated, onRequireAuth }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!currentUser) return;
    loadProfile();
  }, [currentUser]);

  async function loadProfile() {
    setLoading(true);
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
    </div>
  );
}
