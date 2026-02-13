def explain_with_rules(
    self,
    anomalous_sample: np.ndarray,
    context_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Add input validation to ensure that the input data is safe
    if not isinstance(anomalous_sample, np.ndarray):
        return {"error": "Invalid input: Input should be a numpy array"}
    
    if not all(isinstance(x, (int, float)) for x in anomalous_sample.flatten()):
        return {"error": "Invalid input: All elements in the sample should be numbers"}

    # Add sanitization to ensure that the input data is safe
    sanitized_sample = np.array(anomalous_sample).astype('float64')

    # Use the custom rule-based explainer
    explanations = self.custom_explainer.explain(sanitized_sample, context_data)

    return explanations