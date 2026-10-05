import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth.jsx';

// F.R 1.4 / F.R 5.x: only ADMIN users can reach /admin/* routes.
// Non-admins (customers or anonymous) are redirected home with a notice.
export default function AdminRoute() {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (user.role !== 'ADMIN') {
    return (
      <Navigate
        to="/search?notice=Admin%20area%20is%20restricted."
        replace
      />
    );
  }
  return <Outlet />;
}
