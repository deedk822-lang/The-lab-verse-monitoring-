def explain_anomaly_comprehensive(
    anomalous_sample: np.ndarray,
    context_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        encrypted_context_data = encrypt(context_data)
        comprehensive_explanation["explanations"]["rules"] = (
            self.explain_with_rules(anomalous_sample, encrypted_context_data)
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

def encrypt(context_data: dict[str, Any]) -> str:
    # Use a secure encryption algorithm to encrypt the context data
    # For example, use AES-256
    cipher_suite = Fernet.generate_key()
    encrypted_context_data = b" ".join(f"{k}:{v}" for k, v in context_data.items()).encode()
    return base64.b64encode(cipher_suite + encrypted_context_data).decode()

def decrypt(encrypted_context_data: str) -> dict[str, Any]:
    # Use a secure decryption algorithm to decrypt the context data
    # For example, use AES-256
    cipher_suite = base64.b32decode(encrypted_context_data[:16])
    encrypted_context_data = encrypted_context_data[16:]
    try:
        decrypted_context_data = Fernet(cipher_suite).decrypt(encrypted_context_data)
        return dict(item.split(":") for item in decrypted_context_data.decode().split(" "))
    except InvalidTokenError:
        return {}