"""系统配置服务"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig


# 预置配置项
DEFAULT_CONFIGS = {
    "dxcluster_nodes": {"value": "[]", "type": "json", "desc": "DX Cluster节点列表"},
    "qrz_api_key": {"value": "", "type": "string", "desc": "QRZ API密钥"},
    "import_enabled": {"value": "true", "type": "bool", "desc": "允许导入"},
    "export_enabled": {"value": "true", "type": "bool", "desc": "允许导出"},
    "rate_limit_per_minute": {"value": "100", "type": "int", "desc": "每分钟API请求限制"},
    "max_import_records": {"value": "10000", "type": "int", "desc": "单次导入最大记录数"},
    "maintenance_mode": {"value": "false", "type": "bool", "desc": "维护模式"},
}


class ConfigService:
    """系统配置服务"""

    @staticmethod
    def get_all(db: Session) -> list:
        """获取所有配置"""
        configs = db.query(SystemConfig).all()
        if not configs:
            # 首次访问时初始化默认配置（防并发竞争）
            try:
                for key, info in DEFAULT_CONFIGS.items():
                    config = SystemConfig(
                        key=key, value=info["value"],
                        value_type=info["type"], description=info["desc"]
                    )
                    db.add(config)
                db.commit()
                configs = db.query(SystemConfig).all()
            except Exception:
                db.rollback()
                configs = db.query(SystemConfig).all()
        return configs

    @staticmethod
    def get_value(db: Session, key: str) -> Optional[str]:
        """获取单个配置值"""
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return config.value if config else None

    @staticmethod
    def update(db: Session, key: str, value: str, user_id: int) -> Optional[SystemConfig]:
        """更新配置"""
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = value
            config.updated_by = user_id
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def get_bool(db: Session, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        val = ConfigService.get_value(db, key)
        if val is None:
            return default
        return val.lower() in ("true", "1", "yes")

    @staticmethod
    def get_int(db: Session, key: str, default: int = 0) -> int:
        """获取整数配置"""
        val = ConfigService.get_value(db, key)
        if val is None:
            return default
        try:
            return int(val)
        except ValueError:
            return default
