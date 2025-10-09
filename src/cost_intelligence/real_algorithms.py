import numpy as np
from scipy.stats import zscore

def detect_anomalies_zscore(data, threshold=3.0):
    """
    Detects anomalies in a time series using the Z-score method.

    Args:
        data (list or np.array): The time series data.
        threshold (float): The Z-score threshold for anomaly detection.

    Returns:
        list: A list of indices where anomalies were detected.
    """
    if not isinstance(data, np.ndarray):
        data = np.array(data)

    z_scores = np.abs(zscore(data))
    return np.where(z_scores > threshold)[0].tolist()