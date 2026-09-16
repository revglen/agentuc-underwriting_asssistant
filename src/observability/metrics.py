import asyncio
import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram, start_http_server

class MetricsRegistry:
    def __init__(self):
        self.tool_call_total = Counter(
            "tool_call_total", "Total tool calls", ["server", "tool", "status"]
        )
        self.tool_call_duration_seconds=Histogram(
            "tool_call_duration_seconds", "Total call duration in seconds", ["server", "tool"]
        )
        self.tool_call_in_progress=Gauge(
            "tool_call_in_progress", "Total calls currently running", ["server", "tool"]
        )
        self.tool_call_errors_total=Counter(
            "tool_call_errors_total", "Tool calls currently running", ["server", "tool", "error_tyoe"]
        )
        self.last_success_timestamp_seconds=Gauge(
            "last_success_timestamp_seconds", "Unix time of the last successful call",
            ["server", "tool"],
        )

        self._server_started=False

    def start_server(self, port: int):
        if self._server_started:
            return

        start_http_server(port, addr='0.0.0.0')
        self._server_started=True

    # def track(self, server: int, tool: str):
    #     def decorator(fn):
    #         @wraps(fn)
    #         def wrapper(*args, **kwargs):
    #             in_progress=self.tool_call_in_progress.labels(server=server, tool=tool)
    #             in_progress.inc()
    #             start = time.perf_counter()
    #             status = "success"
    #             try:
    #                 result = fn(*args, **kwargs)
    #                 return result
    #             except Exception as e:
    #                 status="error"
    #                 self.tool_call_errors_total.labels(
    #                     server=server, tool=tool, error_tyoe=type(e).__name__).inc()
    #                 raise
    #             finally:
    #                 duration = time.perf_counter() - start
    #                 self.tool_call_duration_seconds.labels(server=server, tool=tool).observe(duration)
    #                 self.tool_call_total.labels(server=server, tool=tool, status=status).inc()
    #                 in_progress.dec()
    #                 if status == "success":
    #                     self.last_success_timestamp_seconds.labels(server=server, tool=tool).set(time.time())
                    
    #         return wrapper
    #     return decorator

    def track(self, server: int, tool: str):
        def decorator(fn):
            if asyncio.iscoroutinefunction(fn):
                @wraps(fn)
                async def async_wrapper(*args, **kwargs):
                    in_progress = self.tool_call_in_progress.labels(server=server, tool=tool)
                    in_progress.inc()
                    start = time.perf_counter()
                    status = "success"
                    try:
                        result = await fn(*args, **kwargs)
                        return result
                    except Exception as e:
                        status = "error"
                        self.tool_call_errors_total.labels(
                            server=server, tool=tool, error_tyoe=type(e).__name__).inc()
                        raise
                    finally:
                        duration = time.perf_counter() - start
                        self.tool_call_duration_seconds.labels(server=server, tool=tool).observe(duration)
                        self.tool_call_total.labels(server=server, tool=tool, status=status).inc()
                        in_progress.dec()
                        if status == "success":
                            self.last_success_timestamp_seconds.labels(server=server, tool=tool).set(time.time())

                return async_wrapper

            @wraps(fn)
            def wrapper(*args, **kwargs):
                in_progress = self.tool_call_in_progress.labels(server=server, tool=tool)
                in_progress.inc()
                start = time.perf_counter()
                status = "success"
                try:
                    result = fn(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    self.tool_call_errors_total.labels(
                        server=server, tool=tool, error_tyoe=type(e).__name__).inc()
                    raise
                finally:
                    duration = time.perf_counter() - start
                    self.tool_call_duration_seconds.labels(server=server, tool=tool).observe(duration)
                    self.tool_call_total.labels(server=server, tool=tool, status=status).inc()
                    in_progress.dec()
                    if status == "success":
                        self.last_success_timestamp_seconds.labels(server=server, tool=tool).set(time.time())

            return wrapper
        return decorator

metrics = MetricsRegistry()