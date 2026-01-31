import numpy as np

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

class AdvancedExplainabilityEngine:
    def __init__(
        self, model, training_data: np.ndarray, feature_names: List[str] = None
    ):
        # ... (other methods remain the same)

    def explain_with_lime(self, anomalous_sample: np.ndarray) -> Dict[str, Any]:
        if not self.lime_explainer:
            return {"error": "LIME explainer not available"}
        
        # Sanitize and mask the data
        sanitized_sample = self._sanitize_and_mask_data(anomalous_sample)
        lime_sample = sanitized_sample.flatten()
        explanation = self.lime_explainer.explain_instance(
            lime_sample, self._predict_for_lime, num_features=10
        )
        
        # Return masked result
        return {
            "method": "LIME",
            "predicted_value": float(explanation.predicted_value),
            "feature_contributions": [
                {"feature": str(f), "weight": w} for f, w in explanation.as_list()
            ],
        }

    def _sanitize_and_mask_data(self, sample: np.ndarray) -> np.ndarray:
        # Example of masking the data
        masked_sample = sample.copy()
        masked_sample[masked_sample < 0] *= -1  # Example: invert negative values to mask
        return masked_sample

    def _predict_for_lime(self, X: np.ndarray) -> np.ndarray:
        X_3d = X.reshape(
            X.shape[0], self.training_data.shape[1], self.training_data.shape[2]
        )
        X_tensor = torch.FloatTensor(X_3d)
        _, anomaly_scores, _ = self.model(X_tensor)
        scores = anomaly_scores.detach().numpy()
        return np.hstack((1 - scores, scores))
import numpy as np

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

class AdvancedExplainabilityEngine:
    def __init__(
        self, model, training_data: np.ndarray, feature_names: List[str] = None
    ):
        # ... (other methods remain the same)

    def _predict_for_lime(self, X: np.ndarray) -> np.ndarray:
        if not isinstance(X, np.ndarray):
            raise ValueError("Input data must be a numpy array")
        
        if X.shape[1] != self.training_data.shape[1]:
            raise ValueError("Input data shape does not match the training data shape")
        
        if X.shape[0] != 1:
            raise ValueError("Input data should have exactly one sample")
        
        X_3d = X.reshape(
            X.shape[0], self.training_data.shape[1], self.training_data.shape[2]
        )
        X_tensor = torch.FloatTensor(X_3d)
        _, anomaly_scores, _ = self.model(X_tensor)
        scores = anomaly_scores.detach().numpy()
        return np.hstack((1 - scores, scores))
import numpy as np

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

class AdvancedExplainabilityEngine:
    def __init__(
        self, model, training_data: np.ndarray, feature_names: List[str] = None
    ):
        # ... (other methods remain the same)

    def explain_with_shap(self, anomalous_sample: np.ndarray) -> Dict[str, Any]:
        if not self.shap_explainer:
            return {"error": "SHAP explainer not available"}
        
        sample_tensor = torch.from_numpy(anomalous_sample.reshape(1, -1, 1)).float()
        shap_values = self.shap_explainer.shap_values(sample_tensor)
        abs_sum = np.sum(np.abs(shap_values))
        normalized_shap_values = shap_values / (abs_sum + 1e-9) * 100
        
        feature_importance = []
        for i, shap_val in enumerate(normalized_shap_values):
            if shap_val > 0.01:  # Example: Exclude very small contributions
                feature_importance.append(
                    {
                        "feature_index": i,
                        "shap_value": float(shap_val),
                        "impact_percentage": float(shap_val) / (abs_sum + 1e-9) * 100,
                    }
                )
        feature_importance.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return {
            "method": "SHAP",
            "shap_values": normalized_shap_values.tolist(),
            "base_value": float(self.shap_explainer.expected_value),
            "feature_importance": feature_importance[:10],
        }