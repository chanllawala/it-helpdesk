import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">IT Helpdesk</div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/tickets">Tickets</NavLink>
          <NavLink to="/tickets/new">New Ticket</NavLink>
        </nav>
        <div className="user-menu">
          <span>
            {user?.full_name} <span className="role-badge">{user?.role}</span>
          </span>
          <button onClick={handleLogout}>Log out</button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
