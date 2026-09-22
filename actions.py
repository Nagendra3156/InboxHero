import json
from pathlib import Path

class ActionGate:
    def __init__(self, outbox: Path, audit_log, dry_run=False, approved=False):
        self.outbox = outbox
        self.audit_log = audit_log
        self.dry_run = dry_run
        self.approved = approved
        self.outbox.mkdir(parents=True, exist_ok=True)

    def send(self, message_id, to, subject, body):
        proposed = {"message_id": message_id, "action": "send", "to": to, "subject": subject, "body": body}
        if self.dry_run:
            self.audit_log.log("approval_guard", proposed=proposed, human="dry-run", result="suppressed")
            return "would_send"
        if not self.approved:
            self.audit_log.log("approval_guard", proposed=proposed, human="not-approved", result="blocked")
            return "blocked"
        target = self.outbox / f"{message_id}.json"
        target.write_text(json.dumps(proposed, indent=2), encoding="utf8")
        self.audit_log.log("approval_guard", proposed=proposed, human="approved", result="sent", outbox=str(target.name))
        return "sent"

    def delete(self, message_id):
        proposed = {"message_id": message_id, "action": "delete"}
        self.audit_log.log("approval_guard", proposed=proposed, human="not-allowed", result="blocked")
        return "blocked"
