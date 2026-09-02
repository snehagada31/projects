const API_BASE = "https://projects-h6bp.onrender.com/feed?cursor=0&limit=100";

const feed = document.querySelector(".feed");
const loadedFeed = document.getElementById("loaded-feed");
const feedStatus = document.getElementById("feed-status");

// ---------- Reply modal: shared by EVERY tweet's comment button ----------
const modal = document.getElementById("reply-modal");
const modalClose = document.getElementById("modal-close");
const modalReplyingTo = document.getElementById("modal-replying-to");
const modalForm = document.getElementById("modal-form");
const modalInput = document.getElementById("modal-reply-input");

let targetTweetEl = null;   // the specific <article class="tweet"> being replied to
let targetCommentSpan = null; // that tweet's comment-count <span>, to bump on submit

function openReplyModal(tweetEl) {
  targetTweetEl = tweetEl;
  const actionsDiv = tweetEl.querySelector(".tweet-actions");
  targetCommentSpan = actionsDiv.querySelector(".count-comment");

  const author = actionsDiv.dataset.author || "";
  const handle = actionsDiv.dataset.handle || "";
  modalReplyingTo.textContent = `Replying to ${handle || author}`;

  modal.classList.remove("hidden");
  modalInput.value = "";
  modalInput.focus();
}

function closeReplyModal() {
  modal.classList.add("hidden");
  targetTweetEl = null;
}

modalClose.addEventListener("click", closeReplyModal);

// clicking the dark overlay (outside modal-content) also closes it
modal.addEventListener("click", (e) => {
  if (e.target === modal) closeReplyModal();
});

modalForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = modalInput.value.trim();
  if (text === "" || !targetTweetEl) return;

  const reply = document.createElement("article");
  reply.className = "tweet tweet--reply";
  reply.innerHTML = `
    <div class="tweet-author">
      <img class="avatar" src="https://api.dicebear.com/7.x/avataaars/svg?seed=you" alt="">
      <div class="tweet-author-info">
        <span>You</span>
        <span>@you</span>
      </div>
    </div>
    <p class="reply-text-body"></p>
    <button class="delete-btn" aria-label="Delete reply">Delete</button>
  `;
  reply.querySelector(".reply-text-body").textContent = text;
  reply.querySelector(".delete-btn").addEventListener("click", () => reply.remove());

  // insert the new reply DIRECTLY after the tweet it's replying to —
  // this is the actual fix: not appended to the bottom of the whole page,
  // not shoved to the top, but right where that tweet lives.
  targetTweetEl.insertAdjacentElement("afterend", reply);

  if (targetCommentSpan) {
    targetCommentSpan.textContent = Number(targetCommentSpan.textContent) + 1;
  }

  closeReplyModal();
});

// ---------- Loaded-post builder (with optional photo) ----------
function buildLoadedPost(post) {
  const article = document.createElement("article");
  article.className = "tweet";

  const handle = "@" + post.author.toLowerCase().replace(/\s+/g, "");
  const imageHtml = post.image
    ? `<img class="tweet-photo" src="${post.image}" alt="">`
    : "";

  article.innerHTML = `
    <div class="tweet-author">
      <img class="avatar" src="https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(post.author)}" alt="">
      <div class="tweet-author-info">
        <span>${post.author}</span>
        <span>${handle}</span>
      </div>
    </div>
    <p class="reply-text-body"></p>
    ${imageHtml}
    <div class="tweet-actions" data-post-id="${post.id}" data-author="${post.author}" data-handle="${handle}">
      <button class="action-comment" aria-label="Reply">💬 <span class="count-comment">${post.comment_count}</span></button>
      <button class="action-retweet" aria-label="Retweet">🔁 <span class="count-retweet">${post.retweet_count}</span></button>
      <button class="action-like" aria-label="Like">♡ <span class="count-like">${post.like_count}</span></button>
      <button class="action-share" aria-label="Share">↗</button>
    </div>
  `;
  article.querySelector(".reply-text-body").textContent = post.text;
  return article;
}

// ---------- Infinite scroll ----------
let cursor = 0;
const limit = 10;
let loading = false;
let hasMore = true;

async function loadNextBatch() {
  if (loading || !hasMore) return;
  loading = true;
  feedStatus.textContent = "Loading more...";

  try {
    const res = await fetch(`${API_BASE}/feed?cursor=${cursor}&limit=${limit}`);
    const data = await res.json();

    data.posts.forEach((post) => {
      loadedFeed.appendChild(buildLoadedPost(post));
    });

    hasMore = data.has_more;
    cursor = data.next_cursor ?? cursor;
    feedStatus.textContent = hasMore ? "Scroll for more" : "You've reached the end";
  } catch (err) {
    feedStatus.textContent = "Backend not running — start uvicorn to load more posts";
    console.log("Feed fetch failed:", err.message);
    hasMore = false;
  } finally {
    loading = false;
  }
}

const observer = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) loadNextBatch();
});
observer.observe(feedStatus);

loadNextBatch();

// ---------- ONE delegated listener handles like/retweet/comment/share for
// EVERY tweet on the page — the original static ones, the main tweet, and
// every post added later via infinite scroll. This works on future posts
// too because the listener lives on `feed` (which never goes away), not
// on the buttons themselves (which get created after the page loads). ----------
feed.addEventListener("click", (event) => {
  const likeBtn = event.target.closest(".action-like");
  const retweetBtn = event.target.closest(".action-retweet");
  const commentBtn = event.target.closest(".action-comment");
  const shareBtn = event.target.closest(".action-share");

  if (likeBtn) {
    const countSpan = likeBtn.querySelector(".count-like");
    const isLiked = likeBtn.classList.toggle("liked");
    countSpan.textContent = Number(countSpan.textContent) + (isLiked ? 1 : -1);
    likeBtn.firstChild.textContent = isLiked ? "♥ " : "♡ ";
  }

  if (retweetBtn) {
    const countSpan = retweetBtn.querySelector(".count-retweet");
    const isRetweeted = retweetBtn.classList.toggle("retweeted");
    countSpan.textContent = Number(countSpan.textContent) + (isRetweeted ? 1 : -1);
  }

  if (commentBtn) {
    const tweetEl = commentBtn.closest(".tweet");
    openReplyModal(tweetEl);
  }

  if (shareBtn) {
    const postId = shareBtn.closest(".tweet-actions").dataset.postId;
    navigator.clipboard.writeText(`${window.location.href}#post-${postId}`)
      .then(() => alert("Link copied!"))
      .catch(() => alert("Couldn't copy link"));
  }
});
