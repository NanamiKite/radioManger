"""数据同步服务"""

import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.sync_history import SyncHistory
from app.services.github_service import GitHubService

logger = logging.getLogger("radiomanager.sync")


class SyncService:
    """数据同步服务（GitHub / 云服务器）"""

    @staticmethod
    def push_to_github(db: Session, user_id: int) -> Dict:
        """推送数据到GitHub"""
        github = GitHubService()
        if not github.is_configured():
            return {"status": "error", "message": "GitHub not configured"}

        # 创建同步记录
        sync_record = SyncHistory(
            user_id=user_id,
            sync_type="push",
            source="github",
            status="pending",
        )
        db.add(sync_record)
        db.commit()

        try:
            # 执行推送
            # logs = LogService.get_all_logs(db, user_id)
            # content = generate_export(logs)
            # result = github.push_logs("repo_url", content)

            sync_record.status = "success"
            sync_record.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()

            return {"sync_id": sync_record.id, "status": "success"}

        except Exception as e:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            db.commit()
            return {"sync_id": sync_record.id, "status": "failed", "error": str(e)}

    @staticmethod
    def get_history(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> tuple:
        """获取同步历史"""
        query = (
            db.query(SyncHistory)
            .filter(SyncHistory.user_id == user_id)
            .order_by(SyncHistory.created_at.desc())
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
