import type {
  Comment,
  DashboardStats,
  Ticket,
  TicketFilters,
  TicketListItem,
  TicketPriority,
  TicketStatus,
  User,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

let token: string | null = localStorage.getItem("helpdesk_token");

export function setToken(newToken: string | null) {
  token = newToken;
  if (newToken) {
    localStorage.setItem("helpdesk_token", newToken);
  } else {
    localStorage.removeItem("helpdesk_token");
  }
}

export function getToken() {
  return token;
}

class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const data = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: form,
  });
  setToken(data.access_token);
  return data;
}

export function register(email: string, full_name: string, password: string) {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, full_name, password }),
  });
}

export function getMe() {
  return request<User>("/auth/me");
}

export function listAgents() {
  return request<User[]>("/users/agents");
}

export function listTickets(filters: TicketFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const qs = params.toString();
  return request<TicketListItem[]>(`/tickets${qs ? `?${qs}` : ""}`);
}

export function getTicket(id: number) {
  return request<Ticket>(`/tickets/${id}`);
}

export function createTicket(payload: {
  title: string;
  description: string;
  category: string;
  priority: TicketPriority;
}) {
  return request<Ticket>("/tickets", { method: "POST", body: JSON.stringify(payload) });
}

export function assignTicket(id: number, assigned_to_id: number) {
  return request<Ticket>(`/tickets/${id}/assign`, {
    method: "POST",
    body: JSON.stringify({ assigned_to_id }),
  });
}

export function updateTicketStatus(id: number, status: TicketStatus) {
  return request<Ticket>(`/tickets/${id}/status`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export function listComments(ticketId: number) {
  return request<Comment[]>(`/tickets/${ticketId}/comments`);
}

export function addComment(ticketId: number, body: string) {
  return request<Comment>(`/tickets/${ticketId}/comments`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export function getDashboardStats() {
  return request<DashboardStats>("/dashboard/stats");
}

export { ApiError };
