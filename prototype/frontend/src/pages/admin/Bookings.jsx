import { useEffect, useState } from 'react';
import { api } from '../../api.js';

// F.R 5.4 / UC-22: admin bookings view with status override capability.
const STATUSES = [
  'INPROGRESS',
  'CONFIRMED',
  'FAILED_PAYMENT',
  'EXPIRED',
  'CANCELLED',
  'COMPLETED',
];

export default function AdminBookings() {
  const [filters, setFilters] = useState({
    status: '',
    customer_email: '',
    vehicle_id: '',
    from: '',
    to: '',
  });
  const [bookings, setBookings] = useState([]);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);
  const [overrideFor, setOverrideFor] = useState(null); // booking object
  const [newStatus, setNewStatus] = useState('CONFIRMED');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const qp = new URLSearchParams();
      Object.entries(filters).forEach(([k, v]) => {
        if (v) qp.set(k, v);
      });
      const qs = qp.toString();
      const data = await api.get(`/admin/bookings${qs ? `?${qs}` : ''}`);
      setBookings(Array.isArray(data) ? data : []);
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line
  }, []);

  const openOverride = (b) => {
    setOverrideFor(b);
    setNewStatus(b.status);
    setReason('');
  };

  const submitOverride = async (e) => {
    e.preventDefault();
    if (!overrideFor) return;
    setSubmitting(true);
    setErr(null);
    try {
      await api.post(`/admin/bookings/${overrideFor.id}/override-status`, {
        status: newStatus,
        reason,
      });
      setOverrideFor(null);
      await load();
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setSubmitting(false);
    }
  };

  const fmtDate = (iso) =>
    iso ? new Date(iso).toLocaleDateString(undefined, { dateStyle: 'medium', timeZone: 'UTC' }) : '—';
  const fmtMoney = (n) =>
    (n == null ? 0 : Number(n)).toLocaleString(undefined, {
      style: 'currency',
      currency: 'USD',
    });

  return (
    <div>
      <h2>Bookings</h2>

      <form className="card admin-filters" onSubmit={load}>
        <label>Status
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">Any</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>Customer email
          <input
            value={filters.customer_email}
            onChange={(e) => setFilters({ ...filters, customer_email: e.target.value })}
          />
        </label>
        <label>Vehicle id
          <input
            value={filters.vehicle_id}
            onChange={(e) => setFilters({ ...filters, vehicle_id: e.target.value })}
          />
        </label>
        <label>From
          <input
            type="date"
            value={filters.from}
            onChange={(e) => setFilters({ ...filters, from: e.target.value })}
          />
        </label>
        <label>To
          <input
            type="date"
            value={filters.to}
            onChange={(e) => setFilters({ ...filters, to: e.target.value })}
          />
        </label>
        <button className="primary" disabled={loading}>
          {loading ? 'Loading…' : 'Filter'}
        </button>
      </form>

      {err && <div className="error">{err}</div>}

      <div className="card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Ref</th>
              <th>Customer</th>
              <th>Vehicle</th>
              <th>Dates</th>
              <th>Status</th>
              <th>Total</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.id}>
                <td className="ref">{b.reference || b.id}</td>
                <td>{b.customer_email || '—'}</td>
                <td>
                  {b.vehicle_label || '—'}
                </td>
                <td>
                  {fmtDate(b.period_start)} → {fmtDate(b.period_end)}
                </td>
                <td>
                  <span className={`status status-${b.status}`}>{b.status}</span>
                </td>
                <td>{fmtMoney(b.quote_total ?? b.quoteTotal)}</td>
                <td>
                  <button className="link-btn" onClick={() => openOverride(b)}>
                    Override status
                  </button>
                </td>
              </tr>
            ))}
            {bookings.length === 0 && !loading && (
              <tr>
                <td colSpan={7} className="muted">No bookings match those filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {overrideFor && (
        <div className="modal-backdrop" onClick={() => setOverrideFor(null)}>
          <div className="modal card" onClick={(e) => e.stopPropagation()}>
            <h3>Override booking status</h3>
            <div className="muted">
              {overrideFor.reference || overrideFor.id}
            </div>
            <form onSubmit={submitOverride}>
              <label>New status
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                >
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
              <label>Reason
                <textarea
                  required
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <div className="modal-actions">
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => setOverrideFor(null)}
                >Cancel</button>
                <button className="primary" disabled={submitting}>
                  {submitting ? 'Saving…' : 'Apply override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
