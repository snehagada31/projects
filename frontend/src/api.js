const API_BASE = "http://localhost:8000";

export async function fetchFeed(cursor, limit = 10) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  const url = isRealCursor
    ? `${API_BASE}/feed?cursor=${encodeURIComponent(cursor)}&limit=${limit}`
    : `${API_BASE}/feed?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch feed");
  const data = await res.json();

  return {
    posts: (data.items || data.posts || []).map((item) => ({
      id: item.id,
      author: item.author?.displayName || item.author?.handle || item.author || "User",
      handle: "@" + (item.author?.handle || "user"),
      text: item.text,
      image: item.media?.[0]?.largeUrl || item.media?.[0]?.smallUrl || item.image || null,
      like_count: item.likeCount ?? item.like_count ?? 0,
      comment_count: item.replyCount ?? item.comment_count ?? 0,
      retweet_count: item.retweetCount ?? item.retweet_count ?? 0,
      liked_by_viewer: item.likedByViewer ?? item.liked_by_viewer ?? false,
      reposted_by_viewer: item.repostedByViewer ?? item.reposted_by_viewer ?? false,
      created_at: item.createdAt || item.created_at,
    })),
    next_cursor: data.nextCursor !== undefined ? data.nextCursor : data.next_cursor,
    has_more: data.hasMore !== undefined ? data.hasMore : data.has_more,
  };
}

export async function likePost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/like`, {
    method: "PUT",
  });
  if (!res.ok) throw new Error("Failed to like post");
  return res.json();
}

export async function unlikePost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/like`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to unlike post");
  return res.json();
}

export async function repostPost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/repost`, {
    method: "PUT",
  });
  if (!res.ok) throw new Error("Failed to repost");
  return res.json();
}

export async function unrepostPost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/repost`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to undo repost");
  return res.json();
}

export async function createPost({ kind = "original", text, replyToId = null, repostOfId = null }) {
  const res = await fetch(`${API_BASE}/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kind,
      text,
      replyToId,
      repostOfId,
    }),
  });
  if (!res.ok) throw new Error("Failed to create post");
  return res.json();
}

export async function deletePost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete post");
  return res.json();
}

export async function fetchPostReplies(postId, cursor = null, limit = 50) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  let url = `${API_BASE}/posts/${postId}/replies?limit=${limit}`;
  if (isRealCursor) {
    url += `&cursor=${encodeURIComponent(cursor)}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch replies");
  const data = await res.json();
  return {
    replies: (data.items || []).map((item) => ({
      id: item.id,
      author: item.author?.displayName || item.author?.handle || "User",
      handle: "@" + (item.author?.handle || "user"),
      text: item.text,
      created_at: item.createdAt,
    })),
    next_cursor: data.nextCursor,
    has_more: data.hasMore,
  };
}

export async function searchPosts(query, cursor = null, limit = 10) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  let url = `${API_BASE}/search/posts?q=${encodeURIComponent(query)}&limit=${limit}`;
  if (isRealCursor) {
    url += `&cursor=${encodeURIComponent(cursor)}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to search posts");
  const data = await res.json();
  return {
    posts: (data.items || []).map((item) => ({
      id: item.id,
      author: item.author?.displayName || item.author?.handle || "User",
      handle: "@" + (item.author?.handle || "user"),
      text: item.text,
      image: item.media?.[0]?.largeUrl || null,
      like_count: item.likeCount ?? 0,
      comment_count: item.replyCount ?? 0,
      retweet_count: item.retweetCount ?? 0,
      liked_by_viewer: item.likedByViewer ?? false,
      reposted_by_viewer: item.repostedByViewer ?? false,
      created_at: item.createdAt,
    })),
    next_cursor: data.nextCursor,
    has_more: data.hasMore,
  };
}

export async function fetchUsers(query = null) {
  const url = query ? `${API_BASE}/users?q=${encodeURIComponent(query)}` : `${API_BASE}/users`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

export async function followUser(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}/follow`, {
    method: "PUT",
  });
  if (!res.ok) throw new Error("Failed to follow user");
  return res.json();
}

export async function unfollowUser(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}/follow`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to unfollow user");
  return res.json();
}