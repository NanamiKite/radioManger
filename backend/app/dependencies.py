# from fastapi import Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from app.database.session import get_db
# from app.utils.security import SecurityUtils
# from fastapi.security import HTTPAuthorizationCredentials


# security = HTTPBearer()

# async def get_current_user(
#     credentials: HTTPAuthCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ):
#     """获取当前认证用户"""
#     from app.models.user import User
    
#     try:
#         payload = SecurityUtils.decode_token(credentials.credentials)
#         user_id = payload.get("sub")
        
#         if user_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token"
#             )
        
#         user = db.query(User).filter(User.id == int(user_id)).first()
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User not found"
#             )
        
#         return user
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=str(e)
#         )

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.utils.security import SecurityUtils

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前认证用户"""

    from app.models.user import User

    try:
        # Bearer Token字符串
        token = credentials.credentials

        payload = SecurityUtils.decode_token(token)

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        user = (
            db.query(User)
            .filter(User.id == int(user_id))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
