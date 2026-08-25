from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import UserRole, TicketStatus, TicketPriority


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.USER


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Comments ----------

class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    body: str
    created_at: datetime
    author: UserOut


# ---------- Tickets ----------

class TicketCreate(BaseModel):
    title: str
    description: str
    category: str = "general"
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[TicketPriority] = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketAssign(BaseModel):
    assigned_to_id: int


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    creator: UserOut
    assignee: Optional[UserOut] = None


class TicketListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    creator: UserOut
    assignee: Optional[UserOut] = None


# ---------- Dashboard ----------

class StatusCount(BaseModel):
    status: TicketStatus
    count: int


class PriorityCount(BaseModel):
    priority: TicketPriority
    count: int


class DashboardStats(BaseModel):
    total_tickets: int
    by_status: list[StatusCount]
    by_priority: list[PriorityCount]
    average_resolution_hours: Optional[float] = None
    open_tickets: int
    unassigned_tickets: int
