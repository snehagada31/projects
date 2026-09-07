import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import RightPanel from "./components/RightPanel.jsx";
import Tweet from "./components/Tweet.jsx";
import ReplyModal from "./components/ReplyModal.jsx";
import ImageLightbox from "./components/ImageLightbox.jsx";
import { fetchFeed } from "./api.js";

export default function App() {
  const [loadedPosts, setLoadedPosts] = useState([]);
  const [cursor, setCursor] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const [repliesByTarget, setRepliesByTarget] = useState({});
  const [replyingTo, setReplyingTo] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [lightboxImage, setLightboxImage] = useState(null);

  // Full search index, fetched once. The backend caps "limit" at 50 per
  // request (le=50 in main.py), so getting all 100 mock posts takes TWO
  // calls (0-50, then 50-100), merged together — a single limit=100 call
  // was silently rejected by the backend, which is why search was broken.
  const [allPostsForSearch, setAllPostsForSearch] = useState([]);

  const feedStatusRef = useRef(null);

    const loadNextBatch = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    try {
      const data = await fetchFeed(cursor, 10);
      setLoadedPosts((prev) => {
        const existingIds = new Set(prev.map((p) => p.id));
        const newOnes = data.posts.filter((p) => !existingIds.has(p.id));
        return [...prev, ...newOnes];
      });
      setHasMore(data.has_more);
      setCursor(data.next_cursor ?? cursor);
    } catch (err) {
      console.log("Feed fetch failed:", err.message);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [cursor, loading, hasMore]);

  useEffect(() => {
    const el = feedStatusRef.current;
    if (!el) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) loadNextBatch();
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadNextBatch]);

  useEffect(() => {
    loadNextBatch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    Promise.all([fetchFeed(0, 50), fetchFeed(50, 50)])
      .then(([first, second]) => {
        setAllPostsForSearch([...first.posts, ...second.posts]);
      })
      .catch((err) => console.log("Search index fetch failed:", err.message));
  }, []);

  function openReplyModal(targetId, handle) {
    setReplyingTo({ targetId, handle });
  }

  function submitReply(text) {
    const targetId = replyingTo.targetId;
    const newReply = {
      id: crypto.randomUUID(),
      author: "You",
      handle: "@you",
      text,
    };
    setRepliesByTarget((prev) => ({
      ...prev,
      [targetId]: [...(prev[targetId] || []), newReply],
    }));
    setReplyingTo(null);
  }

  function deleteReply(targetId, replyId) {
    setRepliesByTarget((prev) => ({
      ...prev,
      [targetId]: prev[targetId].filter((r) => r.id !== replyId),
    }));
  }

  function renderRepliesFor(targetId) {
    const replies = repliesByTarget[targetId] || [];
    return replies.map((r) => (
      <Tweet
        key={r.id}
        author={r.author}
        handle={r.handle}
        text={r.text}
        isReply
        onDelete={() => deleteReply(targetId, r.id)}
      />
    ));
  }

  const query = searchQuery.trim().toLowerCase();
  const visiblePosts = query
    ? allPostsForSearch.filter(
        (p) =>
          p.author.toLowerCase().includes(query) ||
          p.text.toLowerCase().includes(query)
      )
    : loadedPosts;

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="feed">
        <header>
          <button aria-label="Go back">&larr;</button>
          <h1>Post</h1>
        </header>

        <Tweet
          author="Nikkar"
          handle="@niki"
          text='Anyone else find generators click way easier once you stop thinking "loop" and start thinking "pause button"?'
          onComment={() => openReplyModal("nikkar", "@niki")}
          onImageClick={setLightboxImage}
        />
        {renderRepliesFor("nikkar")}

        <Tweet
          author="Trisha"
          handle="@trisha_dev"
          text="Building a feed paginator with a generator today — yield 10 posts at a time instead of loading the whole thing into memory."
          time="2026-08-25T09:14:00+05:30"
          initialComments={3}
          initialRetweets={4}
          initialLikes={19}
          onComment={() => openReplyModal("main", "@trisha_dev")}
          onImageClick={setLightboxImage}
        />
        {renderRepliesFor("main")}

        <section className="replies">
          <h2>Replies</h2>

          <Tweet
            author="shreehari"
            handle="@shree"
            text="wait does that mean the whole feed never sits in memory at once?"
            showActions={false}
          />
          {renderRepliesFor("shreehari")}

          {visiblePosts.map((post) => {
            const targetId = `post-${post.id}`;
            const handle = "@" + post.author.toLowerCase().replace(/\s+/g, "");
            return (
              <div key={post.id}>
                <Tweet
                  author={post.author}
                  handle={handle}
                  text={post.text}
                  image={post.image}
                  initialComments={post.comment_count}
                  initialRetweets={post.retweet_count}
                  initialLikes={post.like_count}
                  onComment={() => openReplyModal(targetId, handle)}
                  onImageClick={setLightboxImage}
                />
                {renderRepliesFor(targetId)}
              </div>
            );
          })}

          <p ref={feedStatusRef} className="feed-status">
            {hasMore ? "Scroll for more" : "You've reached the end"}
          </p>
        </section>
      </main>

      <RightPanel searchQuery={searchQuery} onSearchChange={setSearchQuery} />

      <ReplyModal
        replyingTo={replyingTo}
        onClose={() => setReplyingTo(null)}
        onSubmit={submitReply}
      />

      <ImageLightbox src={lightboxImage} onClose={() => setLightboxImage(null)} />
    </div>
  );
}