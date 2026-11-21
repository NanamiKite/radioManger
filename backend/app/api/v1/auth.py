from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.database.session import get_db
from app.schemas.user import Password, UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate
from app.services.user_service import UserService
from app.utils.security import SecurityUtils
from app.config import settings
from app.dependencies import get_current_user
from app.exceptions import AuthException
from app.services.session_service import SessionService



class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: Password
    confirm_password: Password


class DeleteAccountRequest(BaseModel):
    password: str


class ConfirmDeleteRequest(BaseModel):
    code: str


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = UserService.create_user(db, user_data)

        # 审计日志
        if settings.DATABASE_MODE == "mysql":
            from app.services.audit_service import AuditService
            AuditService.log(db, user, "REGISTER",
                             ip_address=request.client.host if request.client else None)

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """用户登录"""
    user = UserService.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise AuthException("Invalid credentials")

    access_token, access_jti = SecurityUtils.create_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    ip = request.client.host if request.client else None
    SessionService.create_session(
        db, user.id, access_jti,
        ip_address=ip, user_agent=request.headers.get("user-agent", "")[:500],
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    db.commit()
    if settings.DATABASE_MODE == "mysql":
        from app.services.audit_service import AuditService
        AuditService.log(db, user, "LOGIN", ip_address=ip)
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user=Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_user_info(
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新用户信息"""
    user = UserService.update_user(db, current_user, user_data)

    if settings.DATABASE_MODE == "mysql":
        from app.services.audit_service import AuditService
        AuditService.log(db, user, "UPDATE_PROFILE",
                         ip_address=request.client.host if request.client else None)

    return user


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """修改密码"""
    if req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Passwords do not match"
        )

    try:
        UserService.change_password(db, current_user, req.old_password, req.new_password)

        if settings.DATABASE_MODE == "mysql":
            from app.services.audit_service import AuditService
            AuditService.log(db, current_user, "CHANGE_PASSWORD",
                             ip_address=request.client.host if request.client else None)

        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Revoke the authenticated session before reporting a successful logout."""
    SessionService.remove_session(db, request.state.auth_jti)
    db.commit()
    if settings.DATABASE_MODE == "mysql":
        from app.services.audit_service import AuditService
        ip = request.client.host if request.client else None
        AuditService.log(db, current_user, "LOGOUT", ip_address=ip)

    return {"message": "Logout successful"}


# ── 账号注销（仅服务器模式）──

@router.post("/delete-account")
def request_delete_account(
    req: DeleteAccountRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """申请注销账号 - 进入 30 天冷却期"""
    if settings.DATABASE_MODE == "sqlite":
        raise HTTPException(status_code=400, detail="Account deletion not available in local mode")

    # 验证密码
    if not SecurityUtils.verify_password(req.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    # 检查是否已在冷却期
    if current_user.deletion_scheduled_at and not current_user.deletion_cancelled:
        raise HTTPException(status_code=400, detail="Deletion already scheduled")

    # 设置冷却期
    current_user.deletion_scheduled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    current_user.deletion_cancelled = False
    db.commit()

    # 发送验证邮件（预留接口，当前跳过）
    from app.services.email_service import EmailService
    code = EmailService.generate_code()
    EmailService.store_code(current_user.email, code, "delete_account")
    # EmailService.send_verification_code(current_user.email, code, "delete_account")

    # 审计日志
    from app.services.audit_service import AuditService
    AuditService.log(db, current_user, "DELETE_ACCOUNT_REQUEST",
                     ip_address=request.client.host if request.client else None)

    return {
        "message": "Account deletion scheduled. You have 30 days to cancel.",
        "scheduled_at": current_user.deletion_scheduled_at.isoformat(),
        "cooldown_days": 30,
        # "verification_code": code,  # 开发模式下返回，生产环境通过邮件发送
    }


@router.post("/cancel-delete")
def cancel_delete_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """撤销注销申请"""
    if settings.DATABASE_MODE == "sqlite":
        raise HTTPException(status_code=400, detail="Not available in local mode")

    if not current_user.deletion_scheduled_at:
        raise HTTPException(status_code=400, detail="No deletion scheduled")

    current_user.deletion_scheduled_at = None
    current_user.deletion_cancelled = False
    db.commit()

    # 审计日志
    from app.services.audit_service import AuditService
    AuditService.log(db, current_user, "CANCEL_DELETE_ACCOUNT",
                     ip_address=request.client.host if request.client else None)

    return {"message": "Account deletion cancelled"}


@router.post("/confirm-delete")
def confirm_delete_account(
    req: ConfirmDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """确认注销账号 - 需要验证码"""
    if settings.DATABASE_MODE == "sqlite":
        raise HTTPException(status_code=400, detail="Not available in local mode")

    if not current_user.deletion_scheduled_at:
        raise HTTPException(status_code=400, detail="No deletion scheduled")

    # 校验冷却期：必须过了 30 天
    cooldown_end = current_user.deletion_scheduled_at + timedelta(days=30)
    if datetime.now(timezone.utc).replace(tzinfo=None) < cooldown_end:
        remaining = (cooldown_end - datetime.now(timezone.utc).replace(tzinfo=None)).days
        raise HTTPException(status_code=400, detail=f"Cooldown period not ended. {remaining} days remaining.")

    # 验证码校验
    from app.services.email_service import EmailService
    if not EmailService.verify_code(current_user.email, req.code, "delete_account"):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # 软删除用户
    current_user.is_deleted = True
    current_user.is_active = False
    current_user.deletion_scheduled_at = None
    SessionService.remove_all_sessions(db, current_user.id)
    db.commit()

    # 审计日志
    from app.services.audit_service import AuditService
    AuditService.log(db, current_user, "DELETE_ACCOUNT_CONFIRM",
                     ip_address=request.client.host if request.client else None)

    return {"message": "Account deleted successfully"}
