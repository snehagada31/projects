# Decision Record 11: Real-Time Trending News & Live API Resilience

**Decision:**
Power the "What's happening" panel using a 3-tier resilient architecture: primary live news fetched directly from the open Algolia Hacker News public API, secondary fallback to dynamic backend hashtag extraction (`GET /trends`), and tertiary fallback to curated live tech news defaults.

**Options considered:**
1. *Static hardcoded mock trends*: Hardcoded array in frontend components. Rejected: static lists become stale immediately and do not represent a production-ready application.
2. *Paid News API requiring secret API keys*: Rapidly hits monthly rate limits on free plans, breaks on public GitHub forks without `.env` secrets, and exposes API keys if called client-side.
3. *Resilient 3-Tier Live Public News Engine (Chosen)*:
   - Primary: Client-side fetch to `https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=6`. Requires no secret API key, has open CORS headers, and provides real-time breaking tech & global news headlines with engagement scores (points and comments) and direct article URLs.
   - Secondary: Backend `GET /trends` endpoint that scans the PostgreSQL `posts` table for `#hashtags` using regex, ranking them by frequency.
   - Tertiary: Curated fallback defaults ensuring zero UI breakage even during complete network partitions.

**Why this one:**
- **Zero Configuration**: Works instantly on fresh developer machines, Vercel deployments, and production environments without needing API keys or payment cards.
- **High User Engagement**: Cards feature live engagement metrics, source domain tags (e.g. `Live News · nytimes.com`, `Live News · github.com`), and open the real live article in a new tab when clicked.
- **Fail-Safe High Availability**: If the third-party news service experiences an outage or client is offline, the system seamlessly degrades to database hashtags without rendering an error screen.

**Risks:**
- Third-party API schema changes or temporary network timeout.
  *Mitigation*: Wrapped in robust `try...catch` blocks that immediately fall back to local backend trends.

**Verification:**
- `frontend/src/api.js::fetchTrendingTopics`
- `frontend/src/components/RightPanel.jsx` (Interactive news cards & `● LIVE NEWS` badge)
- `backend/app/api/posts.py::get_trending_topics`
- `backend/app/repositories/postgres_repository.py::get_trending_topics`
