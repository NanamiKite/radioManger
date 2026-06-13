from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import UserResponse
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_user_info(current_user = Depends(get_current_user)):
    """获取用户信息"""
    return current_user
