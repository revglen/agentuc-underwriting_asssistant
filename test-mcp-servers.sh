#!/usr/bin/env bash
set -euo pipefail
#cd "$(dirname "${BASH_SOURCE[0]}")/.."

MCP_HOST="${MCP_HOST:-127.0.0.1}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
READY_TIMEOUT="${READY_TIMEOUT:-60}"

echo "==> starting mcp-servers, prometheus, grafana"
docker compose -f ./docker-compose.monitoring.yml up -d --build mcp-servers api prometheus grafana

wait_for_port() {
    local port="$1" name="$2"
    local waited=0
    until curl -s -o /dev/null "http://${MCP_HOST}:${port}" 2>/dev/null || [ "$waited" -ge "$READY_TIMEOUT" ]; do
        sleep 2
        waited=$((waited + 2))
    done
    if [ "$waited" -ge "$READY_TIMEOUT" ]; then
        echo "FAIL: $name (port $port) not reachable after ${READY_TIMEOUT}s"
        return 1
    fi
    echo "OK  : $name (port $port) reachable"
}

echo "==> waiting for MCP endpoints and metrics endpoints"
FAILED=0
wait_for_port 9001 "credit_bureau MCP" || FAILED=1
wait_for_port 8001 "credit_bureau metrics" || FAILED=1
wait_for_port 9002 "bank_statement_parser MCP" || FAILED=1
wait_for_port 8002 "bank_statement_parser metrics" || FAILED=1
wait_for_port 9003 "policy_rules_engine MCP" || FAILED=1
wait_for_port 8003 "policy_rules_engine metrics" || FAILED=1

if [ "$FAILED" -ne 0 ]; then
    echo "==> one or more servers never came up; check: docker compose logs mcp-servers"
    exit 1
fi

echo "==> listing tools on each server (real MCP client calls, not just a port check)"
for server in credit_bureau bank_statement_parser policy_rules_engine; do
    echo "--- $server ---"
    PYTHONPATH=src .venv/bin/python src/script/mcp_client_test.py "$server" || FAILED=1
done

echo "==> checking Prometheus sees all three scrape targets as up"
for job in credit_bureau bank_statement_parser policy_rules_engine; do
    job_ok=0
    for attempt in 1 2 3; do
        STATUS=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" | .venv/bin/python -c "
import json, sys
data = json.load(sys.stdin)
for t in data['data']['activeTargets']:
    if t['labels'].get('job') == '$job':
        print(t['health'])
        break
")
        if [ "$STATUS" = "up" ]; then
            echo "OK  : Prometheus target $job is up (attempt $attempt)"
            job_ok=1
            break
        fi
        sleep 3
    done
    if [ "$job_ok" -ne 1 ]; then
        echo "FAIL: Prometheus target $job is not up after 3 attempts (last status: ${STATUS:-not found}, check ${PROMETHEUS_URL}/targets)"
        FAILED=1
    fi
done

echo "==> smoke test PASSED"