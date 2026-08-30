"""API behaviour, with the access-control rules given the most attention.

A helpdesk where one user can read another's tickets is not a bug you want to
find in production.
"""

from app.models import UserRole


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_then_login(client):
    client.post(
        "/auth/register",
        json={"email": "new@example.com", "full_name": "New User", "password": "password123"},
    )
    response = client.post(
        "/auth/login", data={"username": "new@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_with_wrong_password_is_rejected(client, make_user):
    make_user("user@example.com")
    response = client.post(
        "/auth/login", data={"username": "user@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


def test_duplicate_email_is_rejected(client, make_user):
    make_user("taken@example.com")
    response = client.post(
        "/auth/register",
        json={"email": "taken@example.com", "full_name": "Other", "password": "password123"},
    )
    assert response.status_code == 400


def test_registration_cannot_grant_admin(client, make_user):
    """Only the very first account may be an admin; after that the requested
    role is ignored, or anyone could sign up as an administrator."""
    make_user("first@example.com", UserRole.ADMIN)

    client.post(
        "/auth/register",
        json={
            "email": "sneaky@example.com",
            "full_name": "Sneaky",
            "password": "password123",
            "role": "admin",
        },
    )
    response = client.post(
        "/auth/login", data={"username": "sneaky@example.com", "password": "password123"}
    )
    token = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/auth/me", headers=token).json()["role"] == "user"


def test_unauthenticated_requests_are_rejected(client):
    assert client.get("/tickets").status_code == 401


def test_create_and_list_own_ticket(client, make_user, login):
    make_user("user@example.com")
    headers = login("user@example.com")

    created = client.post(
        "/tickets",
        json={"title": "Printer jammed", "description": "Tray 2", "priority": "high"},
        headers=headers,
    )
    assert created.status_code == 201

    listed = client.get("/tickets", headers=headers).json()
    assert [t["title"] for t in listed] == ["Printer jammed"]


def test_a_user_cannot_see_another_users_tickets(client, make_user, login):
    make_user("alice@example.com")
    make_user("bob@example.com")

    alice = login("alice@example.com")
    client.post(
        "/tickets", json={"title": "Alice only", "description": "private"}, headers=alice
    )

    bob = login("bob@example.com")
    assert client.get("/tickets", headers=bob).json() == []


def test_a_user_cannot_read_another_users_ticket_directly(client, make_user, login):
    make_user("alice@example.com")
    make_user("bob@example.com")

    alice = login("alice@example.com")
    ticket_id = client.post(
        "/tickets", json={"title": "Alice only", "description": "private"}, headers=alice
    ).json()["id"]

    bob = login("bob@example.com")
    assert client.get(f"/tickets/{ticket_id}", headers=bob).status_code == 403


def test_an_agent_sees_every_ticket(client, make_user, login):
    make_user("user@example.com")
    make_user("agent@example.com", UserRole.AGENT)

    user = login("user@example.com")
    client.post("/tickets", json={"title": "Theirs", "description": "x"}, headers=user)

    agent = login("agent@example.com")
    assert len(client.get("/tickets", headers=agent).json()) == 1


def test_a_standard_user_cannot_change_status(client, make_user, login):
    make_user("user@example.com")
    headers = login("user@example.com")
    ticket_id = client.post(
        "/tickets", json={"title": "T", "description": "x"}, headers=headers
    ).json()["id"]

    response = client.post(
        f"/tickets/{ticket_id}/status", json={"status": "resolved"}, headers=headers
    )
    assert response.status_code == 403


def test_resolving_records_a_timestamp(client, make_user, login):
    """The dashboard's average resolution time depends on this being set."""
    make_user("user@example.com")
    make_user("agent@example.com", UserRole.AGENT)

    ticket_id = client.post(
        "/tickets",
        json={"title": "T", "description": "x"},
        headers=login("user@example.com"),
    ).json()["id"]

    agent = login("agent@example.com")
    resolved = client.post(
        f"/tickets/{ticket_id}/status", json={"status": "resolved"}, headers=agent
    ).json()

    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None


def test_reopening_clears_the_resolution_timestamp(client, make_user, login):
    make_user("user@example.com")
    make_user("agent@example.com", UserRole.AGENT)

    ticket_id = client.post(
        "/tickets", json={"title": "T", "description": "x"}, headers=login("user@example.com")
    ).json()["id"]

    agent = login("agent@example.com")
    client.post(f"/tickets/{ticket_id}/status", json={"status": "resolved"}, headers=agent)
    reopened = client.post(
        f"/tickets/{ticket_id}/status", json={"status": "in_progress"}, headers=agent
    ).json()

    assert reopened["resolved_at"] is None


def test_assignment_requires_a_staff_assignee(client, make_user, login):
    make_user("user@example.com")
    make_user("agent@example.com", UserRole.AGENT)
    plain = make_user("other@example.com")

    ticket_id = client.post(
        "/tickets", json={"title": "T", "description": "x"}, headers=login("user@example.com")
    ).json()["id"]

    agent = login("agent@example.com")
    response = client.post(
        f"/tickets/{ticket_id}/assign", json={"assigned_to_id": plain.id}, headers=agent
    )
    assert response.status_code == 400


def test_comment_thread(client, make_user, login):
    make_user("user@example.com")
    make_user("agent@example.com", UserRole.AGENT)

    user = login("user@example.com")
    ticket_id = client.post(
        "/tickets", json={"title": "T", "description": "x"}, headers=user
    ).json()["id"]

    client.post(f"/tickets/{ticket_id}/comments", json={"body": "Any update?"}, headers=user)
    client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "Looking now"},
        headers=login("agent@example.com"),
    )

    comments = client.get(f"/tickets/{ticket_id}/comments", headers=user).json()
    assert [c["body"] for c in comments] == ["Any update?", "Looking now"]


def test_filtering_by_status(client, make_user, login):
    make_user("user@example.com")
    make_user("agent@example.com", UserRole.AGENT)
    user = login("user@example.com")

    open_id = client.post(
        "/tickets", json={"title": "Still open", "description": "x"}, headers=user
    ).json()["id"]
    client.post("/tickets", json={"title": "Will resolve", "description": "x"}, headers=user)

    agent = login("agent@example.com")
    client.post(f"/tickets/{open_id}/status", json={"status": "resolved"}, headers=agent)

    resolved = client.get("/tickets?status_filter=resolved", headers=agent).json()
    assert [t["title"] for t in resolved] == ["Still open"]


def test_dashboard_counts_reflect_tickets(client, make_user, login):
    make_user("agent@example.com", UserRole.AGENT)
    headers = login("agent@example.com")
    client.post("/tickets", json={"title": "A", "description": "x"}, headers=headers)

    stats = client.get("/dashboard/stats", headers=headers).json()
    assert stats["total_tickets"] == 1
    assert stats["open_tickets"] == 1
