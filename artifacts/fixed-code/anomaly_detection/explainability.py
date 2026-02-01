def explain_anomaly_comprehensive(
    anomalous_sample: np.ndarray,
    context_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    comprehensive_explanation = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "sample_data": anomalous_sample.tolist(),
        "explanations": {},
    }

    if not self.shap_explainer:
        return {"error": "SHAP explainer not available"}

    try:
        sample_tensor = torch.from_numpy(anomalous_sample.reshape(1, -1, 1)).float()
        shap_values = self.shap_explainer.shap_values(sample_tensor)
        shap_values_2d = shap_values.reshape(shap_values.shape[0], -1)
        feature_importance = self._calculate_shap_importance(shap_values_2d[0])
    except Exception as e:
        self.logger.error(f"SHAP explanation failed: {e}")
        comprehensive_explanation["explanations"]["shap"] = None

    if not self.lime_explainer:
        return {"error": "LIME explainer not available"}

    try:
        lime_sample = anomalous_sample.flatten()
        explanation = self.lime_explainer.explain_instance(
            lime_sample, self._predict_for_lime, num_features=10
        )
    except Exception as e:
        self.logger.error(f"LIME explanation failed: {e}")
        comprehensive_explanation["explanations"]["lime"] = None

    try:
        comprehensive_explanation["explanations"]["rules"] = (
            self.explain_with_rules(anomalous_sample, context_data)
        )
    except Exception as e:
        self.logger.error(f"Custom explanation failed: {e}")
        comprehensive_explanation["explanations"]["rules"] = None

    return comprehensive_explanation