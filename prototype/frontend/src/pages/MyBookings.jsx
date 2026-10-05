import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';

const fmt = (iso) =>
  iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '';

// Booking dates are picked as calendar days (UTC midnight), so show them in UTC.
const fmtDay = (iso) =>
  iso ? new Date(iso).toLocaleDateString(undefined, { dateStyle: 'medium', timeZone: 'UTC' }) : '';

function Hold({ expiresAt }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const rem = new Date(expiresAt).getTime() - now;
  if (rem <= 0) return <span>Hold expired</span>;
  const m = Math.floor(rem / 60000);
  const s = Math.floor((rem % 60000) / 1000);
  return <span>Hold expires in {m}:{String(s).padStart(2, '0')} (at {fmt(expiresAt)})</span>;
}

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [vehicles, setVehicles] = useState({}); // id -> vehicle | null (cached)
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

  // Fetch vehicle make/model once per id; tolerate errors (F.R 3.4).
  useEffect(() => {
    const ids = [...new Set(bookings.map((b) => b.vehicle_id))].filter(
      (id) => id != null && !(id in vehicles)
    );
    if (!ids.length) return;
    ids.forEach((id) => {
      api.get(`/vehicles/${id}`)
        .then((v) => setVehicles((c) => ({ ...c, [id]: v })))
        .catch(() => setVehicles((c) => ({ ...c, [id]: null })));
    });
    setVehicles((c) => ids.reduce((a, id) => ({ ...a, [id]: a[id] ?? undefined }), { ...c }));
  }, [bookings]); // eslint-disable-line react-hooks/exhaustive-deps

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
  if (err) {
    const staff = /forbidden/i.test(err);
    return <div className="error">{staff ? 'My Bookings is for customer accounts. Admins can review bookings under Admin → Bookings.' : err}</div>;
  }

  return (
    <div>
      <h2>My bookings</h2>
      {bookings.length === 0 && <div className="muted">You have no bookings yet.</div>}
      <div className="list">
        {bookings.map((b) => {
          const v = vehicles[b.vehicle_id];
          const payable = ['INPROGRESS', 'FAILED_PAYMENT'].includes(b.status);
          return (
            <div className="card booking-row" key={b.id}>
              <div>
                <div className="ref">{b.reference || b.id}</div>
                <div className="muted">
                  {v ? `${v.make} ${v.model}` : 'Vehicle'} · {fmtDay(b.period_start)} → {fmtDay(b.period_end)}
                </div>
                {b.quote_total != null && <div>Total: ${b.quote_total}</div>}
                {b.status === 'FAILED_PAYMENT' && b.hold_expires_at && (
                  <div className="muted"><Hold expiresAt={b.hold_expires_at} /></div>
                )}
              </div>
              <div className={`status status-${b.status}`}>{b.status}</div>
              <div>
                {payable && (
                  <Link className="link-btn" to={`/checkout/${b.id}`}>
                    {b.status === 'FAILED_PAYMENT' ? 'Retry payment' : 'Pay now'}
                  </Link>
                )}{' '}
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
          );
        })}
      </div>
    </div>
  );
}
