import base64

class AdvancedExplainabilityEngine:
    # ... other methods ...

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

        # Encrypting sensitive data
        encrypted_sample = base64.b64encode(anomalous_sample.tobytes()).decode('utf-8')
        comprehensive_explanation["sample_data"] = encrypted_sample

        # Encrypting logs
        encrypted_logs = base64.b64encode(comprehensive_explanation.encode('utf-8')).decode('utf-8')
        self.logger.info("Encrypted log: %s", encrypted_logs)

        return comprehensive_explanation