import { useEffect, useState } from "react";
import * as api from "../api/client";
import type { DashboardStats } from "../api/types";
import { PriorityBadge, StatusBadge } from "../components/Badges";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDashboardStats()
      .then(setStats)
      .catch(() => setError("Failed to load dashboard stats"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!stats) return <div className="page-loading">Loading…</div>;

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_tickets}</div>
          <div className="stat-label">Total tickets</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.open_tickets}</div>
          <div className="stat-label">Open</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.unassigned_tickets}</div>
          <div className="stat-label">Unassigned</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {stats.average_resolution_hours !== null ? `${stats.average_resolution_hours}h` : "—"}
          </div>
          <div className="stat-label">Avg. resolution time</div>
        </div>
      </div>

      <div className="breakdown-grid">
        <section className="panel">
          <h2>Tickets by status</h2>
          <ul className="breakdown-list">
            {stats.by_status.map((row) => (
              <li key={row.status}>
                <StatusBadge status={row.status} />
                <span>{row.count}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="panel">
          <h2>Tickets by priority</h2>
          <ul className="breakdown-list">
            {stats.by_priority.map((row) => (
              <li key={row.priority}>
                <PriorityBadge priority={row.priority} />
                <span>{row.count}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
