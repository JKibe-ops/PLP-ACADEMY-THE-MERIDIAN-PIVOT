# Solstice Async Check-in

A solo implementation of the Solstice Events Co. badge check-in pivot.

The app demonstrates an asynchronous print workflow:

1. A staff member selects an attendee and simulates a QR scan.
2. The app publishes a print request to a queue.
3. The attendee stays in `pending` until a printer webhook confirms completion.
4. The UI changes to `checked in` only after that confirmation.
5. A second scan for the same attendee is blocked, so no second badge is printed.

## First-time setup

Requirements:

- Node.js 18 or newer
- npm

From this folder, install dependencies and start the development server:

```bash
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

When the dev server is started with network access enabled, the current browser link is:

**http://192.168.0.111:5174/**

Open it from a device on the same network. The development server must remain running, and the address may change if the computer joins a different network.

## Try the flow

1. Keep the **Kiosk** view selected.
2. Choose one of the three sample attendees.
3. Select **Simulate QR scan**.
4. Watch the state change from `pending` to `checked in` after the webhook confirmation.
5. Select the scan button again to see the duplicate scan protection.
6. Open **Operations** to review the roster and event stream.
7. Use **Reset simulation** to return to the initial state.

## Production build

```bash
npm run build
```

The build output is written to `dist/`. It is intentionally ignored by Git, along with `node_modules/`.

## Project layout

- `src/App.tsx`: kiosk UI, operations view, simulation state, queue events, and webhook transition
- `src/styles.css`: responsive visual system and layout
- `src/main.tsx`: React entry point
- `vite.config.ts`: Vite configuration

This repository is a solo Solstice project. It contains no group-project or Northstar sprint material.

## Meridian pivot mini-prototype

The non-TypeScript learning prototype is in [`meridian-pivot-prototype`](meridian-pivot-prototype). It uses FastAPI to model the queue and webhook version of the check-in flow:

```bash
cd meridian-pivot-prototype
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/` for the Python-served browser UI or `http://127.0.0.1:8000/docs` for the interactive API. Run `python -m pytest -q` to verify pending state, duplicate protection, and replay-safe webhook handling. The independent learning record is in [`LEARNING_BLOCKER_JOURNAL.md`](meridian-pivot-prototype/LEARNING_BLOCKER_JOURNAL.md).

The final pivot accounting is in [`SCOPE_DELTA_ANALYSIS.md`](SCOPE_DELTA_ANALYSIS.md), covering dropped, modified, and added work, deadline trade-offs, and regression checks.
