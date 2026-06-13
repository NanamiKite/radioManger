from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.log_service import LogService
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/overview")
async def get_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取统计概览"""
    stats = LogService.get_stats(db, current_user.id)
    return {"data": stats}
