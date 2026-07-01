from prometheus_client import Gauge, Summary, Counter

# Custom Business Posture metrics
VULNERABILITY_COUNT = Gauge(
    "secureflow_vulnerabilities_total",
    "Total active vulnerabilities tracked in security database",
    ["severity"]
)

SCAN_DURATION = Summary(
    "secureflow_scan_duration_seconds",
    "Time taken to execute complete cloud scans in background workers"
)

ML_INFERENCE_TIME = Summary(
    "secureflow_ml_inference_seconds",
    "Time spent running neural networks inference predictions",
    ["model_name"]
)

DATABASE_QUERY_LATENCY = Summary(
    "secureflow_database_query_duration_seconds",
    "SQL database read/write query latency profiles"
)

ALERT_DISPATCH_COUNT = Counter(
    "secureflow_alerts_dispatched_total",
    "Count of outbound security alerts sent",
    ["channel", "severity"]
)
