import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth.jsx';
import NavBar from './components/NavBar.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Search from './pages/Search.jsx';
import VehicleDetail from './pages/VehicleDetail.jsx';
import Checkout from './pages/Checkout.jsx';
import MyBookings from './pages/MyBookings.jsx';
import NotFound from './pages/NotFound.jsx';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <NavBar />
        <main className="container">
          <Routes>
            <Route path="/" element={<Navigate to="/search" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/search" element={<Search />} />
            <Route
              path="/vehicles/:id"
              element={
                <ProtectedRoute>
                  <VehicleDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/checkout/:bookingId"
              element={
                <ProtectedRoute>
                  <Checkout />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bookings"
              element={
                <ProtectedRoute>
                  <MyBookings />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  );
}
