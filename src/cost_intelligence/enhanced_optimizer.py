from .real_algorithms import detect_anomalies_zscore

class EnhancedCostOptimizer:
    """
    An enhanced cost optimizer that uses ML for anomaly detection.
    """
    def __init__(self, model_cache_path="."):
        self.model_cache_path = model_cache_path

    async def detect_anomalies(self, data, strategy="zscore", threshold=3.0):
        """
        Detects anomalies in the given data using the specified strategy.
        """
        if strategy == "zscore":
            anomalies = detect_anomalies_zscore(data, threshold)
            return anomalies
        else:
            raise ValueError(f"Unknown anomaly detection strategy: {strategy}")

    def label_anomaly(self, anomaly_type):
        """
        Labels an anomaly with a given type.
        """
        return {
            "type": anomaly_type,
            "description": f"Detected a {anomaly_type} anomaly."
        }