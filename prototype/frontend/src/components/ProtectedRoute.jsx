import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth.jsx';

// F.R 1.4: only authenticated customers can reach booking pages.
export default function ProtectedRoute({ children }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}
