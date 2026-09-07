const TRENDS = [
  { category: "Technology · Trending", title: "#AsyncPython", meta: "12.4K posts" },
  { category: "Programming · Trending", title: "FastAPI", meta: "8,201 posts" },
  { category: "Trending in India", title: "#100DaysOfCode", meta: "45.2K posts" },
];

const FOLLOW_SUGGESTIONS = [
  { name: "Dev Patel", handle: "@devpatel" },
  { name: "Maya Chen", handle: "@mayacodes" },
];

export default function RightPanel({ searchQuery, onSearchChange }) {
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
        <h2>What's happening</h2>
        {TRENDS.map((t) => (
          <div className="trend" key={t.title}>
            <span className="trend__category">{t.category}</span>
            <span className="trend__title">{t.title}</span>
            <span className="trend__meta">{t.meta}</span>
          </div>
        ))}
        <a href="#" className="show-more">Show more</a>
      </div>

      <div className="right-panel__box">
        <h2>Who to follow</h2>
        {FOLLOW_SUGGESTIONS.map((p) => (
          <div className="follow-suggestion" key={p.handle}>
            <img
              className="avatar avatar--sm"
              src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${p.name}`}
              alt=""
            />
            <div className="tweet-author-info">
              <span>{p.name}</span>
              <span>{p.handle}</span>
            </div>
            <button className="follow-btn">Follow</button>
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
        <span>&copy; 2026 X-clone</span>
      </footer>
    </aside>
  );
}
