export default function Sidebar() {
  const navItems = [
    ["🏠", "Home"], ["🔍", "Explore"], ["🔔", "Notifications"],
    ["👥", "Follow"], ["💬", "Chat"], ["✨", "Grok"],
    ["🕒", "History"], ["✅", "Premium"], ["👤", "Profile"], ["⋯", "More"],
  ];

  return (
    <nav className="sidebar" aria-label="Main navigation">
      <div className="sidebar__logo">𝕏</div>
      <ul className="sidebar__nav">
        {navItems.map(([icon, label]) => (
          <li key={label}>
            <a href="#">
              {icon} <span>{label}</span>
            </a>
          </li>
        ))}
      </ul>
      <button className="sidebar__post-btn">Post</button>
      <div className="sidebar__user">
        <img className="avatar" src="https://api.dicebear.com/7.x/avataaars/svg?seed=you" alt="" />
        <div className="tweet-author-info">
          <span>You</span>
          <span>@you</span>
        </div>
      </div>
    </nav>
  );
}
