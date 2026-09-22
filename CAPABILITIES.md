# CAPABILITIES.md — inboxHero

**Student:** Siripuram Nagendra Babu, evernorth-aai-1169081 
**Repository:** https://github.com/Nagendra3156/InboxHero

Run one capability with:

```text
python demo.py --cap R1
```

Run the complete sequence with:

```text
python demo.py --all
```

## The system, in one paragraph

A single Python system with no agent framework. The supplied 100-message inbox is loaded once; obvious receipts, newsletters, notifications, phishing patterns, and assistant-directed hostile instructions are dispatched by deterministic rules before any optional model call. Unresolved messages use a safe classification path, with an optional Gemini adapter when configured. Grounded replies use thread-walk retrieval, preferences persist in `state/preferences.json`, and irreversible actions are isolated behind `ActionGate`.

## Design choices you were asked to state

- **Framework: none.** The system has explicit mail_router, retrieval, preference_store, dashboard and action-approval_guard components; a framework would add abstraction without improving the assignment's visible safety boundary.
- **Model:** Gemini 3.5 Flash-Lite is the optional provider configured through `GEMINI_API_KEY` and `GEMINI_MODEL`. The submitted project also runs without a provider key using deterministic rules and safe defaults.
- **Messages:** 100. The current no-provider run handles 62 messages through deterministic rules and leaves no message undecided. The remaining messages follow the reasoning/safe-default path.
- **Dispositions:** `reply`, `archive`, `defer`, `delegate`, `escalate`. Every message receives exactly one.
- **Retrieval:** `thread-walk` first, with keyword fallback. The required grounded case is `m008`, which cites earlier `m003`.
- **Irreversible:** `send` and `delete`. Send has no unsend operation; delete is irreversible because the mock mail_store has no trash/recovery contract.
- **Reversible:** `draft`, `label`, `archive`, `defer`.
- **Gate:** both dry-run and explicit approval are implemented. `ActionGate` is the only component allowed to write an approved send into `outbox/`.
- **Escalation line:** financial transfers, credential/security requests, legal/high-impact actions, hostile instructions and preference conflicts remain for human review. The trade-off is less autonomy for high-impact work in exchange for a smaller irreversible-action surface.

## Capabilities

| id | name | tier | one-line claim |
|---|---|---|---|
| R1 | Zero the inbox | B | Assigns exactly one disposition and reason to all 100 messages. |
| R2 | Grounded reply | B | Drafts m008 using earlier m003 and records the source ID. |
| R3 | Gate the irreversible | C | Prevents send/delete without dry-run or explicit approval. |
| R4 | Persistent preference | C | Persists m041's calendar preference and applies it after restart to m043. |
| R5 | Refuse embedded instructions | C | Refuses, flags and reports assistant-directed instructions. |
| R6 | Dashboard | C | Generates exactly three panes with cited commitments and surfaced conflicts. |
| X1 | Follow-up tracking | B | Finds unanswered sent mail waiting at least three days and drafts a chase. |
| X2 | Morning digest | B | Produces needs-you, can-wait and auto-archived sections. |

## Final Report

### 1. What did you refuse to automate?

The system deliberately refuses to automate `m023`, which asks for a $3,200 wire while asking the recipient to keep finance out of the loop, and it refuses the assistant-directed instructions in `m017`, `m024`, `m039`, and `m047`. These messages are flagged or escalated rather than forwarded, deleted, or sent. Security/credential messages such as `m021` and `m045` are also kept behind the review boundary. The trade-off is less autonomous completion for high-impact work in exchange for preventing untrusted email content from triggering irreversible effects.

### 2. Where does untrusted text enter your system?

Email content enters through `mail_store.py` as data and is passed to `rules.py`, retrieval, and, for unresolved messages, the optional model adapter. The architectural boundary is `actions.py`: model output and email content cannot directly create an irreversible effect because only `ActionGate` has access to the send/delete operations. An attacker would therefore have to defeat both the classification path and the separate action approval_guard rather than merely persuade the model through an email body.

### 3. Who is accountable when it sends the wrong thing?

The inbox owner is accountable for an approved message sent in the owner's name; inboxHero is the automation being audited, not the human action_plan-maker. The system records the message ID, proposed action, approval/dry-run result, and outbox filename in `audit_log.jsonl`. Dry-run allows the owner to inspect the exact proposed action before an outbox write. This gives a audit_log from source message through system proposal to the human authorization boundary.

### 4. Name your own machinery.

`agent.py` acts as the mail_router/classification layer, `retrieval.py` provides grounding, `preference_store.py` provides persistent state, `actions.py` is the tool/action boundary, and `demo.py` orchestrates the capabilities. These correspond to roles that a framework might expose as Agents, Tasks, orchestration/graph, Memory and Tools. A framework would provide standardized orchestration, retries and observability, but using none avoids introducing abstraction larger than the problem.

## Evidence map

- **R1:** `decisions.json`, `audit_log.jsonl`; one `action_plan` event per message.
- **R2:** `audit_log.jsonl` records `read(m003)` before `draft(m008)` and the draft cites `m003`.
- **R3:** `--dry-run` prints the proposed send and leaves `outbox/` unchanged; approval_guard events record the action_plan.
- **R4:** `state/preferences.json` is written before a fresh Python process reloads it and handles `m043`.
- **R5:** refusal events name hostile message IDs; no hostile request is written to `outbox/` and the source messages remain in the inbox.
- **R6:** `dashboard.html` and `dashboard.json` contain exactly three panes; commitments include source IDs and simultaneous commitments are listed under conflicts.
- **X1:** output contains only sent messages with no later same-thread reply and at least three days of waiting.
- **X2:** terminal output is derived from `decisions.json`.
