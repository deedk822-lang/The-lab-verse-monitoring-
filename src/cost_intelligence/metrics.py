from prometheus_client import Counter, Gauge

# Counter for the total number of optimization runs
OPTIMIZATION_RUNS_TOTAL = Counter(
    "labverse_cost_optimization_runs_total",
    "Total number of cost optimization runs.",
    ["strategy", "status"]
)

# Counter for the total number of anomalies detected
ANOMALIES_DETECTED_TOTAL = Counter(
    "labverse_cost_anomalies_detected_total",
    "Total number of cost anomalies detected.",
    ["anomaly_type"]
)

# Gauge for the last anomaly detection Z-score
LAST_ANOMALY_ZSCORE = Gauge(
    "labverse_cost_last_anomaly_zscore",
    "The Z-score of the last detected anomaly."
)