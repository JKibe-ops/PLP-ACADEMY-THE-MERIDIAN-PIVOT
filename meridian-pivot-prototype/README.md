# Meridian Pivot Mini-Prototype

This is a solo, non-TypeScript learning prototype for the Solstice Events Co. pivot. It uses **FastAPI**, an unfamiliar tool for this exercise, to model an asynchronous badge-print workflow.

## Run it

From this directory:

```bash
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

Open the Python browser UI at `http://127.0.0.1:8000/` or the interactive API page at `http://127.0.0.1:8000/docs`.

Try the flow:

1. `POST /scan` with `{ "attendee_id": "SOL-001" }`.
2. Confirm `GET /attendees` reports `pending` and `GET /queue` contains one print job.
3. Use the returned job ID with `POST /vendor/complete` to simulate the vendor callback.
4. Confirm the attendee becomes `checked-in`.
5. Call `POST /scan` for the same attendee again and confirm it is rejected as a duplicate.

The callback endpoint requires `x-webhook-secret: local-demo-secret`. The implementation removes a job by ID and treats replayed callbacks as no-ops, so confirmations can arrive late or more than once without printing a second badge.

This Python UI is the no-TypeScript path for the prototype. It serves the page, styling, and browser interactions from FastAPI while preserving the same queue, pending, webhook, checked-in, and duplicate-scan behavior.

## Tests

```bash
python -m pytest -q
```

## Files

- `app.py`: FastAPI service, in-memory queue, scan endpoint, vendor callback simulator, and webhook handler
- `test_app.py`: focused behavior tests for pending state, duplicate protection, and callback idempotency
- `LEARNING_BLOCKER_JOURNAL.md`: resources consulted, errors encountered, and independent resolutions
