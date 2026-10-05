import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth.jsx';

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link to="/search" className="brand">DriveAway</Link>
        <nav className="nav-links">
          <Link to="/search">Search</Link>
          {user && user.role !== 'ADMIN' && <Link to="/bookings">My Bookings</Link>}
          {user?.role === 'ADMIN' && (
            <div className="admin-menu">
              <button type="button" className="link-btn admin-menu-btn">Admin ▾</button>
              <div className="admin-menu-items">
                <Link to="/admin">Dashboard</Link>
                <Link to="/admin/fleet">Fleet</Link>
                <Link to="/admin/categories">Categories</Link>
                <Link to="/admin/bookings">Bookings</Link>
              </div>
            </div>
          )}
          {user ? (
            <>
              <span className="muted">{user.firstName || user.email}</span>
              <button className="link-btn" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
