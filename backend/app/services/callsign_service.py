"""呼号查询服务"""

import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.callsign_cache import CallsignCache
from app.utils.qrz_client import QRZClient

logger = logging.getLogger("radiomanager.callsign")


class CallsignService:
    """呼号查询服务（支持本地缓存 + QRZ.com）"""

    @staticmethod
    def lookup(db: Session, call_sign: str) -> Optional[Dict]:
        """查询呼号（先查缓存，再查QRZ）"""
        call_sign = call_sign.upper().strip()

        # 1. 查本地缓存
        cached = (
            db.query(CallsignCache)
            .filter(CallsignCache.call_sign == call_sign)
            .first()
        )
        if cached:
            result = CallsignService._model_to_dict(cached)
            result["cached"] = True
            result["cached_at"] = cached.cached_at
            return result

        # 2. 查QRZ
        try:
            client = QRZClient()
            qrz_data = client.lookup(call_sign)
            client.close()
        except Exception as e:
            logger.warning(f"QRZ lookup failed: {e}")
            qrz_data = None

        if qrz_data:
            # 写入缓存
            cache_entry = CallsignService._save_cache(db, qrz_data)
            qrz_data["cached"] = False
            qrz_data["cached_at"] = cache_entry.cached_at
            return qrz_data

        return None

    @staticmethod
    def _model_to_dict(cache: CallsignCache) -> Dict:
        """将模型转为字典"""
        return {
            "call_sign": cache.call_sign,
            "first_name": cache.first_name,
            "last_name": cache.last_name,
            "full_name": cache.full_name,
            "country": cache.country,
            "grid_square": cache.grid_square,
            "latitude": float(cache.latitude) if cache.latitude else None,
            "longitude": float(cache.longitude) if cache.longitude else None,
            "class_type": cache.class_type,
            "license_date": cache.license_date,
            "license_exp": cache.license_exp,
            "previous_call": cache.previous_call,
            "qrz_url": cache.qrz_url,
        }

    @staticmethod
    def _save_cache(db: Session, data: Dict) -> CallsignCache:
        """保存呼号到缓存"""
        cache = CallsignCache(
            call_sign=data["call_sign"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            full_name=data.get("full_name"),
            country=data.get("country"),
            grid_square=data.get("grid_square"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            class_type=data.get("class_type"),
            license_date=data.get("license_date"),
            license_exp=data.get("license_exp"),
            previous_call=data.get("previous_call"),
            qrz_url=data.get("qrz_url"),
            cached_at=datetime.utcnow(),
        )
        db.add(cache)
        db.commit()
        db.refresh(cache)
        return cache

    @staticmethod
    def clear_cache(db: Session, call_sign: str) -> bool:
        """清除呼号缓存"""
        cached = (
            db.query(CallsignCache)
            .filter(CallsignCache.call_sign == call_sign.upper().strip())
            .first()
        )
        if cached:
            db.delete(cached)
            db.commit()
            return True
        return False

    @staticmethod
    def search(db: Session, prefix: str, country: Optional[str] = None) -> list:
        """搜索缓存的呼号"""
        query = db.query(CallsignCache).filter(
            CallsignCache.call_sign.ilike(f"{prefix}%")
        )
        if country:
            query = query.filter(CallsignCache.country.ilike(f"%{country}%"))
        return [CallsignService._model_to_dict(c) for c in query.limit(20).all()]
