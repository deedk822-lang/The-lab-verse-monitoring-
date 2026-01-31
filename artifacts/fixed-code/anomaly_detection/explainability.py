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
    
    # Validate input
    if not isinstance(anomalous_sample, np.ndarray):
        raise ValueError("Anomalous sample must be a NumPy array")
    if not context_data:
        self.logger.warning("Context data is optional. Using default empty dictionary.")
        context_data = {}
    
    # Proceed with the rest of the method
    # ...
def _setup_shap_explainer(self):
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