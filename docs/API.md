# API Migration: Flask → FastAPI

## Breaking Changes

### Server Framework
- **Before:** Flask with `@app.route` decorators
- **After:** FastAPI with type-safe endpoints

### Import Paths (src-layout)
```python
# Before
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

# After
from src.rainmaker_orchestrator.core.orchestrator import RainmakerOrchestrator
```

### Health Check Response Format
```json
{
  "status": "healthy",
  "timestamp": "2026-01-13T12:00:00Z",
  "dependencies": {
    "orchestrator": {"status": "healthy"},
    "kimi_client": {"status": "healthy"}
  }
}
```

### Request Validation
All endpoints now use Pydantic models with automatic validation:
- 422 status for validation errors (not 400)
- Detailed error messages in response

### Rate Limiting
- `/health`: 100/minute
- `/execute`: 10/minute
- `/webhook/alert`: 30/minute

## Migration Checklist

- [ ] Update client code to handle 422 validation errors
- [ ] Add retry logic for rate limit (429) responses
- [ ] Update health check polling (new response format)
- [ ] Test OpenAPI schema at `/docs`
