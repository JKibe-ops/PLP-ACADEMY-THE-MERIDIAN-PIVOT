# Scope Delta Analysis

**Project:** Solstice Events Co. async badge check-in

**Delivery mode:** Solo implementation

**Original deadline:** The existing delivery deadline remained fixed after the vendor announcement.

**Pivot:** The badge-printer vendor deprecated the synchronous REST print API. The check-in service had to move to a message-queue request plus an application webhook callback, with no deadline extension and no scope negotiation back to the synchronous design.

## Executive summary

The original check-in behavior was preserved at the user-outcome level: a valid attendee can receive one badge, the screen confirms check-in only after successful printing, and duplicate scans do not print another badge. The implementation boundary changed from a blocking vendor call to an asynchronous queue and webhook lifecycle.

The pivot was absorbed by narrowing the deliverable to a working, observable prototype with an in-memory queue and deterministic tests. Production broker infrastructure, persistence, retry workers, and a full hardware QR reader were deliberately deferred rather than pretending they were complete.

## Before and after

| Area | Original specification | Final pivot specification | Delta |
| --- | --- | --- | --- |
| Print request | Call vendor REST API synchronously | Publish a print job to a queue | **Modified** |
| Request timing | Wait for vendor success response in the scan request | Return `202 Accepted` while the job is pending | **Modified** |
| UI state | Show `Checked In` after synchronous print success | Show `pending`, then `Checked In` only after webhook confirmation | **Modified** |
| Completion signal | Inline REST response | `POST /webhooks/print-complete` callback | **Added** |
| Duplicate protection | Reject an attendee already checked in | Reject both pending and checked-in scans; do not create a second job | **Modified** |
| Callback ordering | Not applicable | Completion callbacks can arrive late or be replayed safely | **Added** |
| Attendee coverage | At least three attendees, including a duplicate scan | Three seeded attendees plus automated duplicate and replay tests | **Retained and strengthened** |
| Operations visibility | Not specified | Queue inspection and event stream endpoints/UI | **Added** |

## Dropped work

These items belonged to the original synchronous implementation or were intentionally removed from the fixed-deadline slice:

- Synchronous vendor REST printing and waiting for its inline success response.
- Any UI path that marks an attendee checked in immediately after the scan request is sent.
- Running the old synchronous and new asynchronous print paths in parallel. The obsolete path is absent from the prototype.
- A production message broker, durable queue storage, and a worker fleet. These require infrastructure and operational decisions outside the time-boxed prototype.
- A physical QR scanner integration. The prototype uses a documented scan request so the asynchronous contract can be tested deterministically.

## Modified work

- **Check-in state machine:** `ready -> pending -> checked-in` replaces `ready -> checked-in`.
- **Scan endpoint:** returns `202 Accepted` with a job ID instead of blocking until printing finishes.
- **Print completion:** moves from the scan response to a signed-secret-protected webhook callback.
- **Duplicate rule:** only `ready` attendees may create a print job. `pending` and `checked-in` both reject a scan.
- **Queue handling:** jobs are removed by ID when a callback arrives, allowing unrelated jobs to remain queued.
- **Completion handling:** a replayed callback returns `ignored` instead of mutating state a second time.
- **User-facing visibility:** pending status and event activity make the asynchronous handoff observable.

## Added work

- `POST /webhooks/print-complete` callback endpoint.
- `POST /vendor/complete` local vendor callback simulator for repeatable testing.
- `GET /queue` and `GET /events` inspection endpoints.
- Webhook secret validation through `x-webhook-secret`.
- Idempotent callback handling for duplicate or out-of-order delivery.
- Focused tests covering pending-before-webhook, duplicate scan protection, and callback replay.
- Learning and blocker journal documenting independent tool discovery and troubleshooting.

## Deadline trade-offs

| Decision | Reason under fixed deadline | Risk accepted | Follow-up for production |
| --- | --- | --- | --- |
| In-memory attendee state | Keeps the pivot runnable without database setup | State is lost on restart | Persist state and enforce a unique attendee/job constraint |
| In-memory queue | Makes queue publication and removal visible in a small prototype | No durability or cross-process delivery | Use the vendor-approved broker and a durable consumer |
| Shared demo webhook secret | Makes local callback testing immediate | Not suitable for real deployment | Verify signed payloads, timestamp, and replay nonce |
| Local vendor simulator | Allows the webhook contract to be exercised without vendor credentials | Does not prove vendor-specific production behavior | Contract-test against the vendor sandbox |
| API-driven scan simulation | Keeps the acceptance path deterministic | No hardware integration | Add scanner adapter after the queue contract is stable |

## Regression check

The following acceptance checks cover the original requirements and the pivot:

1. **Three attendees:** `SOL-001`, `SOL-002`, and `SOL-003` are seeded and available through `GET /attendees`.
2. **No premature check-in:** after `POST /scan`, the attendee is `pending`, the response is `202`, and a job exists in `GET /queue`.
3. **Webhook confirmation:** a valid callback changes the attendee to `checked-in` and removes the matching job.
4. **Duplicate while pending:** a second scan does not append another queue job.
5. **Duplicate after completion:** a scan after `checked-in` is rejected and cannot print another badge.
6. **Replay safety:** the same callback twice produces `processed` then `ignored`.
7. **Webhook authentication:** a callback without the expected secret is rejected with `401`.
8. **Automated result:** `python -m pytest -q` passes all three focused prototype tests.

## Deliverable map

- [FastAPI prototype](meridian-pivot-prototype/app.py)
- [Python-served browser UI](meridian-pivot-prototype/static/index.html)
- [Prototype tests](meridian-pivot-prototype/test_app.py)
- [First-time prototype guide](meridian-pivot-prototype/README.md)
- [Learning and blocker journal](meridian-pivot-prototype/LEARNING_BLOCKER_JOURNAL.md)
- [Browser experience](README.md)

## Final assessment

The pivot is complete within the original deadline boundary for this prototype. The old synchronous behavior was removed from the active path, the new asynchronous lifecycle is executable, duplicate protection survives pending and callback replay conditions, and the remaining production gaps are named rather than hidden.
