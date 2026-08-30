from datetime import datetime, date

from ..timeutil import utcnow
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_agent_or_admin

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _log_notification(db: Session, ticket: models.Ticket, message: str) -> None:
    """Simulated notification — logs to the DB (and stdout) instead of sending real email."""
    recipients = {ticket.creator.email}
    if ticket.assignee:
        recipients.add(ticket.assignee.email)
    for email in recipients:
        note = models.Notification(ticket_id=ticket.id, recipient_email=email, message=message)
        db.add(note)
    print(f"[notify] ticket #{ticket.id} -> {recipients}: {message}")


def _can_view(ticket: models.Ticket, user: models.User) -> bool:
    if user.role in (models.UserRole.ADMIN, models.UserRole.AGENT):
        return True
    return ticket.created_by_id == user.id


def _get_ticket_or_404(db: Session, ticket_id: int) -> models.Ticket:
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("", response_model=schemas.TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ticket = models.Ticket(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        created_by_id=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    _log_notification(db, ticket, f"Ticket #{ticket.id} created: {ticket.title}")
    db.commit()
    return ticket


@router.get("", response_model=list[schemas.TicketListItem])
def list_tickets(
    status_filter: Optional[models.TicketStatus] = None,
    priority: Optional[models.TicketPriority] = None,
    assigned_to_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Ticket)

    if current_user.role == models.UserRole.USER:
        query = query.filter(models.Ticket.created_by_id == current_user.id)

    if status_filter:
        query = query.filter(models.Ticket.status == status_filter)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    if assigned_to_id:
        query = query.filter(models.Ticket.assigned_to_id == assigned_to_id)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(models.Ticket.title.ilike(like), models.Ticket.description.ilike(like)))
    if date_from:
        query = query.filter(models.Ticket.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(models.Ticket.created_at <= datetime.combine(date_to, datetime.max.time()))

    return query.order_by(models.Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_view(ticket, current_user):
        raise HTTPException(status_code=403, detail="You cannot view this ticket")
    return ticket


@router.patch("/{ticket_id}", response_model=schemas.TicketOut)
def update_ticket(
    ticket_id: int,
    payload: schemas.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    is_owner = ticket.created_by_id == current_user.id
    is_staff = current_user.role in (models.UserRole.ADMIN, models.UserRole.AGENT)
    if not (is_owner or is_staff):
        raise HTTPException(status_code=403, detail="You cannot edit this ticket")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assign", response_model=schemas.TicketOut)
def assign_ticket(
    ticket_id: int,
    payload: schemas.TicketAssign,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_agent_or_admin),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    assignee = db.query(models.User).filter(models.User.id == payload.assigned_to_id).first()
    if not assignee or assignee.role not in (models.UserRole.AGENT, models.UserRole.ADMIN):
        raise HTTPException(status_code=400, detail="Assignee must be an agent or admin")

    ticket.assigned_to_id = assignee.id
    db.commit()
    db.refresh(ticket)
    _log_notification(db, ticket, f"Ticket #{ticket.id} assigned to {assignee.full_name}")
    db.commit()
    return ticket


@router.post("/{ticket_id}/status", response_model=schemas.TicketOut)
def update_status(
    ticket_id: int,
    payload: schemas.TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_agent_or_admin),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    ticket.status = payload.status

    if payload.status == models.TicketStatus.RESOLVED and ticket.resolved_at is None:
        ticket.resolved_at = utcnow()
    if payload.status == models.TicketStatus.CLOSED and ticket.closed_at is None:
        ticket.closed_at = utcnow()
    if payload.status in (models.TicketStatus.OPEN, models.TicketStatus.IN_PROGRESS):
        ticket.resolved_at = None
        ticket.closed_at = None

    db.commit()
    db.refresh(ticket)
    _log_notification(db, ticket, f"Ticket #{ticket.id} status changed to {payload.status.value}")
    db.commit()
    return ticket


@router.get("/{ticket_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_view(ticket, current_user):
        raise HTTPException(status_code=403, detail="You cannot view this ticket")
    return (
        db.query(models.Comment)
        .filter(models.Comment.ticket_id == ticket_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )


@router.post("/{ticket_id}/comments", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: int,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_view(ticket, current_user):
        raise HTTPException(status_code=403, detail="You cannot comment on this ticket")

    comment = models.Comment(ticket_id=ticket_id, author_id=current_user.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    _log_notification(db, ticket, f"New comment on ticket #{ticket.id} by {current_user.full_name}")
    db.commit()
    return comment
