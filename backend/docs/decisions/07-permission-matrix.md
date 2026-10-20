# Decision Record 07: Authorization Placement & Route Permission Matrix

**Decision:**
Centralized authorization dependency model using FastAPI `Depends(get_current_user)`, fine-grained resource-level ownership validation in route handlers, and a complete permission matrix covering anonymous, owner, related, and unrelated actors.

**Options considered:**
1. *Global Path-Prefix Middleware*: Checking auth for entire path prefixes (e.g. `/users/*`). Rejected: too coarse; public reads like `GET /users/{id}` or `GET /posts/{id}` must stay accessible anonymously, whereas mutations like `PATCH /users/{id}` require authentication.
2. *Decorator-based route wrappers*: Decorating each handler with `@require_role`. Rejected: hides dependency injection from FastAPI OpenAPI schema generation and makes mocking in tests harder.
3. *FastAPI `Depends` + Resource Verification in Route (Chosen)*:
   - `get_current_user`: extracts and validates Bearer token, fetches active user, and attaches verified `User` object.
   - Route handler compares verified actor against resource owner (`post.author_id == current_user.id`, `notif.recipient_id == current_user.id`).
   - Mismatches return `403 FORBIDDEN` (`AuthorizationError`) without leaking state.

---

## Route Permission Matrix

| Method | Endpoint | Anonymous | Owner | Related User | Unrelated User | Auth Requirement |
|---|---|---|---|---|---|---|
| `GET` | `/health/live` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | None (Public) |
| `GET` | `/health/ready` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | None (Public) |
| `POST` | `/auth/register` | `201 Created` | `201 Created` | `201 Created` | `201 Created` | None (Public) |
| `POST` | `/auth/login` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | None (Public) |
| `POST` | `/auth/logout` | `401 Unauthorized` | `200 OK` | `200 OK` | `200 OK` | Bearer Token |
| `GET` | `/auth/me` | `401 Unauthorized` | `200 OK` | N/A | N/A | Bearer Token |
| `GET` | `/feed` | `200 OK` (Public) | `200 OK` (Personal) | `200 OK` (Personal) | `200 OK` (Personal) | Optional Bearer |
| `GET` | `/posts/{id}` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | Optional Bearer |
| `GET` | `/posts/{id}/replies` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | Optional Bearer |
| `GET` | `/search/posts` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | Optional Bearer |
| `POST` | `/posts` | `401 Unauthorized` | `201 Created` | `201 Created` | `201 Created` | Bearer Token |
| `PATCH` | `/posts/{id}` | `401 Unauthorized` | `200 OK` | `403 Forbidden` | `403 Forbidden` | Bearer Token (Author only) |
| `DELETE` | `/posts/{id}` | `401 Unauthorized` | `200 OK` | `403 Forbidden` | `403 Forbidden` | Bearer Token (Author only) |
| `PUT` | `/posts/{id}/like` | `401 Unauthorized` | `200 OK` | `200 OK` | `200 OK` | Bearer Token |
| `DELETE` | `/posts/{id}/like` | `401 Unauthorized` | `200 OK` | `200 OK` | `200 OK` | Bearer Token |
| `PUT` | `/posts/{id}/repost` | `401 Unauthorized` | `200 OK` | `200 OK` | `200 OK` | Bearer Token |
| `DELETE` | `/posts/{id}/repost`| `401 Unauthorized` | `200 OK` | `200 OK` | `200 OK` | Bearer Token |
| `GET` | `/users` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | None (Public) |
| `GET` | `/users/{id}` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | None (Public) |
| `GET` | `/users/{id}/media` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | None (Public) |
| `GET` | `/users/{id}/followers` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | Optional Bearer |
| `GET` | `/users/{id}/following` | `200 OK` | `200 OK` | `200 OK` | `200 OK` | Optional Bearer |
| `PATCH` | `/users/me` | `401 Unauthorized` | `200 OK` | N/A | N/A | Bearer Token |
| `POST` | `/users/me/deactivate`| `401 Unauthorized` | `200 OK` | N/A | N/A | Bearer Token |
| `PATCH` | `/users/{id}` | `401 Unauthorized` | `200 OK` | `403 Forbidden` | `403 Forbidden` | Bearer Token (Self only) |
| `PUT` | `/users/{id}/follow` | `401 Unauthorized` | `422 (Self)` | `200 OK` | `200 OK` | Bearer Token |
| `DELETE` | `/users/{id}/follow` | `401 Unauthorized` | `422 (Self)` | `200 OK` | `200 OK` | Bearer Token |
| `GET` | `/notifications` | `401 Unauthorized` | `200 OK` | N/A | N/A | Bearer Token |
| `GET` | `/notifications/unread-count` | `401 Unauthorized` | `200 OK` | N/A | N/A | Bearer Token |
| `PATCH` | `/notifications/{id}/read` | `401 Unauthorized` | `200 OK` | `403 Forbidden` | `403 Forbidden` | Bearer Token (Recipient only) |
| `POST` | `/notifications/read-all` | `401 Unauthorized` | `200 OK` | N/A | N/A | Bearer Token |

---

**Test proving it:**
- `backend/tests/test_permission_matrix.py::test_no_unclassified_mutations_in_route_matrix`
- `backend/tests/test_permission_matrix.py::test_request_id_tracing_on_allowed_and_denied_requests`
