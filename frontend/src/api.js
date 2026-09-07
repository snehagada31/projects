// All backend calls live here, in one place — components import this
// instead of calling fetch() directly. If your Render URL ever changes,
// you only edit it here, not in five different components.
const API_BASE = "https://projects-h6bp.onrender.com";

export async function fetchFeed(cursor, limit = 10) {
  const res = await fetch(`${API_BASE}/feed?cursor=${cursor}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch feed");
  return res.json(); // { posts, next_cursor, has_more }
}