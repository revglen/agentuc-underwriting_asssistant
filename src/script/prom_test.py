"""
Standalone manual check for src/observability/metrics.py.

Not a pytest test (no assertions, starts a real HTTP server) — run directly:
    python3 tests/metrics_manual_check.py

Exercises the track() decorator with one success and one failure, then scrapes
its own /metrics endpoint and prints the relevant lines so you can eyeball that
all 5 metrics update correctly before wiring this into a real MCP server.
"""
import urllib.request
import random
import time

from observability.metrics import MetricsRegistry

metrics = MetricsRegistry()

PORT = 9000
print("About to test prometheus....")

PORT = 8001
SERVER_NAME = "credit_bureau" 
 
@metrics.track(server=SERVER_NAME, tool="get_credit_score")
def get_credit_score():
    time.sleep(random.uniform(0.05, 0.3))
    if random.random() < 0.1:
        raise TimeoutError("simulated bureau timeout")
    return "ok"
 
@metrics.track(server="manual_check", tool="ok_call")
def succeeds():
    return "fine"

@metrics.track(server="manual_check", tool="fail_call")
def fails():
    raise ValueError("forced failure for manual check")

def main():
    metrics.start_server(PORT)

    print(f"serving /metrics on :{PORT}, Ctrl+C to stop")
    #for i in range(1000):
    while True:
        try:
            get_credit_score()
        except TimeoutError:
            pass
        time.sleep(random.uniform(0.3, 1.0))

    print("Completed...")    

    # body = urllib.request.urlopen(f"http://localhost:{PORT}/metrics").read().decode()

    # print(f"scraped http://localhost:{PORT}/metrics\n")
    # for line in body.splitlines():
    #     if line.startswith("tool_") or line.startswith("last_success"):
    #         if 'server="manual_check"' in line:
    #             print(line)


if __name__ == "__main__":
    main()