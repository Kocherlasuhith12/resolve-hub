import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricsCollector:
    request_counts: dict[tuple[str, str, int], int] = field(
        default_factory=lambda: defaultdict(int)
    )
    request_durations: dict[tuple[str, str], list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    active_websockets: int = 0
    audit_events: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_request(self, method: str, path: str, status_code: int, duration: float) -> None:
        self.request_counts[(method, path, status_code)] += 1
        durations = self.request_durations[(method, path)]
        if len(durations) > 1000:
            durations.pop(0)
        durations.append(duration)

    def record_websocket_connect(self) -> None:
        self.active_websockets += 1

    def record_websocket_disconnect(self) -> None:
        if self.active_websockets > 0:
            self.active_websockets -= 1

    def record_audit_event(self, action: str) -> None:
        self.audit_events[action] += 1

    def generate_prometheus_text(self) -> str:
        lines: list[str] = [
            "# HELP http_requests_total Total number of HTTP requests processed.",
            "# TYPE http_requests_total counter",
        ]
        for (method, path, status), count in self.request_counts.items():
            lines.append(
                f'http_requests_total{{method="{method}",endpoint="{path}",status="{status}"}} '
                f"{count}"
            )

        lines.extend(
            [
                "# HELP http_request_duration_seconds_sum Sum of request durations in seconds.",
                "# TYPE http_request_duration_seconds_sum counter",
            ]
        )
        for (method, path), durations in self.request_durations.items():
            s = sum(durations)
            lines.append(
                f'http_request_duration_seconds_sum{{method="{method}",endpoint="{path}"}} {s:.6f}'
            )

        lines.extend(
            [
                "# HELP active_websocket_connections Number of active WebSocket connections.",
                "# TYPE active_websocket_connections gauge",
                f"active_websocket_connections {self.active_websockets}",
                "# HELP audit_events_total Total number of security audit events.",
                "# TYPE audit_events_total counter",
            ]
        )
        for action, count in self.audit_events.items():
            lines.append(f'audit_events_total{{action="{action}"}} {count}')

        lines.append(
            "# HELP process_uptime_seconds Process uptime timestamp.\n"
            f"process_uptime_seconds {time.time()}"
        )
        return "\n".join(lines) + "\n"


metrics_collector = MetricsCollector()
