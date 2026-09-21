# Twitter-style Tweet Detail Page — React Frontend

A single-tweet detail page (Twitter/X clone) built with React + Vite,
covering semantic HTML, mobile-first responsive design, and an
infinite-scroll feed connected to a FastAPI backend.

## Features

- Semantic HTML structure (`<article>` per tweet, `<section>` for
  replies, `<time>` with machine-readable `datetime`, `<form>`/`<label>`
  for the reply composer) — screen-reader tested
- Mobile-first responsive layout: full 3-column desktop view (sidebar /
  feed / right panel), collapsing to a bottom tab bar + stacked right
  panel on narrower screens
- Infinite scroll via `IntersectionObserver`, pulling paginated posts
  from the backend's `/feed?cursor=&limit=` endpoint
- Reply modal shared across every tweet — remembers which tweet was
  clicked, inserts the reply directly under that specific tweet
- Like/retweet with a small fading toast message ("Liked"/"Unliked")
- Search bar filtering the loaded feed by author or text
- Click-to-expand image lightbox
- Like/retweet/comment/share buttons work identically on the main
  tweet and every infinite-scroll-loaded post, via one shared component

## Tech stack

- **React 18** + **Vite 5** (dev server, build tool)
- Plain CSS (`src/style.css`) — no CSS framework
- No state management library — component state (`useState`) + one
  level of prop drilling from `App.jsx`, since the app is small enough
  not to need Redux/Context

## Project structure

```
frontend/
├── package.json
├── vite.config.js
├── index.html              # just the #root shell — React renders everything into it
└── src/
    ├── main.jsx              # entry point
    ├── App.jsx               # state + layout — the "brain"
    ├── api.js                # backend fetch calls, one place
    ├── style.css
    └── components/
        ├── Tweet.jsx          # reusable — every tweet on the page
        ├── ReplyModal.jsx
        ├── Sidebar.jsx
        ├── RightPanel.jsx
        └── ImageLightbox.jsx
```

## Setup

Requires Node.js and npm.

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173` by default.

## Backend connection

`src/api.js` holds the single `API_BASE` constant every fetch call
uses. Currently pointed at the deployed FastAPI backend on Render:

```js
const API_BASE = "https://projects-h6bp.onrender.com";
```

To run against a backend on your own machine instead, change this to
`http://127.0.0.1:8000` and start that backend locally first (see the
backend's own README for its run instructions).

**Note:** this frontend expects the backend's `/feed` response shape to
be `{ posts: [...], next_cursor, has_more }` with snake_case-ish flat
post objects (`author`, `text`, `image`, `comment_count`, `like_count`,
`retweet_count`). This is the *original* mock-data backend
(`backend/main.py` at the project root) — it is **not** yet compatible
with the newer, more strictly-structured `app/` backend (Stage A of the
PRD-based assignment), which returns a different camelCase contract
(`items`, `nextCursor`, nested `author`/`media` objects). Reconnecting
this frontend to that new backend is separate, not-yet-done work.

## Build for production

```bash
npm run build
```

Outputs to `dist/`. Deployed via Vercel with:
- **Root Directory:** `frontend`
- **Framework Preset:** Vite (auto-fills build command `npm run build`,
  output directory `dist`)

## Known limitations

- Search only filters posts already fetched from the backend (up to
  100, via two paginated calls on page load) — it does not query a
  real search endpoint, since the connected backend doesn't have one.
- Like/retweet/reply are client-side only — nothing persists to a
  database. Refreshing the page resets all interaction state.
- The right panel's "What's happening" trends and "Who to follow"
  suggestions are static placeholder content, not real data.