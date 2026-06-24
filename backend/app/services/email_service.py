"""邮箱服务 - 预留接口，等有SMTP服务时启用"""
import logging
from typing import Optional

logger = logging.getLogger("radiomanager.email")


class EmailService:
    """邮箱服务（预留）"""

    @staticmethod
    def send_verification_code(email: str, code: str, purpose: str = "verify") -> bool:
        """发送验证码邮件
        
        Args:
            email: 收件人邮箱
            code: 6位验证码
            purpose: 用途 (register/delete_account/reset_password)
        
        Returns:
            是否发送成功
        """
        # TODO: 接入SMTP服务后实现
        # 目前直接返回True，跳过邮件发送
        logger.info(f"[EMAIL STUB] Would send code {code} to {email} for {purpose}")
        return True

    @staticmethod
    def generate_code() -> str:
        """生成6位验证码"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    @staticmethod
    def store_code(email: str, code: str, purpose: str, ttl_seconds: int = 300):
        """存储验证码（内存缓存，TTL 5分钟）"""
        # TODO: 接入Redis后使用Redis存储
        # 目前使用内存字典
        if not hasattr(EmailService, '_codes'):
            EmailService._codes = {}
        EmailService._codes[f"{email}:{purpose}"] = {
            "code": code,
            "expires": __import__('time').time() + ttl_seconds
        }

    @staticmethod
    def verify_code(email: str, code: str, purpose: str) -> bool:
        """验证验证码"""
        if not hasattr(EmailService, '_codes'):
            return False
        key = f"{email}:{purpose}"
        entry = EmailService._codes.get(key)
        if not entry:
            return False
        if __import__('time').time() > entry["expires"]:
            del EmailService._codes[key]
            return False
        if entry["code"] == code:
            del EmailService._codes[key]
            return True
        return False
