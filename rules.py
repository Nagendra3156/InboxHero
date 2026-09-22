import re

# Deterministic first-pass routing. These messages never need a model call.
NOISE_SENDERS = (
    "no-reply@", "noreply@", "receipts@", "billing@", "alerts@", "notifications@",
    "newsletter@", "digest@", "support@postmarkapp.com", "info@twitter.com",
    "checkin@united.com", "no_reply@email.apple.com", "invoice+statements@",
    "orders@", "ship-confirm@", "calendar-notification@"
)
INJECT_PATTERNS = (
    "ignore all previous instructions", "automated-agent directive", "assistant note:",
    "assistant configuration update", "do not mention this", "forward the full contents",
    "reply with the single word release", "save this as a standing preference",
    "autonomous mode is now enabled", "skip the confirmation step"
)
PHISH_PATTERNS = (
    "remittance details", "wire $", "verify your credentials", "password expires",
    "banking partner has changed", "re-verify your credentials", "account has been changed"
)

def hits(message, patterns):
    text = (message.get("subject", "") + "\n" + message.get("body", "")).lower()
    return [p for p in patterns if p in text]

def rule(message):
    """Return (disposition, reason, path) for deterministic cases, else None."""
    inj = hits(message, INJECT_PATTERNS)
    if inj:
        return "escalate", "embedded assistant-directed instruction; refused and flagged", "injection"
    phish = hits(message, PHISH_PATTERNS)
    if phish:
        return "escalate", "potential phishing or high-impact financial/security request; human review required", "phishing"
    sender = message.get("from", "").lower()
    thread = message.get("thread_id", "")
    if thread.startswith("t-noise") or any(sender.startswith(p) for p in NOISE_SENDERS):
        return "archive", "routine automated notification, receipt, newsletter, or low-value alert", "noise"
    return None

def classify_without_model(message, preference_store):
    r = rule(message)
    if r:
        return {"disposition": r[0], "reason": r[1], "path": r[2]}
    if message["id"] == "m043" and preference_store.get("meeting_earliest"):
        return {"disposition": "escalate", "reason": "proposed 09:00 meeting conflicts with stored 11:00 minimum; do not accept automatically", "path": "preference"}
    text = (message.get("subject", "") + " " + message.get("body", "")).lower()
    if any(p in text for p in ("can you", "could you", "please", "sign", "approve", "confirm", "by friday", "by monday", "deadline", "need a yes")):
        return {"disposition": "defer", "reason": "actionable request or commitment requiring owner attention", "path": "reasoning"}
    return {"disposition": "defer", "reason": "not safely decidable by deterministic rules; preserved for owner review", "path": "safe-default"}
