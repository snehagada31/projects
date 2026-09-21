# Request Lifecycle

How one HTTP request actually becomes a response, from Uvicorn down to
your route code and back — and the ASGI vs WSGI distinction the raw lab
(A1) was built to demonstrate directly.

## WSGI vs ASGI, briefly

WSGI (the older standard) handles one request at a time, synchronously,
per worker — it has no native concept of "wait for something without
blocking everyone else." ASGI was built to support async: HTTP,
WebSockets, and long-lived connections, using Python's `async`/`await`.

**Uvicorn is the server** — it accepts real TCP connections, parses raw
HTTP, and speaks the ASGI protocol. **FastAPI is the application
framework** — it doesn't do any of that networking itself; it's a
Python object that Uvicorn calls according to the ASGI contract. This
is the distinction `labs/raw_asgi/app.py` demonstrates by implementing
that contract by hand, with no framework at all.

## The ASGI contract itself

Every ASGI app is a callable with this exact shape:

```python
async def app(scope, receive, send):
    ...
```

- `scope` — a dict describing the incoming connection: method, path,
  headers, query string, connection type (`http`, `websocket`, or
  `lifespan`).
- `receive` — a function to call for more incoming data (e.g. the
  request body, for POST requests).
- `send` — how the app talks back. Every HTTP response is **two
  separate messages**: `http.response.start` (status code + headers),
  then `http.response.body` (the actual bytes). FastAPI hides this
  from you — `return {"status": "ok"}` does both steps internally.

## What actually happens, request to response, in the FULL app (`app/main.py`)

1. **Uvicorn accepts the connection**, parses the raw HTTP request into
   an ASGI `scope` dict.
2. **CORS middleware** checks the request's `Origin` header against
   `FRONTEND_ORIGIN` (from `app/config.py`) — rejects it before your
   route code ever runs if it doesn't match.
3. **`RequestIdMiddleware`** (`app/common/request_id.py`) generates a
   UUID, stores it on `request.state.request_id`, and starts a timer.
   This happens for every request, success or failure — it's outer
   middleware, so it wraps everything else.
4. **FastAPI's router** matches the path (`/feed`, `/posts/{id}`, etc.)
   to the right function in `app/api/`.
5. **Path/query parameters are validated.** For typed params
   (`limit: int`), FastAPI validates automatically and raises
   `RequestValidationError` on failure. For the extra checks the
   contract needs (duplicate params, unknown params, the legacy `page`
   rejection), `app/common/query_validation.py` inspects the raw query
   string directly — this is checked *before* any repository call.
6. **`Depends(get_social_repository)`** runs — FastAPI calls this
   function and injects whatever it returns into the route. In a test,
   this exact function can be swapped for one returning fake data
   (`app.dependency_overrides`), without touching the route.
7. **The route calls into `app/services/`**, which asks
   `app/repositories/social_repository.py` for raw fixture data and
   converts it into schema objects (`app/schemas/`) — this is where
   `camelCase` conversion happens automatically via `CamelModel`'s
   `alias_generator`.
8. **`fake_io_operation`** (`app/common/fake_io.py`) wraps the
   configured `SIMULATED_IO_MS` delay in a `try/finally` — this
   guarantees its "end" log line fires even if something inside raises
   or the request gets cancelled mid-wait.
9. **FastAPI serializes the returned Pydantic model to JSON** and sends
   it back through ASGI's two-message `send()` pattern (the same
   pattern the raw lab does by hand).
10. **If anything raised an exception** at any point in steps 5–9, one
    of the handlers in `app/common/error_handlers.py` catches it
    instead, and builds the `{"error": {...}, "requestId": ...}`
    envelope — the client never sees FastAPI's default error shape.
11. **`RequestIdMiddleware` finishes**, logs
    `METHOD PATH STATUS DURATION request_id=...`, and attaches
    `X-Request-Id` to the response headers.

## Why lifespan differs between the two apps

`labs/raw_asgi/app.py` runs with `--lifespan off` — it has nothing to
set up (no database, no cache), so instead of writing code to
participate in a handshake it doesn't need, the flag tells Uvicorn to
skip offering it entirely.

`app/main.py`'s `lifespan` function currently does nothing either
(`yield` with no setup) — but it's written as a *real* lifespan handler,
not disabled, because this app already has `db.py` (a Postgres pool)
waiting in the wings for Stage C. When persistence is added, opening
that pool on startup — and closing it on shutdown — goes directly into
this function without restructuring anything else.

## Why an async route can still block

`async def` alone doesn't make code non-blocking — it only means the
function *can* pause and let other work happen while it's waiting.
If any code inside actually calls a **synchronous, blocking** function
(`time.sleep`, a non-async database driver, a blocking file read), the
entire event loop freezes for every other request being served at the
same time — not just the one that called it. This is exactly why
`fake_io.py` uses `await asyncio.sleep(...)`, never `time.sleep(...)`:
`asyncio.sleep` yields control back to the event loop, letting other
requests actually run during the wait — which is what
`tests/test_concurrency.py` measures directly (3 concurrent requests
finishing in ~1x the delay, not 3x).