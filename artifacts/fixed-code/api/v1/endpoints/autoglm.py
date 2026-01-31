from fastapi import HTTPException
from sqlalchemy.orm import Session

def get_current_user(session: Session = Depends()) -> User:
    username = session.query(User).filter_by(username=request.form.get('username')).first()
    if not username or not username.check_password(request.form.get('password')):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    return username
import jwt

def validate_api_key(api_key: str) -> bool:
    try:
        decoded = jwt.decode(api_key, settings.SECRET_KEY)
        if decoded['iss'] != 'your_service_name':
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to validate API key: {str(e)}", exc_info=True)
        return False
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/autoglm", tags=["autoglm"])

@router.get("/health", summary="Health check for GLM and AutoGLM services")
async def autoglm_health_check():
    # ...
    return health_status