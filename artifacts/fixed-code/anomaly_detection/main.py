# Example of implementing input validation in the /explain endpoint
@app.post(
    "/explain", summary="Explain a detected anomaly", tags=["Explainability"]
)
async def explain_anomaly(data: dict):
    if explainer is None:
        raise HTTPException(
            status_code=503, detail="Explainability engine is not available."
        )
    
    try:
        # Validate the sample data
        if "sample" not in data or not isinstance(data["sample"], np.ndarray):
            raise ValueError("Missing or invalid 'sample' parameter.")
        
        # Validate the context data
        if "context" not in data:
            raise ValueError("Missing 'context' parameter.")
        
        # Validate the alert data
        if "alert_data" not in data or not isinstance(data["alert_data"], dict):
            raise ValueError("Missing or invalid 'alert_data' parameter.")
        
        # Perform any necessary validation on the other fields
        
        explanation = explainer.explain_anomaly_comprehensive(
            data["sample"],
            data.get("context"),
            **data["alert_data"]
        )
        return explanation
    except Exception as e:
        logger.error(f"Error in explanation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))