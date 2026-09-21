## Run

Install Uvicorn if needed:

    pip install uvicorn

Run from inside `labs/raw_asgi`:

    uvicorn app:app --lifespan off

Visit:
    http://127.0.0.1:8000/health/live
    http://127.0.0.1:8000/feed