import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_tickets = relationship(
        "Ticket", back_populates="creator", foreign_keys="Ticket.created_by_id"
    )
    assigned_tickets = relationship(
        "Ticket", back_populates="assignee", foreign_keys="Ticket.assigned_to_id"
    )
    comments = relationship("Comment", back_populates="author")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, default="general")
    priority = Column(SAEnum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    status = Column(SAEnum(TicketStatus), nullable=False, default=TicketStatus.OPEN)

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    creator = relationship("User", back_populates="created_tickets", foreign_keys=[created_by_id])
    assignee = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_to_id])
    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="ticket", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Notification(Base):
    """Simulated notification log — a real system would send email/Slack here."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    recipient_email = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="notifications")
