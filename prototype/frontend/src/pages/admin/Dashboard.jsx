import { useEffect, useState } from 'react';
import { api } from '../../api.js';

// F.R 5.1 / UC-19: admin dashboard — fleet snapshot and booking volume.
export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const d = await api.get('/admin/dashboard');
        setData(d);
      } catch (e) {
        setErr(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="muted">Loading…</div>;
  if (err) return <div className="error">{err}</div>;
  if (!data) return null;

  const counts = data.counts || {};
  const byStatus = data.bookings_by_status || {};

  const fmtMoney = (n) =>
    (n == null ? 0 : Number(n)).toLocaleString(undefined, {
      style: 'currency',
      currency: 'USD',
    });

  return (
    <div>
      <h2>Admin dashboard</h2>

      <div className="admin-tiles">
        <div className="admin-tile card">
          <div className="muted">Available</div>
          <div className="tile-num">{counts.available ?? 0}</div>
        </div>
        <div className="admin-tile card">
          <div className="muted">Rented</div>
          <div className="tile-num">{counts.rented ?? 0}</div>
        </div>
        <div className="admin-tile card">
          <div className="muted">In maintenance</div>
          <div className="tile-num">{counts.in_maintenance ?? 0}</div>
        </div>
        <div className="admin-tile card">
          <div className="muted">Retired</div>
          <div className="tile-num">{counts.retired ?? 0}</div>
        </div>
        <div className="admin-tile card">
          <div className="muted">Total fleet</div>
          <div className="tile-num">{counts.total ?? 0}</div>
        </div>
      </div>

      <div className="admin-twocol">
        <div className="card">
          <h3>Bookings by status</h3>
          <table className="admin-table">
            <tbody>
              {[
                'INPROGRESS',
                'CONFIRMED',
                'FAILED_PAYMENT',
                'EXPIRED',
                'CANCELLED',
                'COMPLETED',
              ].map((s) => (
                <tr key={s}>
                  <td>
                    <span className={`status status-${s}`}>{s}</span>
                  </td>
                  <td className="num">{byStatus[s] ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>Operations</h3>
          <div className="kv">
            <span className="muted">Revenue (last 30d)</span>
            <strong>{fmtMoney(data.revenue_30d)}</strong>
          </div>
          <div className="kv">
            <span className="muted">Upcoming pickups (next 7d)</span>
            <strong>{data.upcoming_pickups_7d ?? 0}</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
