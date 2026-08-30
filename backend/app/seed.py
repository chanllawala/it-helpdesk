"""Populate the database with demo users and tickets. Run with: python -m app.seed"""

from datetime import timedelta

from .timeutil import utcnow

from .database import Base, SessionLocal, engine
from .models import Comment, Ticket, TicketPriority, TicketStatus, User, UserRole
from .security import hash_password

Base.metadata.create_all(bind=engine)


def run():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded, skipping.")
            return

        admin = User(
            email="admin@helpdesk.example",
            full_name="Alex Admin",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
        )
        agent = User(
            email="agent@helpdesk.example",
            full_name="Sam Agent",
            hashed_password=hash_password("agent123"),
            role=UserRole.AGENT,
        )
        user = User(
            email="user@helpdesk.example",
            full_name="Jamie User",
            hashed_password=hash_password("user123"),
            role=UserRole.USER,
        )
        db.add_all([admin, agent, user])
        db.commit()
        db.refresh(admin)
        db.refresh(agent)
        db.refresh(user)

        t1 = Ticket(
            title="Can't connect to VPN",
            description="Getting a timeout error when connecting to the corporate VPN from home.",
            category="Network",
            priority=TicketPriority.HIGH,
            status=TicketStatus.IN_PROGRESS,
            created_by_id=user.id,
            assigned_to_id=agent.id,
            created_at=utcnow() - timedelta(days=2),
        )
        t2 = Ticket(
            title="New laptop request",
            description="My laptop is 5 years old and struggling to run our IDE.",
            category="Hardware",
            priority=TicketPriority.LOW,
            status=TicketStatus.OPEN,
            created_by_id=user.id,
            created_at=utcnow() - timedelta(days=1),
        )
        t3 = Ticket(
            title="Password reset for shared drive",
            description="Locked out of the finance shared drive after too many failed attempts.",
            category="Access",
            priority=TicketPriority.URGENT,
            status=TicketStatus.RESOLVED,
            created_by_id=user.id,
            assigned_to_id=agent.id,
            created_at=utcnow() - timedelta(days=3),
            resolved_at=utcnow() - timedelta(days=2, hours=20),
        )
        db.add_all([t1, t2, t3])
        db.commit()
        db.refresh(t1)

        db.add(
            Comment(
                ticket_id=t1.id,
                author_id=agent.id,
                body="Looking into it — can you confirm which VPN client version you're using?",
            )
        )
        db.commit()
        print("Seed data created:")
        print("  admin@helpdesk.example / admin123")
        print("  agent@helpdesk.example / agent123")
        print("  user@helpdesk.example / user123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
