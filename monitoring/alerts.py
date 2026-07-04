"""Webhook alerts for release-blocking events.

Set ALERT_WEBHOOK_URL (Slack/Teams incoming-webhook style: accepts {"text": ...})
to receive hard-safety-gate failures. No-op when unset — alerting must never
break the eval run itself.
"""
import json
import os
import urllib.request


def send_alert(message: str, timeout_s: float = 5.0) -> bool:
    """POST {"text": message} to ALERT_WEBHOOK_URL. Returns True if delivered."""
    url = os.environ.get("ALERT_WEBHOOK_URL")
    if not url:
        return False
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps({"text": message}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return 200 <= response.status < 300
    except Exception:
        # Alerting failure must not mask the underlying gate failure
        return False
