export default function Sidebar({
  activeTab = "home",
  onSelectTab,
  currentUser = null,
  onOpenAuthModal,
  onLogout,
  unreadCount = 0,
}) {
  const navItems = [
    { icon: "🏠", label: "Home", id: "home" },
    { icon: "🔍", label: "Explore", id: "explore" },
    { icon: "🔔", label: "Notifications", id: "notifications", badge: unreadCount },
    { icon: "👤", label: "Profile", id: "profile" },
  ];

  return (
    <nav className="sidebar" aria-label="Main navigation">
      <div className="sidebar__logo" onClick={() => onSelectTab && onSelectTab("home")} style={{ cursor: "pointer" }}>
        𝕏
      </div>

      <ul className="sidebar__nav">
        {navItems.map((item) => (
          <li key={item.id}>
            <a
              href="#"
              className={activeTab === item.id ? "active" : ""}
              onClick={(e) => {
                e.preventDefault();
                if (onSelectTab) onSelectTab(item.id);
              }}
              style={{ position: "relative" }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge > 0 && (
                <span
                  style={{
                    backgroundColor: "#1d9bf0",
                    color: "white",
                    fontSize: "12px",
                    fontWeight: "bold",
                    borderRadius: "999px",
                    padding: "2px 8px",
                    marginLeft: "auto",
                  }}
                >
                  {item.badge}
                </span>
              )}
            </a>
          </li>
        ))}
      </ul>

      {currentUser ? (
        <button
          className="sidebar__post-btn"
          onClick={() => {
            if (onSelectTab) onSelectTab("home");
            const input = document.querySelector(".composer textarea");
            if (input) input.focus();
          }}
        >
          Post
        </button>
      ) : (
        <button
          className="sidebar__post-btn"
          style={{ background: "#00ba7c" }}
          onClick={onOpenAuthModal}
        >
          Sign In
        </button>
      )}

      <div className="sidebar__user" style={{ marginTop: "auto" }}>
        {currentUser ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
            <div
              style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }}
              onClick={() => onSelectTab && onSelectTab("profile")}
            >
              <img
                className="avatar"
                src={currentUser.avatar?.smallUrl || `https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser.handle}`}
                alt=""
                style={{ width: "40px", height: "40px", borderRadius: "50%" }}
              />
              <div className="tweet-author-info">
                <span style={{ fontWeight: "bold" }}>{currentUser.displayName}</span>
                <span style={{ color: "#71767b" }}>@{currentUser.handle}</span>
              </div>
            </div>
            <button
              onClick={onLogout}
              title="Sign Out"
              style={{
                background: "transparent",
                border: "1px solid #536471",
                color: "#e7e9ea",
                borderRadius: "999px",
                padding: "4px 10px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Log out
            </button>
          </div>
        ) : (
          <div
            onClick={onOpenAuthModal}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              cursor: "pointer",
              width: "100%",
              padding: "4px",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                background: "#333",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "18px",
              }}
            >
              👤
            </div>
            <div className="tweet-author-info">
              <span style={{ fontWeight: "bold" }}>Guest Mode</span>
              <span style={{ color: "#1d9bf0", fontSize: "13px" }}>Click to Sign In ➔</span>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
