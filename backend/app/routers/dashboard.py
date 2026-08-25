from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Ticket)
    if current_user.role == models.UserRole.USER:
        query = query.filter(models.Ticket.created_by_id == current_user.id)

    tickets = query.all()
    total = len(tickets)

    status_counts: dict[models.TicketStatus, int] = {}
    priority_counts: dict[models.TicketPriority, int] = {}
    for t in tickets:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1

    resolved = [t for t in tickets if t.resolved_at is not None]
    if resolved:
        total_hours = sum((t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved)
        avg_hours = round(total_hours / len(resolved), 2)
    else:
        avg_hours = None

    return schemas.DashboardStats(
        total_tickets=total,
        by_status=[schemas.StatusCount(status=s, count=c) for s, c in status_counts.items()],
        by_priority=[schemas.PriorityCount(priority=p, count=c) for p, c in priority_counts.items()],
        average_resolution_hours=avg_hours,
        open_tickets=status_counts.get(models.TicketStatus.OPEN, 0),
        unassigned_tickets=sum(1 for t in tickets if t.assigned_to_id is None),
    )
