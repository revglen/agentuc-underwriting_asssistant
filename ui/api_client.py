"""
Thin wrapper around the FastAPI backend's async evaluation endpoints, kept
separate from ui/app.py so it can be tested without a Streamlit runtime.
"""
from __future__ import annotations

import requests
import urllib3

# self-signed dev cert - same tradeoff as every curl -k in this project
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ApiError(Exception):
    pass


def submit_evaluation(base_url: str, applicant_id: str, requested_amount: float, months: int) -> dict:
    """POST /applications/evaluate/async - returns {job_id, status} immediately."""
    try:
        resp = requests.post(
            f"{base_url}/applications/evaluate/async",
            json={
                "applicant_id": applicant_id,
                "requested_amount": requested_amount,
                "months_of_statements": months,
            },
            verify=False,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise ApiError(f"could not submit evaluation: {exc}") from None


def poll_job(base_url: str, job_id: str) -> dict:
    """GET /applications/evaluate/async/{job_id} - current status/result/error."""
    try:
        resp = requests.get(f"{base_url}/applications/evaluate/async/{job_id}", verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise ApiError(f"could not poll job {job_id}: {exc}") from None