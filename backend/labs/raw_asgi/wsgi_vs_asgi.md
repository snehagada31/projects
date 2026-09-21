
**Note:** Run the command from inside `labs/raw_asgi`.

---

## Step 4: `wsgi_vs_asgi.md`

The PRD asks for a **short comparison**, not a long essay.

````md
# WSGI vs ASGI

## WSGI

- Designed for synchronous Python web applications.
- Handles one request at a time per worker.
- Does not natively support WebSockets or long-lived async connections.

## ASGI

- Designed for asynchronous applications.
- Supports HTTP, WebSockets, and lifespan events.
- Allows non-blocking I/O using `async` and `await`.

## Uvicorn vs FastAPI

- **Uvicorn** is the ASGI server. It receives requests and communicates with ASGI applications.
- **FastAPI** is an ASGI application framework that builds APIs on top of the ASGI interface.

In this lab, Uvicorn runs our raw ASGI application directly without FastAPI.