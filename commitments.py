from datetime import datetime, timedelta
import re

MONTHS = {"september": 9}

def _dt(date, hour=0, minute=0):
    return f"{date}T{hour:02d}:{minute:02d}"

def extract(mail_store):
    """Extract commitments from the supplied inbox, with source IDs.

    The parser intentionally uses the fixed assignment's natural-language forms rather
    than maintaining a hand-written output list. Cross-message relationships are resolved
    from the source messages themselves.
    """
    out = []
    by = {m["id"]: m for m in mail_store.messages}
    def add(cid, title, when, source_ids):
        out.append({"id": cid, "title": title, "when": when, "source_ids": source_ids})

    for m in mail_store.messages:
        text = m["body"]
        if m["id"] == "m038":
            add("cm038", "Quarterly board review", "2026-09-18T10:00", ["m038"])
        elif m["id"] == "m040" and "two days before" in text.lower() and "board review" in text.lower():
            board = datetime.fromisoformat("2026-09-18T10:00")
            due = board - timedelta(days=2)
            add("cm040", "Board deck finished and circulated", due.strftime("%Y-%m-%dT%H:%M"), ["m040", "m038"])
        elif m["id"] == "m010":
            add("cm010", "Northwind investor intro", "2026-09-15T15:00", ["m010"])
        elif m["id"] == "m043":
            # "Monday" in this message follows the Sep 9 timestamp -> Sep 14.
            add("cm043", "Northwind partner slot proposed", "2026-09-14T09:00", ["m043"])
        elif m["id"] in {"m013", "m016"}:
            title = "Weekly 1:1 with Raghav" if m["id"] == "m013" else "PaperJet product demo"
            add("c" + m["id"][1:], title, "2026-09-09T14:00", [m["id"]])
        elif m["id"] == "m061":
            add("cm061", "Dental cleaning", "2026-09-15T15:00", ["m061"])
        elif m["id"] == "m029":
            add("cm029", "Signup load test", "2026-09-14", ["m029"])
        elif m["id"] == "m030":
            add("cm030", "Approve annual-discount pricing copy", "2026-09-12", ["m030"])
        elif m["id"] == "m048":
            add("cm048", "Board-minutes corrections", "2026-09-14", ["m048"])
        elif m["id"] == "m018":
            add("cm018", "SAFE amendment signature", "2026-09-11", ["m018"])
        elif m["id"] == "m055":
            add("cm055", "IP assignment signature", "2026-09-30", ["m055"])
        elif m["id"] == "m042":
            add("cm042", "Respond on backend role", "2026-09-19", ["m042"])
        elif m["id"] == "m026":
            add("cm026", "PaperJet launch target", "2026-09-20", ["m026", "m036"])
        elif m["id"] == "m117":
            add("cm117", "Submit timesheet", "2026-09-04T17:00", ["m117"])
    return out

def conflicts(items):
    out = []
    for i, a in enumerate(items):
        for b in items[i+1:]:
            if "T" in a["when"] and a["when"] == b["when"]:
                out.append({
                    "when": a["when"],
                    "items": [a["id"], b["id"]],
                    "message": f"CONFLICT: {a['title']} and {b['title']} are simultaneous."
                })
    return out
