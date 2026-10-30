"""Thin Apify REST client: start an actor run, wait for it, return dataset items."""
import time

import requests

import config

API_BASE = "https://api.apify.com/v2"


def run_actor(actor_id: str, run_input: dict, wait_secs: int = 300, poll: int = 5) -> list:
    """Start an actor run, poll until it finishes, and return its dataset items.

    Raises RuntimeError if the run fails or times out.
    """
    token = config.APIFY_TOKEN
    if not token:
        raise RuntimeError("APIFY_TOKEN is missing (check .env)")

    start = requests.post(
        f"{API_BASE}/acts/{actor_id}/runs",
        params={"token": token},
        json=run_input,
        timeout=30,
    )
    start.raise_for_status()
    run = start.json()["data"]
    run_id = run["id"]
    dataset_id = run["defaultDatasetId"]

    deadline = time.time() + wait_secs
    while time.time() < deadline:
        r = requests.get(f"{API_BASE}/actor-runs/{run_id}", params={"token": token}, timeout=30)
        r.raise_for_status()
        status = r.json()["data"]["status"]
        if status in ("SUCCEEDED",):
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify actor {actor_id} run {run_id} ended with status {status}")
        time.sleep(poll)
    else:
        raise RuntimeError(f"Apify actor {actor_id} run {run_id} did not finish within {wait_secs}s")

    items, offset = [], 0
    while True:
        r = requests.get(
            f"{API_BASE}/datasets/{dataset_id}/items",
            params={"token": token, "offset": offset, "limit": 1000, "clean": "true"},
            timeout=60,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        items.extend(batch)
        offset += len(batch)
        if len(batch) < 1000:
            break
    return items
