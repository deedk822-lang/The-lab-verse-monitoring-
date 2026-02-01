import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import lime.lime_tabular

# Wrapper model for SHAP DeepExplainer
class AnomalyScoreModel(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        anomaly_score, _, _ = self.model(x)
        return anomaly_score

class AdvancedExplainabilityEngine:
    """Comprehensive explainability for ML anomaly detection"""

    def __init__(
        self, model, training_data: np.ndarray, feature_names: List[str] = None
    ):
        self.model = model
        self.training_data = torch.tensor(training_data).float()
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(self.training_data.shape[1])]
        self.logger = logging.getLogger("explainability_engine")

        self._setup_shap_explainer()
        self._setup_lime_explainer()
        self._setup_custom_explainer()

    def _setup_shap_explainer(self):
        """Setup SHAP explainer using the more efficient DeepExplainer."""
        try:
            shap_model = AnomalyScoreModel(self.model)
            background_tensor = torch.from_numpy(self.training_data).float()
            self.shap_explainer = shap.DeepExplainer(shap_model, background_tensor)
            self.logger.info("SHAP DeepExplainer initialized successfully")
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
            "timestamp": datetime.now().isoformat(),
            "sample_data": anomalous_sample.tolist(),
            "explanations": {},
        }

        if self.shap_explainer:
            try:
                shap_values = self.shap_explainer.shap_values(anomalous_sample)
                comprehensive_explanation["explanations"]["shap"] = {
                    f"{i}": shap_value.item() for i, shap_value in enumerate(shap_values)
                }
            except Exception as e:
                self.logger.error(f"Failed to compute SHAP values: {e}")

        if self.lime_explainer:
            try:
                explanations = self.lime_explainer.explain_instance(
                    anomalous_sample,
                    class_names=["normal", "anomaly"],
                    top_labels=3,  # Adjust the number of top labels as needed
                )
                comprehensive_explanation["explanations"]["lime"] = {
                    f"{i}": explanation.as_list() for i in range(len(explanations))
                }
            except Exception as e:
                self.logger.error(f"Failed to compute LIME explanations: {e}")

        if self.custom_explainer:
            try:
                custom_explanation = self.custom_explainer.analyze(anomalous_sample)
                comprehensive_explanation["explanations"]["custom"] = {
                    f"{i}": explanation for i, explanation in enumerate(custom_explanation)
                }
            except Exception as e:
                self.logger.error(f"Failed to compute custom explanations: {e}")

        return comprehensive_explanation