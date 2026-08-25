import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as api from "../api/client";
import { ApiError } from "../api/client";
import type { Comment, Ticket, TicketStatus, User } from "../api/types";
import { PriorityBadge, StatusBadge } from "../components/Badges";
import { useAuth } from "../context/AuthContext";

const STATUSES: TicketStatus[] = ["open", "in_progress", "resolved", "closed"];

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const ticketId = Number(id);
  const { user } = useAuth();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [agents, setAgents] = useState<User[]>([]);
  const [newComment, setNewComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isStaff = user?.role === "admin" || user?.role === "agent";

  const load = useCallback(async () => {
    try {
      const [t, c] = await Promise.all([api.getTicket(ticketId), api.listComments(ticketId)]);
      setTicket(t);
      setComments(c);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load ticket");
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (isStaff) api.listAgents().then(setAgents).catch(() => undefined);
  }, [isStaff]);

  async function handleStatusChange(status: TicketStatus) {
    setBusy(true);
    try {
      const updated = await api.updateTicketStatus(ticketId, status);
      setTicket(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update status");
    } finally {
      setBusy(false);
    }
  }

  async function handleAssign(assignedToId: number) {
    setBusy(true);
    try {
      const updated = await api.assignTicket(ticketId, assignedToId);
      setTicket(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to assign ticket");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddComment(e: FormEvent) {
    e.preventDefault();
    if (!newComment.trim()) return;
    setBusy(true);
    try {
      const comment = await api.addComment(ticketId, newComment);
      setComments((prev) => [...prev, comment]);
      setNewComment("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add comment");
    } finally {
      setBusy(false);
    }
  }

  if (error && !ticket) return <div className="error-banner">{error}</div>;
  if (!ticket) return <div className="page-loading">Loading…</div>;

  return (
    <div className="ticket-detail">
      <div className="ticket-header">
        <div>
          <h1>
            #{ticket.id} {ticket.title}
          </h1>
          <div className="badge-row">
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
            <span className="category-tag">{ticket.category}</span>
          </div>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="ticket-body">
        <section className="panel description-panel">
          <h2>Description</h2>
          <p>{ticket.description}</p>
          <dl className="meta-list">
            <dt>Reported by</dt>
            <dd>{ticket.creator.full_name}</dd>
            <dt>Assigned to</dt>
            <dd>{ticket.assignee?.full_name ?? "Unassigned"}</dd>
            <dt>Created</dt>
            <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
            <dt>Last updated</dt>
            <dd>{new Date(ticket.updated_at).toLocaleString()}</dd>
            {ticket.resolved_at && (
              <>
                <dt>Resolved</dt>
                <dd>{new Date(ticket.resolved_at).toLocaleString()}</dd>
              </>
            )}
          </dl>
        </section>

        {isStaff && (
          <section className="panel">
            <h2>Manage</h2>
            <label>
              Status
              <select
                value={ticket.status}
                disabled={busy}
                onChange={(e) => handleStatusChange(e.target.value as TicketStatus)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Assignee
              <select
                value={ticket.assignee?.id ?? ""}
                disabled={busy}
                onChange={(e) => handleAssign(Number(e.target.value))}
              >
                <option value="" disabled>
                  Select agent…
                </option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.full_name}
                  </option>
                ))}
              </select>
            </label>
          </section>
        )}
      </div>

      <section className="panel comments-panel">
        <h2>Activity</h2>
        <ul className="comment-list">
          {comments.map((c) => (
            <li key={c.id}>
              <div className="comment-meta">
                <strong>{c.author.full_name}</strong>
                <span>{new Date(c.created_at).toLocaleString()}</span>
              </div>
              <p>{c.body}</p>
            </li>
          ))}
          {comments.length === 0 && <li className="empty-row">No comments yet.</li>}
        </ul>
        <form onSubmit={handleAddComment} className="comment-form">
          <textarea
            placeholder="Add an update…"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            rows={3}
          />
          <button type="submit" disabled={busy || !newComment.trim()}>
            Post
          </button>
        </form>
      </section>
    </div>
  );
}
