import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import *
from mail_store import MailStore
from audit_log import Trace
from preference_store import PreferenceMemory
from agent import classify, grounded_reply
from actions import ActionGate
from rules import INJECT_PATTERNS, PHISH_PATTERNS, hits, rule
from commitments import extract, conflicts
from dashboard.dashboard import write
from llm_client import GeminiClient


def load(clear_trace=True):
    if clear_trace and TRACE.exists():
        TRACE.unlink()
    OUTBOX.mkdir(exist_ok=True)
    return MailStore(INBOX), Trace(TRACE), PreferenceMemory(PREFS)


def r1(mail_store, audit_log, preference_store):
    llm = GeminiClient()
    decisions, rule_count, model_count = [], 0, 0
    for message in mail_store.messages:
        d = classify(message, mail_store, preference_store, llm=llm, audit_log=audit_log)
        decisions.append({"message_id": message["id"], **d})
        if d["path"] in {"noise", "injection", "phishing"}:
            rule_count += 1
        if d["path"] == "model":
            model_count += 1
        audit_log.log("action_plan", cap="R1", message_id=message["id"], **d)
    DECISIONS.write_text(json.dumps(decisions, indent=2), encoding="utf8")
    undecided = sum(1 for x in decisions if not x.get("disposition"))
    print(f"processed: {len(decisions)} rule_handled: {rule_count} model_classified: {model_count} undecided: {undecided}")
    return decisions


def r2(mail_store, audit_log, preference_store):
    result = grounded_reply(mail_store, "m008", audit_log)
    print(json.dumps(result, indent=2))
    if result is None:
        print("No draft created because the required information was not grounded in the inbox.")


def r3(mail_store, audit_log, preference_store, dry=True, approved=False):
    approval_guard = ActionGate(OUTBOX, audit_log, dry_run=dry, approved=approved)
    result = approval_guard.send("m046", "editor@techbrief.news", "Re: Quick question for our launch coverage", "Draft awaiting human approval.")
    print("proposed:", result)
    print("outbox/ writes:", len(list(OUTBOX.glob("*.json"))))


def _r4_restart_phase():
    mail_store, audit_log, preference_store = load(clear_trace=False)
    result = classify(mail_store.get("m043"), mail_store, preference_store)
    audit_log.log("preference_reused", cap="R4", message_id="m043", result=result)
    print("fresh process preference:", json.dumps(result))


def r4(mail_store, audit_log, preference_store):
    preference_store.remember({"key": "meeting_earliest", "value": "11:00", "source_message_id": "m041"})
    audit_log.log("preference_saved", cap="R4", message_id="m041", key="meeting_earliest")
    # Start a genuinely new Python process so the demonstration is end-to-end across exit/restart.
    cmd = [sys.executable, str(Path(__file__).resolve()), "--r4-restart"]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("saved preference:", json.dumps(preference_store.data, indent=2))
    print(completed.stdout.strip())


def r5(mail_store, audit_log, preference_store, verbose=True, cap="R5"):
    flagged = []
    for message in mail_store.messages:
        matched = hits(message, INJECT_PATTERNS)
        if matched:
            item = {
                "message_id": message["id"],
                "attempted": "; ".join(matched),
                "instead": "Refused; flagged; left in place; no outbox action."
            }
            flagged.append(item)
            audit_log.log("refusal", cap=cap, **item)
            if verbose:
                print(f"FLAGGED: {message['id']} -> {item['attempted']}")
    return flagged


def r6(mail_store, audit_log, preference_store):
    decisions = json.loads(DECISIONS.read_text(encoding="utf8")) if DECISIONS.exists() else r1(mail_store, audit_log, preference_store)
    flagged = r5(mail_store, audit_log, preference_store, verbose=False, cap="R6")
    flagged_ids = {x["message_id"] for x in flagged}
    # Add phishing/high-impact messages to the flagged pane; no action is taken.
    for message in mail_store.messages:
        if message["id"] in flagged_ids:
            continue
        if hits(message, PHISH_PATTERNS):
            item = {
                "message_id": message["id"],
                "attempted": "; ".join(hits(message, PHISH_PATTERNS)),
                "instead": "Refused; flagged for human review; left in place."
            }
            flagged.append(item)
            audit_log.log("refusal", cap="R6", **item)
    flagged_ids = {x["message_id"] for x in flagged}
    pending = []
    # The dashboard's pending pane is intentionally narrow: it contains actions
    # inboxHero would like to take but cannot perform without the human approval_guard.
    if mail_store.get("m043") and "m043" not in flagged_ids:
        pending.append({
            "message_id": "m043",
            "action": "send scheduling reply offering 11:00 or later",
            "why": "stored preference forbids accepting a 09:00 meeting; sending is irreversible and needs approval"
        })
    pending.append({
        "message_id": "m046",
        "action": "send launch-coverage reply",
        "why": "reply would leave the system in the owner's name; ActionGate requires dry-run or explicit approval"
    })
    commitments = extract(mail_store)
    conflict_list = conflicts(commitments)
    for item in commitments:
        audit_log.log("commitment", cap="R6", **item)
    for item in conflict_list:
        audit_log.log("conflict", cap="R6", **item)

    write(DASHBOARD, DASHJSON, pending, flagged, commitments, conflict_list)
    print(f"dashboard.html written; commitments: {len(commitments)} conflicts: {len(conflict_list)}")


def x1(mail_store, audit_log, preference_store):
    owner = "sam@paperjet.io"
    sent = [m for m in mail_store.messages if m["from"].lower() == owner]
    result = []
    latest = max(datetime.fromisoformat(m["timestamp"]) for m in mail_store.messages)
    for sent_msg in sent:
        answered = any(
            other["thread_id"] == sent_msg["thread_id"]
            and other["timestamp"] > sent_msg["timestamp"]
            and other["from"].lower() != owner
            for other in mail_store.messages
        )
        days = (latest - datetime.fromisoformat(sent_msg["timestamp"])).days
        if not answered and days >= 3:
            result.append({
                "message_id": sent_msg["id"],
                "days_waiting": days,
                "draft": "Hi, just following up on the request below. Please let me know when you have an update."
            })
    print(json.dumps(result, indent=2))
    audit_log.log("capability", cap="X1", result=result)
    return result


def x2(mail_store, audit_log, preference_store):
    decisions = json.loads(DECISIONS.read_text(encoding="utf8")) if DECISIONS.exists() else r1(mail_store, audit_log, preference_store)
    needs = [x for x in decisions if x["disposition"] != "archive"]
    waiting = [x for x in decisions if x["disposition"] == "defer"]
    archived = [x for x in decisions if x["disposition"] == "archive"]
    print("NEEDS YOU")
    for x in needs[:12]: print(f"- {x['message_id']}: {x['reason']}")
    if len(needs) > 12: print(f"- ... {len(needs)-12} more")
    print(f"\nCAN WAIT\n- {len(waiting)} messages deferred")
    print(f"\nAUTO-ARCHIVED\n- {len(archived)} messages")
    audit_log.log("capability", cap="X2", needs=len(needs), can_wait=len(waiting), archived=len(archived))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cap", choices=["R1", "R2", "R3", "R4", "R5", "R6", "X1", "X2"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--r4-restart", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.r4_restart:
        _r4_restart_phase()
        return

    mail_store, audit_log, preference_store = load()
    if args.all:
        r1(mail_store, audit_log, preference_store)
        r2(mail_store, audit_log, preference_store)
        r3(mail_store, audit_log, preference_store, dry=True)
        r4(mail_store, audit_log, preference_store)
        r5(mail_store, audit_log, preference_store)
        r6(mail_store, audit_log, preference_store)
        x1(mail_store, audit_log, preference_store)
        x2(mail_store, audit_log, preference_store)
        return
    if not args.cap:
        parser.error("use --cap R1..R6/X1/X2 or --all")
    funcs = {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6, "X1": x1, "X2": x2}
    if args.cap == "R3":
        funcs[args.cap](mail_store, audit_log, preference_store, dry=args.dry_run or not args.approve, approved=args.approve)
    else:
        funcs[args.cap](mail_store, audit_log, preference_store)

if __name__ == "__main__":
    main()
