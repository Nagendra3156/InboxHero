# inboxHero — Assignment 06

**Student** Siripuram Nagendra Babu, evernorth-aai-1169081 

**Repository:** https://github.com/Nagendra3156/InboxHero

## What this project demonstrates

inboxHero is a hand-built Python agentic inbox system. It processes all 100 supplied messages, routes obvious noise and hostile content through deterministic rules before any model call, uses explicit retrieval for grounded replies, persists owner preferences across process restarts, and places irreversible effects behind an `ActionGate`. The system also generates a reproducible three-pane dashboard and two additional capabilities: follow-up tracking and a morning digest.

This design follows the course progression from AI-enabled systems and prompt/RAG foundations through agent building blocks, architectural patterns, memory, tools, MCP/protocol boundaries, and agentic frameworks. The course page places Agentic AI, architectural patterns, memory/tools, protocols, and frameworks across Weeks 5–11; Assignment 06 is listed under Week 11.2.

## Framework choice

**Framework: none.** The assignment permits frameworks, but this system has a small number of explicit control points: rule router, optional model adapter, retrieval, persistent memory, commitment extraction, dashboard generation, and one irreversible-action gate. Keeping these as ordinary Python modules makes the safety boundary visible and easy to test. The framework roles are described explicitly in Final Report Q4.

## Setup

```bash
python -m venv .venv
pip install -r requirements.txt
copy .env.example .env       # Windows
```

The project runs without an API key. If a model provider is configured, unresolved messages can use Gemini for classification. No `.env` file is included in the submission.

## Run

Full reproducible run:

```bash
python demo.py --all
```

Individual capabilities:

```bash
python demo.py --cap R1
python demo.py --cap R2
python demo.py --cap R3 --dry-run
python demo.py --cap R4
python demo.py --cap R5
python demo.py --cap R6
python demo.py --cap X1
python demo.py --cap X2
```

### R3 approval example

Dry-run is the default safety demonstration:

```bash
python demo.py --cap R3 --dry-run
```

The gate shows the proposed send and writes nothing to `outbox/`. An explicit approval path is also implemented in code:

```bash
python demo.py --cap R3 --approve
```

The mock project writes only the approved message to `outbox/`; it never sends real email.

## Part 1 — Inbox assumptions

The supplied inbox contains 100 JSON message objects with the fields `id`, `thread_id`, `from`, `to`, `subject`, `timestamp`, `body`, and `unread`. Message IDs are not contiguous (for example, the dataset includes `m001`, `m003`, `m117`, `m119`), so all processing uses the actual IDs present in the file. The implementation does not assume that every numeric ID exists.

## Part 2 — Disposition vocabulary

Every message receives exactly one of:

- `reply` — a response is appropriate.
- `archive` — no owner action is required and the message is safe to remove from the active queue.
- `defer` — owner attention is needed, but inboxHero does not perform the action automatically.
- `delegate` — work should be handed to another human/team.
- `escalate` — security, financial, legal, hostile-instruction, or preference-conflict work requires human review.

The current safe implementation uses `archive`, `defer`, and `escalate` most heavily. Unused vocabulary is retained because the assignment requires a consistent defined vocabulary.

## Part 3 — Retrieval

Retrieval is **thread-walk first, keyword fallback second**. The required grounded case is `m008`: it asks for the staging queue URL that was previously sent to Raghav. inboxHero walks `t-api`, reads `m003`, verifies that `m003` exists in the store, extracts the URL from that source, and records `m003` as the citation in the draft. If the required source cannot be found, the system creates no grounded draft.

## Part 4 — Reversible vs irreversible

`draft`, `label`, `archive`, and `defer` are treated as reversible in this mock system. `send` is irreversible because there is no unsend operation, and `delete` is treated as irreversible because the mock store has no trash/recovery contract. Only `ActionGate.send()` and `ActionGate.delete()` can cross the irreversible boundary. The normal demonstration uses `--dry-run`, which shows the proposed action and writes zero outbox files; an explicit approval path is also implemented.

### Escalation boundary

inboxHero does not autonomously act on financial transfers, credential/security requests, legal signatures, hostile assistant-directed instructions, or preference conflicts. Routine automated mail can be archived by rules. This trades some automation for a much smaller irreversible-action surface and avoids asking the owner to approve every low-risk receipt or newsletter.

## Part 5 — Persistent preference

Message `m041` establishes the standing preference that meetings before 11:00 should not be accepted. `demo.py --cap R4` writes that preference to `state/preferences.json`, starts a fresh Python process, reloads the file, and then handles `m043` using the stored preference. The second process therefore demonstrates persistence across a real process boundary rather than merely reading an in-memory value.

## Part 6 — Hostile inbox

Hostile assistant-directed messages include `m017`, `m024`, `m039`, and `m047`. The system does not follow their embedded instructions, does not write an outbox message on their behalf, does not delete them, and records refusal events containing the message ID and attempted action. Phishing/high-impact messages such as `m021`, `m023`, and `m045` are also surfaced for human review.

## Part 7 — Dashboard

`python demo.py --cap R6` produces `dashboard.html` and `dashboard.json` from the completed run. The HTML has exactly three panes: **Pending actions**, **Flagged**, and **Commitments**. Commitments contain source message IDs, and the system surfaces simultaneous commitments as conflicts rather than silently listing them.

One multi-message commitment is the board-deck deadline: `m038` establishes the board review on September 18 at 10:00, while `m040` says the deck must be circulated two days before that review; the extractor resolves this to September 16 and cites both messages.

## Part 8 — Additional capabilities

### X1 — Follow-up tracking (Tier B)

Finds messages sent by the inbox owner that have received no later reply in the same thread and have been waiting at least three days relative to the latest message timestamp in the supplied dataset. It outputs the message ID, days waiting, and a follow-up draft.

### X2 — Morning digest (Tier B)

Produces a compact summary of messages needing owner attention, messages deferred for later, and the count of messages automatically archived. It is reproducible from `decisions.json` and can be run independently.

## Final Report

### 1. What did you refuse to automate?

The system deliberately refuses to automate `m023`, which asks for a $3,200 wire while asking the recipient to keep finance out of the loop, and it refuses the assistant-directed instructions in `m017`, `m024`, `m039`, and `m047`. These messages are flagged or escalated rather than forwarded, deleted, or sent. Security/credential messages such as `m021` and `m045` are also kept behind the review boundary. The trade-off is less autonomous completion for high-impact work in exchange for preventing untrusted email content from triggering irreversible effects.

### 2. Where does untrusted text enter your system?

Email content enters through `mail_store.py` as data and is passed to `rules.py`, retrieval, and, for unresolved messages, the optional model adapter. The architectural boundary is `actions.py`: model output and email content cannot directly create an irreversible effect because only `ActionGate` has access to the send/delete operations. An attacker would therefore have to defeat the classification path and the separate action gate rather than merely persuade the model through an email body.

### 3. Who is accountable when it sends the wrong thing?

The inbox owner is accountable for an approved message sent in the owner's name; inboxHero is the automation being audited, not the human decision-maker. The system records the message ID, proposed action, approval/dry-run result, and outbox filename in `audit_log.jsonl`. Dry-run allows the owner to inspect the exact proposed action before an outbox write. This gives a trace from source message through system proposal to the human authorization boundary.

### 4. Name your own machinery.

`agent.py` acts as the router/classification layer, `retrieval.py` provides grounding, `preference_store.py` provides persistent state, `actions.py` is the tool/action boundary, and `demo.py` orchestrates the capabilities. These correspond to roles that a framework might expose as Agents, Tasks, orchestration/graph, Memory, and Tools. A framework would provide standardized orchestration, retries, and observability, but using none here keeps the assignment's safety and protocol boundaries explicit and avoids introducing abstraction that is larger than the problem.
