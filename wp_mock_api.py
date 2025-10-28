from fastapi import FastAPI, status
from datetime import datetime
import time

app = FastAPI(
    title="WordPress Mock API",
    description="Mock API for Quantum Observer WordPress Plugin",
    version="1.0.0"
)

@app.get("/wp-json/qo/v1/scan", status_code=status.HTTP_200_OK)
async def wp_scan_endpoint():
    """
    Mock endpoint for the WordPress Quantum Observer scan.
    Required for test_wp_scan_endpoint.
    """
    start_time = time.time()
    # Simulate a fast response time (< 200ms)
    time.sleep(0.05) 
    response_time_ms = (time.time() - start_time) * 1000
    
    return {
        "status": "success",
        "grade": "A+",
        "score": 98,
        "response_time_ms": int(response_time_ms),
        "last_scanned": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    # The test suite expects this to run on port 8000 (WP_BASE_URL)
    uvicorn.run(app, host="0.0.0.0", port=8000)

