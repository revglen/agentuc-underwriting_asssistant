"""
Streamlit UI for the underwriting assistant. Submits an evaluation async,
polls for the result. Plain widgets only, no custom CSS.
"""
from __future__ import annotations

import os
import time

import streamlit as st

from api_client import ApiError, poll_job, submit_evaluation

API_BASE_URL = os.getenv("API_BASE_URL", "https://localhost:8443")

st.set_page_config(page_title="Underwriting Assistant", page_icon="\U0001F4B0")
st.title("Underwriting Assistant")
st.caption(f"API: {API_BASE_URL}")

if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "job_status" not in st.session_state:
    st.session_state.job_status = None

with st.form("evaluate_form"):
    applicant_id = st.text_input("Applicant ID", value="applicant-1")
    requested_amount = st.number_input("Requested amount", min_value=1.0, value=20000.0, step=1000.0)
    months = st.number_input("Months of bank statements", min_value=1, max_value=24, value=6, step=1)
    submitted = st.form_submit_button("Submit for evaluation")

if submitted:
    try:
        result = submit_evaluation(API_BASE_URL, applicant_id, requested_amount, int(months))
        st.session_state.job_id = result["job_id"]
        st.session_state.job_status = result
        st.success(f"Submitted. job_id: {result['job_id']}")
    except ApiError as exc:
        st.error(str(exc))

if st.session_state.job_id:
    st.divider()
    st.subheader("Job status")
    st.text(f"job_id: {st.session_state.job_id}")

    col1, col2 = st.columns(2)
    with col1:
        check_now = st.button("Check status now")
    with col2:
        auto_refresh = st.checkbox("Auto-refresh every 5s", value=False)

    if check_now or auto_refresh:
        try:
            st.session_state.job_status = poll_job(API_BASE_URL, st.session_state.job_id)
        except ApiError as exc:
            st.error(str(exc))

    status = st.session_state.job_status
    if status:
        state = status.get("status")
        if state in ("pending", "running"):
            st.info(f"status: {state}")
        elif state == "completed":
            st.success("status: completed")
            st.json(status["result"])
        elif state == "failed":
            st.error(f"status: failed - {status.get('error')}")

        if auto_refresh and state in ("pending", "running"):
            time.sleep(5)
            st.rerun()

if st.button("Start a new evaluation"):
    st.session_state.job_id = None
    st.session_state.job_status = None
    st.rerun()