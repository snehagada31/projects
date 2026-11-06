import { useState, useEffect } from "react";
import { fetchUsers, fetchUserSuggestions, followUser, unfollowUser, fetchTrendingTopics } from "../api.js";

const DEFAULT_TRENDS = [
  { category: "Technology · Trending", title: "#AsyncPython", meta: "12.4K posts" },
  { category: "Programming · Trending", title: "#FastAPI", meta: "8,201 posts" },
  { category: "Trending in India", title: "#100DaysOfCode", meta: "45.2K posts" },
];

export default function RightPanel({ searchQuery, onSearchChange, currentUser = null, onRequireAuth = null, onFollowChange = null }) {
  const [users, setUsers] = useState([]);
  const [trends, setTrends] = useState(DEFAULT_TRENDS);

  useEffect(() => {
    fetchTrendingTopics()
      .then((data) => {
        if (data?.trends && data.trends.length > 0) {
          setTrends(data.trends);
        }
      })
      .catch((err) => console.error("Failed to load trending topics:", err));
  }, []);

  useEffect(() => {
    fetchUserSuggestions(5)
      .then((data) => {
        if (data && data.length > 0) {
          setUsers(data);
        } else {
          return fetchUsers().then((fallback) => setUsers(fallback));
        }
      })
      .catch(() => {
        fetchUsers()
          .then((data) => setUsers(data))
          .catch((err) => console.error("Failed to load users for follow suggestions:", err));
      });
  }, [currentUser]);

  async function handleToggleFollow(user) {
    if (!currentUser && onRequireAuth) {
      onRequireAuth();
      return;
    }

    const isFollowing = user.following;
    // Optimistic update
    setUsers((prev) =>
      prev.map((u) => (u.id === user.id ? { ...u, following: !isFollowing } : u))
    );

    try {
      if (isFollowing) {
        await unfollowUser(user.id);
      } else {
        await followUser(user.id);
      }
      if (onFollowChange) onFollowChange();
    } catch (err) {
      console.error("Failed to toggle follow:", err);
      // Rollback
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, following: isFollowing } : u))
      );
    }
  }

  return (
    <aside className="right-panel">
      <div className="search-bar">
        <span className="search-bar__icon">🔍</span>
        <input
          type="text"
          placeholder="Search"
          aria-label="Search"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="right-panel__box">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
          <h2 style={{ margin: 0, fontSize: "18px" }}>What's happening</h2>
          <span
            style={{
              fontSize: "11px",
              fontWeight: "700",
              background: "rgba(29, 155, 240, 0.15)",
              color: "#1d9bf0",
              padding: "2px 8px",
              borderRadius: "999px",
              letterSpacing: "0.5px",
            }}
          >
            ● LIVE NEWS
          </span>
        </div>
        {trends.map((t) => (
          <div
            className="trend"
            key={t.title}
            onClick={() => {
              if (t.url) {
                window.open(t.url, "_blank", "noopener,noreferrer");
              } else if (onSearchChange) {
                onSearchChange(t.title);
              }
            }}
            style={{ cursor: "pointer" }}
            title={t.url ? `Read full article: ${t.title}` : `Search posts for ${t.title}`}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="trend__category">{t.category}</span>
              {t.url && <span style={{ fontSize: "12px", color: "#71767b" }}>↗</span>}
            </div>
            <span className="trend__title" style={{ fontSize: "14px", lineHeight: "1.3", margin: "2px 0 4px" }}>
              {t.title}
            </span>
            <span className="trend__meta">{t.meta}</span>
          </div>
        ))}
        <a
          href="#"
          className="show-more"
          onClick={(e) => {
            e.preventDefault();
            if (trends[0]?.url) {
              window.open("https://news.ycombinator.com", "_blank", "noopener,noreferrer");
            } else if (trends[0] && onSearchChange) {
              onSearchChange(trends[0].title);
            }
          }}
        >
          Explore more live news →
        </a>
      </div>

      <div className="right-panel__box">
        <h2>Who to follow</h2>
        {users.slice(0, 4).map((p) => (
          <div className="follow-suggestion" key={p.id}>
            <img
              className="avatar avatar--sm"
              src={
                p.avatar?.smallUrl && !p.avatar.smallUrl.startsWith("/fixtures")
                  ? p.avatar.smallUrl
                  : `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(p.handle || p.displayName)}`
              }
              alt=""
              onError={(e) => {
                e.currentTarget.onerror = null;
                e.currentTarget.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(p.handle || p.displayName)}`;
              }}
            />
            <div className="tweet-author-info">
              <span>{p.displayName}</span>
              <span>@{p.handle}</span>
              {p.reason && (
                <span style={{ fontSize: "11px", color: "#1d9bf0", marginTop: "2px" }}>
                  ★ {p.reason}
                </span>
              )}
            </div>
            <button
              className={`follow-btn${p.following ? " following" : ""}`}
              onClick={() => handleToggleFollow(p)}
              style={{
                background: p.following ? "transparent" : "#eff3f4",
                color: p.following ? "#eff3f4" : "#0f1419",
                border: p.following ? "1px solid #536471" : "none",
                borderRadius: "9999px",
                padding: "6px 16px",
                fontWeight: "700",
                fontSize: "14px",
                cursor: "pointer",
              }}
            >
              {p.following ? "Following" : "Follow"}
            </button>
          </div>
        ))}
        <a href="#" className="show-more">Show more</a>
      </div>

      <footer className="right-panel__footer">
        <a href="#">Terms</a>
        <a href="#">Privacy</a>
        <a href="#">Cookies</a>
        <a href="#">Accessibility</a>
        <a href="#">More</a>
        <span>&copy; 2026 Social Feed</span>
      </footer>
    </aside>
  );
}
