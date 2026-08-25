from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/agents", response_model=list[schemas.UserOut])
def list_agents(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """List agents and admins, for populating ticket-assignment dropdowns."""
    return (
        db.query(models.User)
        .filter(models.User.role.in_([models.UserRole.AGENT, models.UserRole.ADMIN]))
        .order_by(models.User.full_name)
        .all()
    )
