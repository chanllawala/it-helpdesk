import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/client";
import { ApiError } from "../api/client";
import type { TicketPriority } from "../api/types";

export default function CreateTicket() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("general");
  const [priority, setPriority] = useState<TicketPriority>("medium");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const ticket = await api.createTicket({ title, description, category, priority });
      navigate(`/tickets/${ticket.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create ticket");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="form-page">
      <h1>New Ticket</h1>
      <form className="panel form" onSubmit={handleSubmit}>
        {error && <div className="error-banner">{error}</div>}
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={6}
            required
          />
        </label>
        <div className="form-row">
          <label>
            Category
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="general">General</option>
              <option value="Network">Network</option>
              <option value="Hardware">Hardware</option>
              <option value="Software">Software</option>
              <option value="Access">Access</option>
            </select>
          </label>
          <label>
            Priority
            <select value={priority} onChange={(e) => setPriority(e.target.value as TicketPriority)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </label>
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? "Creating…" : "Create Ticket"}
        </button>
      </form>
    </div>
  );
}
