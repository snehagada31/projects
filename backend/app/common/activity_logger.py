"""
Activity audit logger with ISO UTC timestamps.
Logs user actions with actor, action, and target context
(e.g., '@asha liked @devpatel's post').
"""

import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger("app.activity")
logging.basicConfig(level=logging.INFO)

# File handler for local log persistence in backend/logs/activity.log
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "activity.log")


def get_utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log_activity(actor: str, action: str, target: str | None = None, details: str | None = None):
    """
    Emits an audit log entry in UTC time to both standard output and backend/logs/activity.log.
    Example:
    [2026-10-30T12:05:00.123Z UTC] 🔔 ACTION: @asha liked @devpatel's post (post_id=...)
    """
    timestamp = get_utc_now_iso()
    actor_str = f"@{actor.lstrip('@')}" if actor else "@unknown"

    if target:
        msg = f"[{timestamp} UTC] 🔔 ACTION: {actor_str} {action} {target}"
    else:
        msg = f"[{timestamp} UTC] 🔔 ACTION: {actor_str} {action}"

    if details:
        msg += f" | {details}"

    logger.info(msg)
    # Also print directly to ensure visibility in standard output / Render terminal logs
    print(msg, flush=True)

    # Persist directly to backend/logs/activity.log file
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
