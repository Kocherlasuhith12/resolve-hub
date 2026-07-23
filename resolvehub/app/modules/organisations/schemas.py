from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganisationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=2, max_length=80)


class OrganisationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    is_active: bool


class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: UUID


class InvitationResponse(BaseModel):
    id: UUID
    email: EmailStr
    expires_at: datetime
    invitation_token: str | None = None


class InvitationLifecycleResponse(BaseModel):
    id: UUID
    email: EmailStr
    role_id: UUID
    status: str
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    invitation_token: str | None = None


class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organisation_id: UUID
    name: str
    description: str | None
    is_active: bool


class MembershipResponse(BaseModel):
    id: UUID
    organisation_id: UUID
    user_id: UUID
    role_id: UUID
    role_name: str


class MembershipDirectoryResponse(MembershipResponse):
    display_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class CurrentMembershipResponse(MembershipResponse):
    permissions: list[str]


class RoleResponse(BaseModel):
    id: UUID
    name: str
    permissions: list[str]


class MemberRoleUpdate(BaseModel):
    role_id: UUID


class MemberStatusUpdate(BaseModel):
    is_active: bool
