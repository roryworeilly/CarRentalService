import { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get('/bookings');
      setBookings(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const cancel = async (id) => {
    if (!confirm('Cancel this booking? Refunds only issue from CONFIRMED bookings.')) return;
    setCancelling(id);
    try {
      await api.post(`/bookings/${id}/cancel`);
      await load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setCancelling(null);
    }
  };

  if (loading) return <div className="muted">Loading…</div>;
  if (err) return <div className="error">{err}</div>;

  return (
    <div>
      <h2>My bookings</h2>
      {bookings.length === 0 && <div className="muted">You have no bookings yet.</div>}
      <div className="list">
        {bookings.map((b) => (
          <div className="card booking-row" key={b.id}>
            <div>
              <div className="ref">{b.reference || b.id}</div>
              <div className="muted">
                {b.vehicle ? `${b.vehicle.make} ${b.vehicle.model}` : 'Vehicle'} ·{' '}
                {b.pickupDate} → {b.returnDate}
              </div>
            </div>
            <div className={`status status-${b.status}`}>{b.status}</div>
            <div>
              {['INPROGRESS', 'CONFIRMED'].includes(b.status) && (
                <button
                  className="link-btn"
                  disabled={cancelling === b.id}
                  onClick={() => cancel(b.id)}
                >
                  {cancelling === b.id ? 'Cancelling…' : 'Cancel'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
