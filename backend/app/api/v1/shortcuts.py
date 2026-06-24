"""网站快捷链接 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.dependencies import get_current_user

# 内置默认快捷链接
DEFAULT_SHORTCUTS = [
    {"id": 1, "name": "QRZ.com", "url": "https://www.qrz.com", "description": "Amateur radio callsign database"},
    {"id": 2, "name": "ARRL DXCC", "url": "https://www.arrl.org/dxcc", "description": "DXCC entities list"},
    {"id": 3, "name": "LOTW", "url": "https://lotw.arrl.org", "description": "ARRL Logbook of the World"},
    {"id": 4, "name": "Clublog", "url": "https://clublog.org/", "description": "Amateur Radio League Tables"},
    {"id": 5, "name": "DXWatch", "url": "https://dxwatch.com", "description": "Real-time DX cluster spots"},
    {"id": 6, "name": "PSK Reporter", "url": "https://pskreporter.info", "description": "PSK propagation reporting"},
]

router = APIRouter()

# 用户自定义快捷链接（内存存储，后续可持久化）
_user_shortcuts: dict = {}
_shortcut_counter: int = 1000  # 自增 ID，避免与默认 ID 碰撞


@router.get("")
async def get_shortcuts(
    current_user=Depends(get_current_user),
):
    """获取快捷链接列表"""
    user_id = current_user.id
    custom = _user_shortcuts.get(user_id, [])
    return DEFAULT_SHORTCUTS + custom


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_shortcut(
    name: str,
    url: str,
    description: str = "",
    current_user=Depends(get_current_user),
):
    """添加快捷链接"""
    global _shortcut_counter
    user_id = current_user.id
    if user_id not in _user_shortcuts:
        _user_shortcuts[user_id] = []

    _shortcut_counter += 1
    shortcut = {
        "id": _shortcut_counter,
        "name": name,
        "url": url,
        "description": description,
    }
    _user_shortcuts[user_id].append(shortcut)
    return shortcut


@router.delete("/{shortcut_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shortcut(
    shortcut_id: int,
    current_user=Depends(get_current_user),
):
    """删除快捷链接"""
    user_id = current_user.id
    custom = _user_shortcuts.get(user_id, [])
    _user_shortcuts[user_id] = [s for s in custom if s["id"] != shortcut_id]
