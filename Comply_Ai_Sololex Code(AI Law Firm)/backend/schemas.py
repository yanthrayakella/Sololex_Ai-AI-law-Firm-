from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterBody(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    company: str = ""
    subscription_tier: str = Field(pattern="^(basic|pro)$")


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    company: str
    subscription_tier: str
    wechat_openid: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateBody(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    wechat_openid: Optional[str] = None


class ContractUploadMeta(BaseModel):
    contract_type: str = Field(pattern="^(employment|supplier|lease|service)$")


class ClauseItem(BaseModel):
    id: str
    title: str
    text: str
    category: str
    status: str  # compliant | review | non_compliant
    regulation_ref: Optional[str] = None
    fine_amount: Optional[str] = None
    suggested_fix: Optional[str] = None


class ContractSummary(BaseModel):
    id: str
    name: str
    type: str
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class ContractDetailResponse(BaseModel):
    id: str
    name: str
    type: str
    risk_score: int
    file_path: str
    clauses: list[dict[str, Any]]
    created_at: datetime


class AlertItem(BaseModel):
    id: str
    contract_id: Optional[str]
    regulation_id: Optional[str]
    severity: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    compliance_score: int
    open_alerts: int
    contracts_count: int
    high_severity_count: int


class FixRequestBody(BaseModel):
    clause_id: str
    apply_automatic: bool = False
