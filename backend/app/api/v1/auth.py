from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.session import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate
from app.services.user_service import UserService
from app.utils.security import SecurityUtils
from app.config import settings
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = UserService.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username already exists"
        )
    
    # 检查邮箱是否已存在
    existing_email = UserService.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email already registered"
        )
    
    try:
        user = UserService.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        user = UserService.authenticate_user(db, user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # 创建令牌
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = SecurityUtils.create_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = SecurityUtils.create_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            # "user": user
            "user": UserResponse.model_validate(user)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
# @router.post("/login", response_model=TokenResponse)
# async def login(user_data: UserLogin, db: Session = Depends(get_db)):
#     """用户登录"""

#     print("\n===== LOGIN DEBUG =====")
#     print("INPUT username:", user_data.username)

#     try:
#         user = UserService.authenticate_user(
#             db, user_data.username, user_data.password
#         )

#         print("AUTH RESULT:", user)
#         print("STEP 1 auth check OK")

#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid credentials"
#             )

#         # 创建 access token
#         access_token_expires = timedelta(
#             minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#         )

#         access_token = SecurityUtils.create_token(
#             data={"sub": str(user.id)},
#             expires_delta=access_token_expires
#         )

#         print("STEP 2 access token OK")

#         refresh_token = SecurityUtils.create_token(
#             data={"sub": str(user.id)},
#             expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
#         )

#         print("STEP 3 refresh token OK")

#         return {
#             "access_token": access_token,
#             "refresh_token": refresh_token,
#             "token_type": "Bearer",
#             "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "email": user.email
#             }
#         }

#     except Exception as e:
#         import traceback
#         print("\n===== LOGIN ERROR =====")
#         traceback.print_exc()
#         print("=======================\n")

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Login failed"
#         )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_user_info(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新用户信息"""
    user = UserService.update_user(db, current_user, user_data)
    return user

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    confirm_password: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """修改密码"""
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Passwords do not match"
        )
    
    try:
        UserService.change_password(db, current_user, old_password, new_password)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """登出"""
    return {"message": "Logout successful"}
