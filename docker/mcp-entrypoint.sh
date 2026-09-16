#!/usr/bin/env bash
set -e
trap 'kill 0' TERM INT

python -m mcp_servers.credit_bureau.server &
python -m mcp_servers.bank_statement_parser.server &
python -m mcp_servers.policy_rules_engine.server &

wait -n
exit $?