import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api/client";
import type { TicketFilters, TicketListItem, TicketPriority, TicketStatus } from "../api/types";
import { PriorityBadge, StatusBadge } from "../components/Badges";

const STATUSES: TicketStatus[] = ["open", "in_progress", "resolved", "closed"];
const PRIORITIES: TicketPriority[] = ["low", "medium", "high", "urgent"];

export default function Tickets() {
  const [tickets, setTickets] = useState<TicketListItem[]>([]);
  const [filters, setFilters] = useState<TicketFilters>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .listTickets(filters)
      .then(setTickets)
      .catch(() => setError("Failed to load tickets"))
      .finally(() => setLoading(false));
  }, [filters]);

  function updateFilter<K extends keyof TicketFilters>(key: K, value: TicketFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  }

  return (
    <div>
      <div className="page-header">
        <h1>Tickets</h1>
        <Link to="/tickets/new" className="button-link">
          + New Ticket
        </Link>
      </div>

      <div className="filters">
        <input
          placeholder="Search title or description…"
          onChange={(e) => updateFilter("search", e.target.value)}
        />
        <select onChange={(e) => updateFilter("status_filter", e.target.value as TicketStatus)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
        <select onChange={(e) => updateFilter("priority", e.target.value as TicketPriority)}>
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <input type="date" onChange={(e) => updateFilter("date_from", e.target.value)} />
        <input type="date" onChange={(e) => updateFilter("date_to", e.target.value)} />
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading ? (
        <div className="page-loading">Loading…</div>
      ) : (
        <table className="ticket-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Title</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assignee</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>
                  <Link to={`/tickets/${t.id}`}>{t.title}</Link>
                </td>
                <td>{t.category}</td>
                <td>
                  <PriorityBadge priority={t.priority} />
                </td>
                <td>
                  <StatusBadge status={t.status} />
                </td>
                <td>{t.assignee?.full_name ?? "Unassigned"}</td>
                <td>{new Date(t.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {tickets.length === 0 && (
              <tr>
                <td colSpan={7} className="empty-row">
                  No tickets match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
