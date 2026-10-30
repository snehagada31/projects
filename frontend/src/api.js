const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");

// --- Token & Auth Helpers ---
export function getToken() {
  return localStorage.getItem("social_v2_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("social_v2_token", token);
  } else {
    localStorage.removeItem("social_v2_token");
  }
}

export function removeToken() {
  localStorage.removeItem("social_v2_token");
}

export function getAuthHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// --- Auth Endpoints ---
function formatApiError(data, fallbackMsg) {
  if (data?.error?.details && Array.isArray(data.error.details) && data.error.details.length > 0) {
    const messages = data.error.details.map((d) => {
      if (d.field === "password") return "Password must be at least 8 characters long";
      if (d.field === "handle") return "Handle must be valid (1-50 characters)";
      if (d.field === "displayName" || d.field === "display_name") return "Display name is required";
      return `${d.field}: ${d.reason || "invalid"}`;
    });
    return messages.join(", ");
  }
  return data?.error?.message || fallbackMsg;
}

export async function registerUser({ handle, displayName, password, bio = "" }, autoLogin = false) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handle, displayName, password, bio }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(formatApiError(data, "Registration failed"));
  }
  if (autoLogin && data.token) {
    setToken(data.token);
  }
  return data;
}

export async function loginUser({ handle, password }) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handle, password }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(formatApiError(data, "Login failed"));
  }
  if (data.token) {
    setToken(data.token);
  }
  return data;
}

export async function logoutUser() {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  } catch (err) {
    console.error("Logout network call error:", err);
  } finally {
    removeToken();
  }
}

export async function fetchMe() {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      removeToken();
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error("fetchMe error:", err);
    return null;
  }
}

// --- Active Session Management ---
export async function fetchActiveSessions() {
  const res = await fetch(`${API_BASE}/auth/sessions`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to fetch active sessions");
  }
  const data = await res.json();
  return data.sessions || [];
}

export async function revokeSession(sessionId) {
  const res = await fetch(`${API_BASE}/auth/sessions/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to revoke session");
  }
  return res.json();
}

export async function revokeOtherSessions() {
  const res = await fetch(`${API_BASE}/auth/sessions/revoke-others`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to revoke other sessions");
  }
  return res.json();
}

// --- Feed (Personalized when logged in, Public when guest) ---
export async function fetchFeed(cursor, limit = 10) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  const url = isRealCursor
    ? `${API_BASE}/feed?cursor=${encodeURIComponent(cursor)}&limit=${limit}`
    : `${API_BASE}/feed?limit=${limit}`;

  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch feed");
  const data = await res.json();

  return {
    posts: (data.items || []).map((item) => ({
      id: item.id,
      authorId: item.author?.id,
      author: item.author?.displayName || item.author?.handle || "User",
      handle: "@" + (item.author?.handle || "user"),
      authorAvatar: item.author?.avatar?.smallUrl || item.author?.avatar?.largeUrl || null,
      text: item.text,
      image: item.media?.[0]?.largeUrl || item.media?.[0]?.smallUrl || null,
      like_count: item.likeCount ?? 0,
      comment_count: item.replyCount ?? 0,
      retweet_count: item.retweetCount ?? 0,
      liked_by_viewer: item.likedByViewer ?? false,
      reposted_by_viewer: item.repostedByViewer ?? false,
      bookmarked_by_viewer: item.bookmarkedByViewer ?? false,
      reply_to_id: item.replyToId || item.reply_to_id || null,
      reply_to_handle: item.replyToHandle || item.reply_to_handle || null,
      created_at: item.createdAt,
    })),
    next_cursor: data.nextCursor,
    has_more: data.hasMore,
  };
}

// --- Like / Unlike ---
export async function likePost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/like`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to like post");
  }
  return res.json();
}

export async function unlikePost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/like`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to unlike post");
  }
  return res.json();
}

// --- Repost / Unrepost ---
export async function repostPost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/repost`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to repost");
  }
  return res.json();
}

export async function unrepostPost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/repost`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to undo repost");
  }
  return res.json();
}

// --- Post Creation, Edit & Deletion ---
export async function createPost({ kind = "original", text, replyToId = null, repostOfId = null, media = null }) {
  const payload = { kind, text, replyToId, repostOfId };
  if (media && Array.isArray(media) && media.length > 0) {
    payload.media = media;
  }
  const res = await fetch(`${API_BASE}/posts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to create post");
  }
  return res.json();
}

export async function uploadPostImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const base64Data = reader.result;
        const res = await fetch(`${API_BASE}/upload-image`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
          body: JSON.stringify({
            filename: file.name,
            data: base64Data,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err?.error?.message || "Upload failed");
        }
        const data = await res.json();
        resolve(data.url);
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = () => reject(new Error("Failed to read image file"));
    reader.readAsDataURL(file);
  });
}

export async function editPost(postId, text) {
  const res = await fetch(`${API_BASE}/posts/${postId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to edit post");
  }
  return res.json();
}

export async function deletePost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to delete post");
  }
  return res.json();
}

// --- Post Replies ---
export async function fetchPostReplies(postId, cursor = null, limit = 50) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  let url = `${API_BASE}/posts/${postId}/replies?limit=${limit}`;
  if (isRealCursor) {
    url += `&cursor=${encodeURIComponent(cursor)}`;
  }
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch replies");
  const data = await res.json();
  return {
    replies: (data.items || []).map((item) => ({
      id: item.id,
      authorId: item.author?.id,
      author: item.author?.displayName || item.author?.handle || "User",
      handle: "@" + (item.author?.handle || "user"),
      authorAvatar: item.author?.avatar?.smallUrl || null,
      text: item.text,
      created_at: item.createdAt,
    })),
    next_cursor: data.nextCursor,
    has_more: data.hasMore,
  };
}

// --- Search Posts & Users ---
export async function searchPosts(query, cursor = null, limit = 10) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  let url = `${API_BASE}/search/posts?q=${encodeURIComponent(query)}&limit=${limit}`;
  if (isRealCursor) {
    url += `&cursor=${encodeURIComponent(cursor)}`;
  }
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to search posts");
  const data = await res.json();
  return {
    posts: (data.items || []).map((item) => ({
      id: item.id,
      authorId: item.author?.id,
      author: item.author?.displayName || item.author?.handle || "User",
      handle: "@" + (item.author?.handle || "user"),
      authorAvatar: item.author?.avatar?.smallUrl || null,
      text: item.text,
      image: item.media?.[0]?.largeUrl || null,
      like_count: item.likeCount ?? 0,
      comment_count: item.replyCount ?? 0,
      retweet_count: item.retweetCount ?? 0,
      liked_by_viewer: item.likedByViewer ?? false,
      reposted_by_viewer: item.repostedByViewer ?? false,
      bookmarked_by_viewer: item.bookmarkedByViewer ?? false,
      reply_to_id: item.replyToId || item.reply_to_id || null,
      reply_to_handle: item.replyToHandle || item.reply_to_handle || null,
      created_at: item.createdAt,
    })),
    next_cursor: data.nextCursor,
    has_more: data.hasMore,
  };
}

export async function fetchUsers(query = null) {
  const url = query ? `${API_BASE}/users?q=${encodeURIComponent(query)}` : `${API_BASE}/users`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

export async function fetchUserProfile(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export async function fetchUserPosts(userId, kind = null) {
  const url = kind
    ? `${API_BASE}/users/${userId}/posts?kind=${kind}`
    : `${API_BASE}/users/${userId}/posts`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch user posts");
  const data = await res.json();
  return (data.items || []).map((item) => ({
    id: item.id,
    authorId: item.author?.id,
    author: item.author?.displayName || item.author?.handle || "User",
    handle: "@" + (item.author?.handle || "user"),
    authorAvatar: item.author?.avatar?.smallUrl || item.author?.avatar?.largeUrl || null,
    text: item.text,
    image: item.media?.[0]?.largeUrl || item.media?.[0]?.smallUrl || null,
    like_count: item.likeCount ?? 0,
    comment_count: item.replyCount ?? 0,
    retweet_count: item.retweetCount ?? 0,
    liked_by_viewer: item.likedByViewer ?? false,
    reposted_by_viewer: item.repostedByViewer ?? false,
    bookmarked_by_viewer: item.bookmarkedByViewer ?? false,
    created_at: item.createdAt,
  }));
}

export async function updateMyProfile(profileData) {
  const res = await fetch(`${API_BASE}/users/me`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(profileData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to update profile");
  }
  return res.json();
}

// --- Follow / Unfollow ---
export async function followUser(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}/follow`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to follow user");
  }
  return res.json();
}

export async function unfollowUser(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}/follow`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to unfollow user");
  }
  return res.json();
}

// --- Notifications ---
export async function fetchNotifications(cursor = null, limit = 20) {
  let url = `${API_BASE}/notifications?limit=${limit}`;
  if (cursor) {
    url += `&cursor=${encodeURIComponent(cursor)}`;
  }
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch notifications");
  return res.json();
}

export async function fetchUnreadCount() {
  const res = await fetch(`${API_BASE}/notifications/unread-count`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return 0;
  const data = await res.json();
  return data.count || 0;
}

export async function markNotificationRead(notificationId) {
  const res = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to mark notification as read");
  return res.json();
}

export async function markAllNotificationsRead() {
  const res = await fetch(`${API_BASE}/notifications/read-all`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to mark all as read");
  return res.json();
}

// --- Bookmarks (PY-P1-02) ---
export async function bookmarkPost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/bookmark`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to bookmark post");
  }
  return res.json();
}

export async function unbookmarkPost(postId) {
  const res = await fetch(`${API_BASE}/posts/${postId}/bookmark`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to remove bookmark");
  }
  return res.json();
}

export async function fetchBookmarks(cursor = null, limit = 20) {
  const isRealCursor = cursor && typeof cursor === "string" && cursor !== "0";
  let url = `${API_BASE}/bookmarks?limit=${limit}`;
  if (isRealCursor) {
    url += `&cursor=${encodeURIComponent(cursor)}`;
  }
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch bookmarks");
  const data = await res.json();
  return {
    posts: (data.items || []).map((item) => ({
      id: item.id,
      authorId: item.author?.id,
      author: item.author?.displayName || item.author?.handle || "User",
      handle: "@" + (item.author?.handle || "user"),
      authorAvatar: item.author?.avatar?.smallUrl || null,
      text: item.text,
      image: item.media?.[0]?.largeUrl || null,
      like_count: item.likeCount ?? 0,
      comment_count: item.replyCount ?? 0,
      retweet_count: item.retweetCount ?? 0,
      liked_by_viewer: item.likedByViewer ?? false,
      reposted_by_viewer: item.repostedByViewer ?? false,
      bookmarked_by_viewer: true,
      created_at: item.createdAt,
    })),
    next_cursor: data.nextCursor,
    has_more: data.hasMore,
  };
}

// --- People Suggestions (PY-P1-01) ---
export async function fetchUserSuggestions(limit = 5) {
  const res = await fetch(`${API_BASE}/users/suggestions?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

// --- Conversation Expansion (PY-P1-03) ---
export async function fetchConversation(postId, replyLimit = 20) {
  const res = await fetch(`${API_BASE}/posts/${postId}/conversation?reply_limit=${replyLimit}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to fetch conversation");
  }
  return res.json();
}

// --- Reporting & Moderation (PY-P1-06) ---
export async function reportPost(postId, reason, notes = "") {
  const res = await fetch(`${API_BASE}/posts/${postId}/report`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ reason, notes }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || "Failed to submit report");
  }
  return res.json();
}
