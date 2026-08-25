export type UserRole = "admin" | "agent" | "user";
export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: string;
}

export interface Comment {
  id: number;
  ticket_id: number;
  body: string;
  created_at: string;
  author: User;
}

export interface TicketListItem {
  id: number;
  title: string;
  category: string;
  priority: TicketPriority;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  creator: User;
  assignee: User | null;
}

export interface Ticket extends TicketListItem {
  description: string;
  resolved_at: string | null;
  closed_at: string | null;
}

export interface DashboardStats {
  total_tickets: number;
  by_status: { status: TicketStatus; count: number }[];
  by_priority: { priority: TicketPriority; count: number }[];
  average_resolution_hours: number | null;
  open_tickets: number;
  unassigned_tickets: number;
}

export interface TicketFilters {
  status_filter?: TicketStatus;
  priority?: TicketPriority;
  assigned_to_id?: number;
  search?: string;
  date_from?: string;
  date_to?: string;
}
