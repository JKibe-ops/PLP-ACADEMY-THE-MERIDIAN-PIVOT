from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def setup_function() -> None:
    client.post("/reset")


def test_scan_stays_pending_until_webhook() -> None:
    accepted = client.post("/scan", json={"attendee_id": "SOL-001"})
    assert accepted.status_code == 202
    assert accepted.json()["attendee"]["status"] == "pending"
    job_id = accepted.json()["job"]["job_id"]

    before_callback = client.get("/attendees").json()[0]
    assert before_callback["status"] == "pending"

    callback = client.post(
        "/webhooks/print-complete",
        headers={"x-webhook-secret": "local-demo-secret"},
        json={"job_id": job_id, "attendee_id": "SOL-001", "outcome": "completed"},
    )
    assert callback.json()["attendee_status"] == "checked-in"


def test_duplicate_scan_does_not_create_second_job() -> None:
    first = client.post("/scan", json={"attendee_id": "SOL-002"}).json()
    second = client.post("/scan", json={"attendee_id": "SOL-002"}).json()

    assert first["accepted"] is True
    assert second["duplicate"] is True
    assert len(client.get("/queue").json()) == 1


def test_replayed_callback_is_idempotent() -> None:
    first = client.post("/scan", json={"attendee_id": "SOL-003"}).json()
    payload = {"job_id": first["job"]["job_id"], "attendee_id": "SOL-003", "outcome": "completed"}
    headers = {"x-webhook-secret": "local-demo-secret"}

    assert client.post("/webhooks/print-complete", headers=headers, json=payload).json()["status"] == "processed"
    assert client.post("/webhooks/print-complete", headers=headers, json=payload).json()["status"] == "ignored"
