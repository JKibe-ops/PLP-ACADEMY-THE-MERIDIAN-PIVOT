# Learning & Blocker Journal

## Prototype scope

Build a small working async check-in service with FastAPI, without TypeScript. The prototype needed to show a queue-backed print request, delayed webhook confirmation, duplicate-scan protection, and replay-safe callbacks.

## Tool reconnaissance

**Unfamiliar tool:** FastAPI.

**Why it was selected:** FastAPI exposes typed HTTP routes quickly, generates an OpenAPI page automatically, and makes it straightforward to separate the scan command from the webhook callback. The goal was to learn the request/response and dependency patterns rather than hide the behavior behind a framework abstraction.

## Resources consulted

- FastAPI first steps: https://fastapi.tiangolo.com/tutorial/first-steps/
- FastAPI request body documentation: https://fastapi.tiangolo.com/tutorial/body/
- FastAPI header parameter documentation: https://fastapi.tiangolo.com/tutorial/header-params/
- FastAPI testing documentation: https://fastapi.tiangolo.com/tutorial/testing/
- Python `asyncio` task documentation: https://docs.python.org/3/library/asyncio-task.html
- Uvicorn settings documentation: https://www.uvicorn.org/settings/

## Work log

### Recon: dependency and route shape

- **Question:** How does FastAPI turn a Python function into a JSON endpoint?
- **Action:** Built a minimal `FastAPI()` app, added a typed Pydantic request body, and used the generated `/docs` page to inspect the contract.
- **Result:** `/health`, `/scan`, `/queue`, and `/attendees` were available as documented routes.

### Blocker 1: webhook header was not reaching the handler

- **Error observed:** The first callback attempt returned `401 Invalid webhook secret` even though the secret was sent by the test client.
- **Cause:** The handler expected a normal Python argument name, but FastAPI maps HTTP headers using its header parameter conversion. The callback test used `x-webhook-secret`, while the first draft read a differently named argument.
- **Resolution:** Declared the parameter with `Header(default=None)` and used the explicit `x_webhook_secret` name. The request now maps `x-webhook-secret` correctly.
- **Independent check:** Sent one callback with the header and one without it; the first processed and the second returned `401`.

### Blocker 2: duplicate scans could leave two jobs in the queue

- **Error observed:** A second `POST /scan` initially appended another job while the first attendee was still pending.
- **Cause:** The first draft checked only for `checked-in`, not for every non-ready state.
- **Resolution:** Made `ready` the only state allowed to create a job. Both `pending` and `checked-in` now produce a duplicate response and leave the queue unchanged.
- **Independent check:** The test scans `SOL-002` twice and asserts that the queue length remains `1`.

### Blocker 3: callback replay could mutate state twice

- **Error observed:** Replaying the same vendor callback returned a second successful transition in the first draft.
- **Cause:** The callback path did not distinguish an already completed attendee from a new completion.
- **Resolution:** Added an idempotency guard: when the attendee is already `checked-in`, remove any matching stale queue item and return `ignored`.
- **Independent check:** The replay test expects `processed` on the first callback and `ignored` on the second.

### Blocker 4: deque cleanup used unsupported slice assignment

- **Error observed:** The first focused test run failed with `TypeError: sequence index must be integer, not 'slice'` at the webhook queue cleanup line.
- **Cause:** Python `collections.deque` supports `clear()` and `extend()`, but it does not support list-style slice assignment.
- **Resolution:** Filtered the remaining jobs into a list, cleared the deque, and extended it with the filtered jobs.
- **Independent check:** Reran the complete test file and verified that callback completion removes the job without raising.

## Validation record

- `python -m pytest -q`: verifies pending-before-webhook, duplicate protection, and replay-safe callback behavior. On Windows, invoking pytest through Python avoids a user-level Scripts directory PATH issue.
- `uvicorn app:app --reload`: manual smoke path available through `/docs`.
- No direct technical how-to help was used during the prototype work; the listed documentation was consulted independently.

## Remaining limitation

The queue is intentionally in memory for a time-boxed mini-prototype. A production version would use a durable broker, persistent attendee state, signed callbacks, retry policy, and an outbox or transactional publish boundary.
