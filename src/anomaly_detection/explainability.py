# src/anomaly_detection/explainability.py
"""
Advanced explainability using SHAP, LIME, and custom explanations
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn


# Wrapper model for SHAP DeepExplainer
class AnomalyScoreModel(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        _, anomaly_score, _ = self.model(x)
        return anomaly_score


class AdvancedExplainabilityEngine:
    """Comprehensive explainability for ML anomaly detection"""

    def __init__(
        self, model, training_data: np.ndarray, feature_names: List[str] = None
    ):
        self.model = model
        self.training_data = training_data
        self.feature_names = feature_names or [
            f"feature_{i}" for i in range(training_data.shape[1])
        ]
        self.logger = logging.getLogger("explainability_engine")

        self._setup_shap_explainer()
        self._setup_lime_explainer()
        self._setup_custom_explainer()

    def _setup_shap_explainer(self):
        """Setup SHAP explainer using the more efficient DeepExplainer."""
        try:
            if hasattr(self.model, "forward"):
                shap_model = AnomalyScoreModel(self.model)
                background_tensor = torch.from_numpy(self.training_data).float()
                self.shap_explainer = shap.DeepExplainer(shap_model, background_tensor)
                self.logger.info("SHAP DeepExplainer initialized successfully")
            else:
                self.shap_explainer = shap.Explainer(self.model, self.training_data)
                self.logger.info("SHAP Explainer initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SHAP explainer: {e}")
            self.shap_explainer = None

    def _setup_lime_explainer(self):
        """Setup LIME explainer."""
        try:
            lime_training_data = self.training_data.reshape(
                (self.training_data.shape[0], -1)
            )
            self.lime_explainer = lime.lime_tabular.LimeTabularExplainer(
                lime_training_data,
                mode="regression",
                feature_names=[f"ts_{i}" for i in range(lime_training_data.shape[1])],
                class_names=["normal", "anomaly"],
                verbose=False,
            )
            self.logger.info("LIME explainer initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LIME explainer: {e}")
            self.lime_explainer = None

    def _setup_custom_explainer(self):
        """Setup custom rule-based explainer"""
        self.custom_explainer = RuleBasedExplainer(self.feature_names)

    def explain_anomaly_comprehensive(
        self,
        anomalous_sample: np.ndarray,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        comprehensive_explanation = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "sample_data": anomalous_sample.tolist(),
            "explanations": {},
        }
        if self.shap_explainer:
            try:
                comprehensive_explanation["explanations"]["shap"] = (
                    self.explain_with_shap(anomalous_sample)
                )
            except Exception as e:
                self.logger.error(f"SHAP explanation failed: {e}")
        if self.lime_explainer:
            try:
                comprehensive_explanation["explanations"]["lime"] = (
                    self.explain_with_lime(anomalous_sample)
                )
            except Exception as e:
                self.logger.error(f"LIME explanation failed: {e}")
        try:
            comprehensive_explanation["explanations"]["rules"] = (
                self.explain_with_rules(anomalous_sample, context_data)
            )
        except Exception as e:
            self.logger.error(f"Custom explanation failed: {e}")
        comprehensive_explanation["consensus"] = self.generate_consensus_explanation(
            comprehensive_explanation["explanations"]
        )
        comprehensive_explanation["visualizations"] = self.generate_visualizations(
            anomalous_sample, comprehensive_explanation
        )
        return comprehensive_explanation

    def explain_with_shap(self, anomalous_sample: np.ndarray) -> Dict[str, Any]:
        if not self.shap_explainer:
            return {"error": "SHAP explainer not available"}
        sample_tensor = torch.from_numpy(anomalous_sample.reshape(1, -1, 1)).float()
        shap_values = self.shap_explainer.shap_values(sample_tensor)
        shap_values_2d = shap_values.reshape(shap_values.shape[0], -1)
        feature_importance = self._calculate_shap_importance(shap_values_2d[0])
        return {
            "method": "SHAP",
            "shap_values": shap_values_2d[0].tolist(),
            "base_value": float(self.shap_explainer.expected_value),
            "feature_importance": feature_importance,
        }

    def explain_with_lime(self, anomalous_sample: np.ndarray) -> Dict[str, Any]:
        if not self.lime_explainer:
            return {"error": "LIME explainer not available"}
        lime_sample = anomalous_sample.flatten()
        explanation = self.lime_explainer.explain_instance(
            lime_sample, self._predict_for_lime, num_features=10
        )
        return {
            "method": "LIME",
            "predicted_value": float(explanation.predicted_value),
            "feature_contributions": [
                {"feature": str(f), "weight": w} for f, w in explanation.as_list()
            ],
        }

    def _predict_for_lime(self, X: np.ndarray) -> np.ndarray:
        X_3d = X.reshape(
            X.shape[0], self.training_data.shape[1], self.training_data.shape[2]
        )
        X_tensor = torch.FloatTensor(X_3d)
        _, anomaly_scores, _ = self.model(X_tensor)
        scores = anomaly_scores.detach().numpy()
        return np.hstack((1 - scores, scores))

    def explain_with_rules(
        self,
        anomalous_sample: np.ndarray,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.custom_explainer.explain(anomalous_sample, context_data)

    def generate_consensus_explanation(
        self, explanations: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "agreement_score": 0.7,
            "consensus_features": [],
            "explanation_summary": "Consensus summary.",
        }

    def generate_visualizations(
        self, anomalous_sample: np.ndarray, explanation: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {}

    def _calculate_shap_importance(
        self, shap_values: np.ndarray
    ) -> List[Dict[str, Any]]:
        feature_importance = []
        abs_sum = np.sum(np.abs(shap_values))
        for i, shap_val in enumerate(shap_values):
            feature_importance.append(
                {
                    "feature_index": i,
                    "shap_value": float(shap_val),
                    "impact_percentage": float(abs(shap_val) / (abs_sum + 1e-9) * 100),
                }
            )
        feature_importance.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return feature_importance[:10]


class RuleBasedExplainer:
    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names

    def explain(
        self,
        anomalous_sample: np.ndarray,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {"method": "rule_based", "explanations": []}


@dataclass
class ExplainedAnomalyResult:
    metric_name: str
    timestamp: datetime
    value: float
    expected_range: Tuple[float, float]
    severity: str
    confidence: float
    model_used: str
    explanations: Dict[str, Any]
    consensus_explanation: Dict[str, Any]
    visualizations: Dict[str, Any]
    root_cause_analysis: Dict[str, Any]
    business_impact: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]
    automated_actions_possible: List[str]
    human_intervention_required: bool
    explanation_confidence: float
    explanation_completeness: float
    cross_model_agreement: float
