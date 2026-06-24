"""呼号查询服务"""

import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.callsign_cache import CallsignCache
from app.utils.qrz_client import QRZClient
from app.config import settings
from app.utils.dxcc import lookup_dxcc

logger = logging.getLogger("radiomanager.callsign")


class CallsignService:
    """呼号查询服务（支持本地缓存 + QRZ.com + 离线DXCC推断）"""

    @staticmethod
    def lookup(db: Session, call_sign: str) -> Optional[Dict]:
        """查询呼号（先查缓存，再查QRZ，QRZ不可用时返回离线DXCC数据）"""
        call_sign = call_sign.upper().strip()

        # 1. 查本地缓存
        cached = (
            db.query(CallsignCache)
            .filter(CallsignCache.call_sign == call_sign)
            .first()
        )
        if cached and cached.cached_at:
            # 缓存超过30天仍尝试QRZ刷新
            age = (datetime.now(timezone.utc).replace(tzinfo=None) - cached.cached_at).days
            if age < 30:
                result = CallsignService._model_to_dict(cached)
                result["cached"] = True
                result["cached_at"] = cached.cached_at
                return result

        # 2. 查QRZ（如果配置了凭证）
        qrz_configured = bool(settings.QRZ_USERNAME and settings.QRZ_PASSWORD)
        qrz_data = None
        if qrz_configured:
            try:
                client = QRZClient()
                qrz_data = client.lookup(call_sign)
                client.close()
            except Exception as e:
                logger.warning(f"QRZ lookup failed for {call_sign}: {e}")

        if qrz_data:
            cache_entry = CallsignService._save_cache(db, qrz_data)
            qrz_data["cached"] = False
            qrz_data["cached_at"] = cache_entry.cached_at
            return qrz_data

        # 3. 如果缓存已过期但存在，使用缓存
        if cached:
            result = CallsignService._model_to_dict(cached)
            result["cached"] = True
            result["cached_at"] = cached.cached_at
            return result

        # 4. 离线DXCC推断（QRZ不可用时兜底）
        dxcc = lookup_dxcc(call_sign)
        result = {
            "call_sign": call_sign,
            "first_name": None,
            "last_name": None,
            "full_name": None,
            "country": dxcc if dxcc and dxcc != "Unknown" else None,
            "grid_square": None,
            "latitude": None,
            "longitude": None,
            "class_type": None,
            "license_date": None,
            "license_exp": None,
            "previous_call": None,
            "qrz_url": f"https://www.qrz.com/db/{call_sign}",
            "cached": False,
            "cached_at": None,
            "offline": True,
        }
        return result

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
        """保存呼号到缓存（upsert：存在则更新，不存在则插入）"""
        call_sign = data["call_sign"]
        existing = db.query(CallsignCache).filter(CallsignCache.call_sign == call_sign).first()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if existing:
            for key in ["first_name", "last_name", "full_name", "country", "grid_square",
                        "latitude", "longitude", "class_type", "license_date", "license_exp",
                        "previous_call", "qrz_url"]:
                if data.get(key) is not None:
                    setattr(existing, key, data[key])
            existing.cached_at = now
            db.commit()
            db.refresh(existing)
            return existing
        cache = CallsignCache(
            call_sign=call_sign,
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
            cached_at=now,
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
        escaped_prefix = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = db.query(CallsignCache).filter(
            CallsignCache.call_sign.ilike(f"{escaped_prefix}%", escape="\\")
        )
        if country:
            escaped_country = country.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.filter(CallsignCache.country.ilike(f"%{escaped_country}%", escape="\\"))
        return [CallsignService._model_to_dict(c) for c in query.limit(20).all()]
