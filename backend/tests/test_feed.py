"""
Covers the acceptance table's feed cases: default page size, no
duplicates/skips across continuations, the deliberate timestamp tie,
and the query-validation rejections.
"""

from app.fixtures.social_fixtures import ORIGINALS


def test_default_feed_page_size(client):
    r = client.get("/feed")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) <= 10
    assert body["hasMore"] is True
    assert body["nextCursor"] is not None


def test_three_pages_no_duplicates_no_skips(client):
    seen_ids = []
    cursor = None

    for _ in range(3):
        url = "/feed" if cursor is None else f"/feed?cursor={cursor}"
        r = client.get(url)
        body = r.json()
        seen_ids.extend(item["id"] for item in body["items"])
        cursor = body["nextCursor"]

    assert len(seen_ids) == len(set(seen_ids)), "duplicate post across pages"
    assert len(seen_ids) == 30, "should see all 30 originals across exactly 3 pages of 10"


def test_tied_timestamp_originals_both_appear(client):
    """The two originals sharing an identical created_at must BOTH show up
    somewhere in the feed, not have one silently dropped."""
    tied_ids = {
        p["id"] for p in ORIGINALS
        if p["created_at"] == ORIGINALS[4]["created_at"]
    }
    assert len(tied_ids) == 2

    seen_ids = set()
    cursor = None
    for _ in range(10):
        url = "/feed" if cursor is None else f"/feed?cursor={cursor}"
        r = client.get(url)
        body = r.json()
        seen_ids.update(item["id"] for item in body["items"])
        cursor = body.get("nextCursor")
        if tied_ids.issubset(seen_ids) or not body.get("hasMore") or not cursor:
            break

    missing = tied_ids - seen_ids
    assert not missing, f"missing: {missing}\nsample seen: {sorted(seen_ids)[:5]}"

def test_invalid_limit_returns_400(client):
    r = client.get("/feed?limit=abc")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_limit_over_50_returns_400(client):
    r = client.get("/feed?limit=51")
    assert r.status_code == 400


def test_duplicate_param_returns_400(client):
    r = client.get("/feed?limit=5&limit=10")
    assert r.status_code == 400
    assert r.json()["error"]["details"][0]["field"] == "limit"


def test_legacy_page_param_returns_400(client):
    r = client.get("/feed?page=2")
    assert r.status_code == 400


def test_response_has_request_id_header(client):
    r = client.get("/feed")
    assert "x-request-id" in r.headers
