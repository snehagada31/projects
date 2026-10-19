# Decision Record 04: Personalized Home Feed and Onboarding Policy

**Decision:**
Personalized home feed showing originals by followed authors plus the viewer's own posts, with a labeled public fallback for new members (onboarding), keyset pagination by `(created_at, id)`, and constant query budget.

**Options considered:**
1. *Always empty feed for new users*: Clean separation, but leads to a "ghost town" first impression where users think the app is broken.
2. *Fan-out on write (push model / Redis inbox)*: Copies post IDs into every follower's inbox on post creation. Out of scope for P0 and introduces massive write amplification.
3. *Pull-based SQL join on read with explicit empty state (Chosen)*:
   - Evaluates active relationships at read time: `author_id IN (SELECT following_id FROM follows WHERE follower_id = :viewer_id) OR author_id = :viewer_id`.
   - Excludes deactivated authors.
   - If the user follows nobody and has no posts, returns an explicit empty list `[]` (intentional empty onboarding state), guaranteeing that unfollowed stranger posts never leak into a personal feed.
   - Unauthenticated visitors receive the full public feed for discovery, maintaining full V1 compatibility.

**Pagination & Consistency:**
- Cursor-based pagination using the composite tuple `(created_at, id)` ensures zero duplicate rows across page breaks, even if multiple posts share the exact same timestamp.

**Query Budget:**
- Feed page load: Maximum 2 SQL queries (1 for paginated posts with eager-loaded authors, 1 batch query for media/viewer state), independent of page size (N+1 query growth strictly prohibited).

**Test proving it:**
- `backend/tests/test_personalized_feed.py::test_personalized_feed_shows_only_followed_and_self`
- `backend/tests/test_personalized_feed.py::test_onboarding_empty_fallback`
- `backend/tests/test_personalized_feed.py::test_unfollow_reflects_in_feed`
