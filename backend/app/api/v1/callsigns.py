"""呼号查询 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.dependencies import get_current_user
from app.schemas.callsign import (
    CallsignInfo,
    CallsignBatchResponse,
    CallsignQuery,
    CallsignSearchResult,
)
from app.services.callsign_service import CallsignService

router = APIRouter()


# 固定路径路由必须放在 /{call_sign} 之前
@router.get("/search/{prefix}", response_model=CallsignSearchResult)
async def search_callsigns(
    prefix: str,
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """搜索呼号前缀"""
    results = CallsignService.search(db, prefix, country)
    return CallsignSearchResult(results=results)


@router.delete("/cache/{call_sign}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_callsign_cache(
    call_sign: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """清除呼号缓存"""
    CallsignService.clear_cache(db, call_sign)


@router.post("/batch-query", response_model=CallsignBatchResponse)
async def batch_query_callsigns(
    query: CallsignQuery,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批量查询呼号"""
    results = []
    for cs in query.call_signs[:50]:
        result = CallsignService.lookup(db, cs)
        if result:
            results.append(result)

    return CallsignBatchResponse(
        results=results,
        found=len(results),
        not_found=len(query.call_signs) - len(results),
    )


@router.get("/{call_sign}", response_model=CallsignInfo)
async def lookup_callsign(
    call_sign: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """查询单个呼号（离线时返回DXCC推断结果）"""
    result = CallsignService.lookup(db, call_sign)
    if not result:
        raise HTTPException(status_code=404, detail="Callsign not found")
    return result
