import { useState, useEffect } from "react";
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from "../api.js";

export default function NotificationsView({ onRefreshUnread }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadNotifications();
  }, []);

  async function loadNotifications() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNotifications();
      setNotifications(data.items || []);
      if (onRefreshUnread) onRefreshUnread();
    } catch (err) {
      console.error("Failed to load notifications:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleMarkRead(id) {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
      );
      if (onRefreshUnread) onRefreshUnread();
    } catch (err) {
      console.error("Failed to mark read:", err);
    }
  }

  async function handleMarkAllRead() {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
      if (onRefreshUnread) onRefreshUnread();
    } catch (err) {
      console.error("Failed to mark all read:", err);
    }
  }

  function getNotificationIcon(type) {
    switch (type) {
      case "like":
        return "💖";
      case "repost":
        return "🔁";
      case "reply":
        return "💬";
      case "follow":
        return "👥";
      default:
        return "🔔";
    }
  }

  function getNotificationText(notif) {
    const actorName = notif.actor?.displayName || `@${notif.actor?.handle}`;
    switch (notif.eventType) {
      case "like":
        return `${actorName} liked your post`;
      case "repost":
        return `${actorName} reposted your post`;
      case "reply":
        return `${actorName} replied to your post`;
      case "follow":
        return `${actorName} followed you`;
      default:
        return `Activity from ${actorName}`;
    }
  }

  return (
    <div style={{ padding: "16px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingBottom: "16px",
          borderBottom: "1px solid #2f3336",
          marginBottom: "16px",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "20px" }}>Notifications</h2>
        {notifications.some((n) => !n.isRead) && (
          <button
            onClick={handleMarkAllRead}
            style={{
              background: "#1d9bf0",
              color: "#fff",
              border: "none",
              padding: "6px 14px",
              borderRadius: "999px",
              fontSize: "13px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            ✓ Mark all read
          </button>
        )}
      </div>

      {loading && <p style={{ color: "#71767b" }}>Loading notifications...</p>}
      {error && <p style={{ color: "#f4212e" }}>Error: {error}</p>}

      {!loading && notifications.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px 20px", color: "#71767b" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🔔</div>
          <h3>No notifications yet</h3>
          <p style={{ fontSize: "14px" }}>
            When someone likes, reposts, replies to your posts, or follows you, you'll find it here!
          </p>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {notifications.map((notif) => (
          <div
            key={notif.id}
            onClick={() => !notif.isRead && handleMarkRead(notif.id)}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "14px",
              padding: "14px",
              borderRadius: "10px",
              background: notif.isRead ? "transparent" : "rgba(29, 155, 240, 0.08)",
              border: "1px solid",
              borderColor: notif.isRead ? "#2f3336" : "rgba(29, 155, 240, 0.3)",
              cursor: notif.isRead ? "default" : "pointer",
            }}
          >
            <span style={{ fontSize: "22px" }}>{getNotificationIcon(notif.eventType)}</span>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                <img
                  src={
                    notif.actor?.avatar?.smallUrl ||
                    `https://api.dicebear.com/7.x/avataaars/svg?seed=${notif.actor?.handle}`
                  }
                  alt=""
                  style={{ width: "24px", height: "24px", borderRadius: "50%" }}
                />
                <span style={{ fontWeight: "bold", fontSize: "15px" }}>
                  {notif.actor?.displayName}
                </span>
                <span style={{ color: "#71767b", fontSize: "13px" }}>
                  @{notif.actor?.handle}
                </span>
              </div>
              <p style={{ margin: "4px 0", fontSize: "14px", color: notif.isRead ? "#e7e9ea" : "#fff" }}>
                {getNotificationText(notif)}
              </p>
              <span style={{ fontSize: "12px", color: "#71767b" }}>
                {new Date(notif.createdAt).toLocaleDateString()}
              </span>
            </div>
            {!notif.isRead && (
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background: "#1d9bf0",
                  marginTop: "6px",
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
