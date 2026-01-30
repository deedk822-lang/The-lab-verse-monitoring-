import logging
import os
from datetime import datetime

import numpy as np
from fastapi import FastAPI, HTTPException
from src.anomaly_detection.advanced_models import (
    LSTMAnomalyDetector,
    MultiCloudAnomalyDetector,
    TransformerAnomalyDetector,
)
from src.anomaly_detection.enhanced_alerting import (
    AlertChannel,
    AlertSeverity,
    EnhancedAlert,
    EnhancedAlertingSystem,
)

from src.anomaly_detection.explainability import (
    AdvancedExplainabilityEngine,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Application Setup ---
app = FastAPI(
    title="Next-Gen Anomaly Detection API",
    description="Serving advanced ML models for anomaly detection with explainability.",
    version="1.0.0",
)

# --- Global Components (Initialize on startup) ---
lstm_model = LSTMAnomalyDetector()
transformer_model = TransformerAnomalyDetector()
cloud_detector = MultiCloudAnomalyDetector(cloud_configs={"aws": {}, "azure": {}, "gcp": {}})
alerting_system = EnhancedAlertingSystem()
explainer = None


# --- Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """Actions to take on application startup."""
    global explainer
    logger.info("Anomaly Detection Service is starting up.")
    if not os.environ.get("PYTEST_RUNNING"):
        background_data = np.random.rand(10, 10, 1)
        explainer = AdvancedExplainabilityEngine(model=lstm_model, training_data=background_data)
        logger.info("Explainability engine initialized.")
    else:
        logger.warning("Explainability engine not initialized in test environment.")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions to take on application shutdown."""
    logger.info("Anomaly Detection Service is shutting down.")


# --- API Endpoints ---
@app.get("/health", summary="Health Check", tags=["Infrastructure"])
async def health_check():
    """Health check endpoint to ensure the service is running."""
    return {"status": "ok"}


@app.post(
    "/detect/timeseries",
    summary="Detect anomalies in time series data",
    tags=["Detection"],
)
async def detect_timeseries_anomalies(data: dict):
    """Detect anomalies in a given time series using LSTM or Transformer models."""
    try:
        sequences = np.array(data["sequences"])
        model_type = data.get("model", "lstm")
        model = lstm_model if model_type == "lstm" else transformer_model
        anomalies = model.detect_anomalies(sequences)
        return {"anomalies": anomalies}
    except Exception as e:
        logger.error(f"Error in timeseries detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/detect/multi-cloud",
    summary="Detect anomalies in multi-cloud environments",
    tags=["Detection"],
)
async def detect_multi_cloud_anomalies(data: dict):
    """Detect cost, performance, and security anomalies across multiple cloud providers."""
    try:
        time_window = data.get("time_window_hours", 24)
        anomalies = await cloud_detector.detect_multi_cloud_anomalies(time_window)
        cross_cloud_patterns = cloud_detector.detect_cross_cloud_patterns(anomalies)
        return {
            "multi_cloud_anomalies": anomalies,
            "cross_cloud_patterns": cross_cloud_patterns,
        }
    except Exception as e:
        logger.error(f"Error in multi-cloud detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain", summary="Explain a detected anomaly", tags=["Explainability"])
async def explain_anomaly(data: dict):
    """Provide a detailed explanation for an anomalous data point."""
    if explainer is None:
        raise HTTPException(status_code=503, detail="Explainability engine is not available.")
    try:
        sample = np.array(data["sample"])
        context = data.get("context")
        explanation = explainer.explain_anomaly_comprehensive(sample, context)
        return explanation
    except Exception as e:
        logger.error(f"Error in explanation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alert", summary="Trigger an enhanced alert for an anomaly", tags=["Alerting"])
async def trigger_alert(alert_data: dict):
    """Trigger a multi-channel alert for a critical anomaly."""
    try:
        alert = EnhancedAlert(
            alert_id=alert_data.get("alert_id", "test-alert-123"),
            title=alert_data["title"],
            description=alert_data["description"],
            severity=AlertSeverity(alert_data.get("severity", "high")),
            channels=[AlertChannel(c) for c in alert_data.get("channels", ["slack", "email"])],
            anomaly_data=alert_data["anomaly_data"],
            created_at=datetime.now(),
            expires_at=None,
            actions_required=alert_data.get("actions_required", ["Investigate immediately."]),
            auto_remediation_enabled=alert_data.get("auto_remediation_enabled", False),
            escalation_path=[],
            mobile_optimized=True,
        )
        result = await alerting_system.send_enhanced_alert(alert)
        return result
    except Exception as e:
        logger.error(f"Error in alerting endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
