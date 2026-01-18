# src/anomaly_detection/advanced_models.py
"""
Advanced ML models: LSTM, Transformers, and Explainable AI
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import shap
import lime
import lime.lime_tabular
from transformers import TimeSeriesTransformerConfig, TimeSeriesTransformerModel
import logging


class LSTMAnomalyDetector(nn.Module):
    """LSTM-based anomaly detector for time series data"""

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size, num_heads=8, dropout=dropout
        )

        # Reconstruction layers
        self.reconstruction = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, input_size),
        )

        # Anomaly score calculation
        self.anomaly_scorer = nn.Sequential(
            nn.Linear(hidden_size, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid()
        )

    def forward(self, x):
        # LSTM encoding
        lstm_out, (hidden, cell) = self.lstm(x)

        # Attention mechanism
        attn_out, attn_weights = self.attention(lstm_out, lstm_out, lstm_out)

        # Reconstruction
        reconstructed = self.reconstruction(attn_out)

        # Anomaly score
        anomaly_score = self.anomaly_scorer(attn_out[:, -1, :])

        return reconstructed, anomaly_score, attn_weights

    def detect_anomalies(
        self, sequences: np.ndarray, threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in sequences"""

        self.eval()
        anomalies = []

        with torch.no_grad():
            sequences_tensor = torch.FloatTensor(sequences)

            reconstructed, anomaly_scores, attention_weights = self.forward(
                sequences_tensor
            )

            # Calculate reconstruction error
            reconstruction_errors = torch.mean(
                (sequences_tensor - reconstructed) ** 2, dim=(1, 2)
            ).numpy()

            # Detect anomalies
            for i, (error, score, weights) in enumerate(
                zip(reconstruction_errors, anomaly_scores, attention_weights)
            ):
                if error > threshold or score.item() > 0.5:
                    anomalies.append(
                        {
                            "sequence_index": i,
                            "reconstruction_error": float(error),
                            "anomaly_score": float(score.item()),
                            "attention_weights": weights.numpy().tolist(),
                            "severity": self._calculate_severity(error, score.item()),
                            "confidence": float(score.item()),
                        }
                    )

        return anomalies

    def _calculate_severity(
        self, reconstruction_error: float, anomaly_score: float
    ) -> str:
        """Calculate anomaly severity based on multiple factors"""

        combined_score = reconstruction_error * 0.6 + anomaly_score * 0.4

        if combined_score > 0.8:
            return "critical"
        elif combined_score > 0.6:
            return "high"
        elif combined_score > 0.4:
            return "medium"
        elif combined_score > 0.2:
            return "low"
        else:
            return "normal"


class TransformerAnomalyDetector(nn.Module):
    """Transformer-based anomaly detector for complex patterns"""

    def __init__(
        self,
        input_size: int = 1,
        d_model: int = 128,
        num_heads: int = 8,
        num_layers: int = 6,
        dropout: float = 0.1,
        max_length: int = 1000,
    ):
        super().__init__()

        self.d_model = d_model
        self.max_length = max_length

        # Input embedding
        self.input_projection = nn.Linear(input_size, d_model)
        self.positional_encoding = self._generate_positional_encoding(
            max_length, d_model
        )

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=num_heads, dropout=dropout, batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)

        # Output heads
        self.reconstruction_head = nn.Linear(d_model, input_size)
        self.anomaly_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

        # Feature importance head
        self.importance_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, input_size),
            nn.Softmax(dim=-1),
        )

    def _generate_positional_encoding(
        self, max_length: int, d_model: int
    ) -> torch.Tensor:
        """Generate sinusoidal positional encoding"""

        pe = torch.zeros(max_length, d_model)
        position = torch.arange(0, max_length, dtype=torch.float).unsqueeze(1)

        div_term = torch.exp(
            torch.arange(0, d_model, 2).float()
            * (-torch.log(torch.tensor(10000.0)) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        return pe.unsqueeze(0)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape

        # Project input
        x = self.input_projection(x)

        # Add positional encoding
        if seq_len <= self.max_length:
            x = x + self.positional_encoding[:, :seq_len, :].to(x.device)

        # Transformer encoding
        encoded = self.transformer_encoder(x)

        # Multiple outputs
        reconstructed = self.reconstruction_head(encoded)
        anomaly_score = self.anomaly_head(encoded.mean(dim=1))
        feature_importance = self.importance_head(encoded.mean(dim=1))

        return reconstructed, anomaly_score, feature_importance, encoded


class ExplainableAIAnalyzer:
    """SHAP and LIME-based explainability for anomaly detection"""

    def __init__(self, model, background_data: np.ndarray):
        self.model = model
        self.background_data = background_data
        self.shap_explainer = None
        self.lime_explainer = None
        self.setup_explainers()

    def setup_explainers(self):
        """Setup SHAP and LIME explainers"""

        # SHAP explainer
        self.shap_explainer = shap.DeepExplainer(self.model, self.background_data)

        # LIME explainer
        self.lime_explainer = lime.lime_tabular.LimeTabularExplainer(
            self.background_data,
            mode="regression",
            feature_names=[
                f"feature_{i}" for i in range(self.background_data.shape[1])
            ],
            verbose=True,
        )

    def explain_anomaly_shap(self, anomalous_sample: np.ndarray) -> Dict[str, Any]:
        """Explain anomaly using SHAP"""

        # Calculate SHAP values
        shap_values = self.shap_explainer.shap_values(anomalous_sample)

        # Create explanation
        explanation = {
            "method": "SHAP",
            "shap_values": shap_values.tolist(),
            "base_value": float(self.shap_explainer.expected_value),
            "feature_importance": self._calculate_feature_importance(shap_values),
            "summary_plot": self._create_shap_summary(shap_values, anomalous_sample),
        }

        return explanation

    def explain_anomaly_lime(self, anomalous_sample: np.ndarray) -> Dict[str, Any]:
        """Explain anomaly using LIME"""

        # Generate LIME explanation
        explanation = self.lime_explainer.explain_instance(
            anomalous_sample[0], self._predict_wrapper, num_features=10
        )

        # Convert to serializable format
        lime_explanation = {
            "method": "LIME",
            "predicted_value": float(explanation.predicted_value),
            "local_weight": float(explanation.local_weight),
            "feature_importance": [
                {"feature": str(feature), "weight": float(weight)}
                for feature, weight in explanation.as_list()
            ],
            "intercept": float(explanation.intercept[1]),
            "r_squared": float(explanation.score),
        }

        return lime_explanation

    def _predict_wrapper(self, X):
        """Wrapper for model prediction in LIME"""
        X_tensor = torch.FloatTensor(X)
        _, anomaly_scores, _, _ = self.model(X_tensor)
        return anomaly_scores.detach().numpy()

    def _calculate_feature_importance(
        self, shap_values: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Calculate feature importance from SHAP values"""

        feature_importance = []

        for i in range(shap_values.shape[1]):
            importance = {
                "feature_index": i,
                "feature_name": f"feature_{i}",
                "shap_value": float(shap_values[0, i]),
                "abs_shap_value": float(abs(shap_values[0, i])),
                "contribution_direction": (
                    "positive" if shap_values[0, i] > 0 else "negative"
                ),
            }
            feature_importance.append(importance)

        # Sort by absolute importance
        feature_importance.sort(key=lambda x: x["abs_shap_value"], reverse=True)

        return feature_importance[:10]  # Top 10 features

    def _create_shap_summary(self, shap_values: np.ndarray, sample: np.ndarray) -> str:
        """Create SHAP summary text"""

        feature_importance = self._calculate_feature_importance(shap_values)

        summary = "SHAP Analysis Summary:\n"
        summary += f"Base value: {float(self.shap_explainer.expected_value):.4f}\n"
        summary += "Top contributing features:\n"

        for i, feature in enumerate(feature_importance[:5]):
            summary += f"{i+1}. {feature['feature_name']}: {feature['shap_value']:.4f} ({feature['contribution_direction']})\n"

        return summary


class MultiCloudAnomalyDetector:
    """Anomaly detection optimized for multi-cloud environments"""

    def __init__(self, cloud_configs: Dict[str, Any]):
        self.cloud_configs = cloud_configs
        self.cloud_specific_detectors = {}
        self.setup_cloud_detectors()

    def setup_cloud_detectors(self):
        """Setup cloud-specific anomaly detectors"""

        for cloud_provider, config in self.cloud_configs.items():
            self.cloud_specific_detectors[cloud_provider] = {
                "cost_detector": CloudCostAnomalyDetector(cloud_provider, config),
                "performance_detector": CloudPerformanceAnomalyDetector(
                    cloud_provider, config
                ),
                "security_detector": CloudSecurityAnomalyDetector(
                    cloud_provider, config
                ),
            }

    async def detect_multi_cloud_anomalies(
        self, time_window_hours: int = 24
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Detect anomalies across multiple cloud providers"""

        all_anomalies = {}

        for cloud_provider, detectors in self.cloud_specific_detectors.items():
            cloud_anomalies = {
                "cost_anomalies": [],
                "performance_anomalies": [],
                "security_anomalies": [],
            }

            # Cost anomalies
            try:
                cost_anomalies = await detectors["cost_detector"].detect_anomalies(
                    time_window_hours
                )
                cloud_anomalies["cost_anomalies"] = cost_anomalies
            except Exception as e:
                logging.error(
                    f"Cost anomaly detection failed for {cloud_provider}: {e}"
                )

            # Performance anomalies
            try:
                perf_anomalies = await detectors[
                    "performance_detector"
                ].detect_anomalies(time_window_hours)
                cloud_anomalies["performance_anomalies"] = perf_anomalies
            except Exception as e:
                logging.error(
                    f"Performance anomaly detection failed for {cloud_provider}: {e}"
                )

            # Security anomalies
            try:
                security_anomalies = await detectors[
                    "security_detector"
                ].detect_anomalies(time_window_hours)
                cloud_anomalies["security_anomalies"] = security_anomalies
            except Exception as e:
                logging.error(
                    f"Security anomaly detection failed for {cloud_provider}: {e}"
                )

            all_anomalies[cloud_provider] = cloud_anomalies

        return all_anomalies

    def detect_cross_cloud_patterns(
        self, multi_cloud_anomalies: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Detect patterns that span across cloud providers"""

        cross_cloud_patterns = []

        # Look for similar anomalies across clouds
        for anomaly_type in [
            "cost_anomalies",
            "performance_anomalies",
            "security_anomalies",
        ]:
            similar_anomalies = []

            for cloud_provider, anomalies in multi_cloud_anomalies.items():
                cloud_anomalies = anomalies.get(anomaly_type, [])

                for anomaly in cloud_anomalies:
                    # Check if this anomaly is similar to others across clouds
                    if self._is_similar_across_clouds(
                        anomaly, multi_cloud_anomalies, anomaly_type
                    ):
                        similar_anomalies.append(
                            {"cloud_provider": cloud_provider, "anomaly": anomaly}
                        )

            if len(similar_anomalies) >= 2:  # Found in at least 2 clouds
                cross_cloud_patterns.append(
                    {
                        "type": "cross_cloud_similarity",
                        "anomaly_type": anomaly_type,
                        "affected_clouds": [
                            sa["cloud_provider"] for sa in similar_anomalies
                        ],
                        "pattern_confidence": len(similar_anomalies)
                        / len(self.cloud_configs),
                        "severity": max(
                            [sa["anomaly"]["severity"] for sa in similar_anomalies]
                        ),
                        "explanation": f"Similar {anomaly_type} detected across multiple cloud providers",
                    }
                )

        return cross_cloud_patterns

    def _is_similar_across_clouds(
        self,
        anomaly: Dict[str, Any],
        all_anomalies: Dict[str, List[Dict[str, Any]]],
        anomaly_type: str,
    ) -> bool:
        """Check if an anomaly is similar across different cloud providers"""

        # Simple similarity check based on metric name and severity
        # In a real implementation, this would be more sophisticated

        anomaly_metric = anomaly.get("metric_name", "")
        anomaly_severity = anomaly.get("severity", "low")

        similar_count = 0

        for cloud_provider, cloud_anomalies in all_anomalies.items():
            cloud_anomaly_list = cloud_anomalies.get(anomaly_type, [])

            for other_anomaly in cloud_anomaly_list:
                if (
                    other_anomaly.get("metric_name", "") == anomaly_metric
                    and other_anomaly.get("severity", "low") == anomaly_severity
                ):
                    similar_count += 1
                    break

        return similar_count >= 2  # Found in at least 2 clouds


class CloudCostAnomalyDetector:
    """Cloud-specific cost anomaly detection"""

    def __init__(self, cloud_provider: str, config: Dict[str, Any]):
        self.cloud_provider = cloud_provider
        self.config = config

    async def detect_anomalies(self, time_window_hours: int) -> List[Dict[str, Any]]:
        """Detect cost anomalies with more realistic mock data."""
        anomalies = []
        if np.random.rand() > 0.7:  # 30% chance of cost anomaly
            service = np.random.choice(["EC2", "S3", "RDS", "Lambda"])
            cost = 1000 * np.random.rand() + 500
            anomalies.append(
                {
                    "metric_name": f"{self.cloud_provider}_{service}_cost_spike",
                    "timestamp": datetime.now()
                    - timedelta(hours=np.random.randint(1, time_window_hours)),
                    "value": cost,
                    "expected_range": (cost * 0.5, cost * 0.7),
                    "severity": "high",
                    "confidence": 0.88,
                    "explanation": f"Unusually high cost of ${cost:.2f} detected for {service} in {self.cloud_provider}.",
                    "recommended_action": f"Review cost allocation tags for {service} and check for unused resources.",
                }
            )
        return anomalies


class CloudPerformanceAnomalyDetector:
    """Cloud-specific performance anomaly detection"""

    def __init__(self, cloud_provider: str, config: Dict[str, Any]):
        self.cloud_provider = cloud_provider
        self.config = config

    async def detect_anomalies(self, time_window_hours: int) -> List[Dict[str, Any]]:
        """Detect performance anomalies with more realistic mock data."""
        anomalies = []
        if np.random.rand() > 0.6:  # 40% chance of performance anomaly
            metric = np.random.choice(["p99_latency_ms", "error_rate_percent"])
            value = (
                500 * np.random.rand() if "latency" in metric else 10 * np.random.rand()
            )
            anomalies.append(
                {
                    "metric_name": f"{self.cloud_provider}_api_gateway_{metric}",
                    "timestamp": datetime.now()
                    - timedelta(minutes=np.random.randint(1, time_window_hours * 60)),
                    "value": value,
                    "expected_range": (value * 0.3, value * 0.5),
                    "severity": "high",
                    "confidence": 0.91,
                    "explanation": f"High {metric} of {value:.2f} detected on API Gateway in {self.cloud_provider}.",
                    "recommended_action": "Check for slow downstream services or increase in traffic.",
                }
            )
        return anomalies


class CloudSecurityAnomalyDetector:
    """Cloud-specific security anomaly detection"""

    def __init__(self, cloud_provider: str, config: Dict[str, Any]):
        self.cloud_provider = cloud_provider
        self.config = config

    async def detect_anomalies(self, time_window_hours: int) -> List[Dict[str, Any]]:
        """Detect security anomalies with more realistic mock data."""
        anomalies = []
        if np.random.rand() > 0.8:  # 20% chance of security anomaly
            source_ip = f"18.{np.random.randint(10, 200)}.{np.random.randint(10, 200)}.{np.random.randint(10, 200)}"
            anomalies.append(
                {
                    "metric_name": f"{self.cloud_provider}_unusual_login_location",
                    "timestamp": datetime.now()
                    - timedelta(seconds=np.random.randint(1, time_window_hours * 3600)),
                    "value": 1.0,  # Represents a single event
                    "expected_range": (0.0, 0.1),
                    "severity": "critical",
                    "confidence": 0.98,
                    "explanation": f"Anomalous login detected from {source_ip} to a critical system in {self.cloud_provider}.",
                    "recommended_action": f"Immediately investigate activity from {source_ip} and rotate credentials for the affected user.",
                }
            )
        return anomalies
