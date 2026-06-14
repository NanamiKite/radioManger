"""数据同步 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.services.sync_service import SyncService
from app.services.github_service import GitHubService

router = APIRouter()


@router.post("/github/config")
async def configure_github(
    github_url: str,
    branch: str = "main",
    auto_sync: bool = False,
    current_user=Depends(get_current_user),
):
    """配置GitHub同步（预留）"""
    return {
        "message": "GitHub config saved",
        "data": {
            "github_url": github_url,
            "branch": branch,
            "auto_sync": auto_sync,
            "status": "configured",
        },
    }


@router.post("/github/push")
async def push_to_github(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """手动推送数据到GitHub"""
    github = GitHubService()
    if not github.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub not configured. Set GITHUB_TOKEN in environment.",
        )

    result = SyncService.push_to_github(db, current_user.id)
    return result


@router.post("/github/pull")
async def pull_from_github(
    current_user=Depends(get_current_user),
):
    """从GitHub拉取数据（预留）"""
    return {
        "message": "Pull completed",
        "data": {
            "status": "not_implemented",
            "detail": "GitHub pull will be available in a future update",
        },
    }


@router.get("/history")
async def get_sync_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取同步历史"""
    skip = (page - 1) * page_size
    items, total = SyncService.get_history(db, current_user.id, skip, page_size)
    return {
        "items": [
            {
                "sync_id": item.id,
                "sync_type": item.sync_type,
                "source": item.source,
                "status": item.status,
                "added": item.added_count,
                "updated": item.updated_count,
                "deleted": item.deleted_count,
                "completed_at": item.completed_at,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }
