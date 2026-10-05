import { useEffect, useState } from 'react';
import { api } from '../../api.js';

// F.R 5.3 / UC-21: category rate management. Rates are snapshotted on bookings
// (quote_* columns), so edits here never alter existing bookings.
export default function AdminCategories() {
  const [cats, setCats] = useState([]);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [edits, setEdits] = useState({}); // id -> {daily_rate, flat_fee}
  const [savingId, setSavingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', daily_rate: '', flat_fee: '' });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get('/admin/categories');
      setCats(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const startEdit = (c) => {
    setEdits((e) => ({
      ...e,
      [c.id]: { daily_rate: c.daily_rate, flat_fee: c.flat_fee },
    }));
  };

  const cancelEdit = (id) => {
    setEdits((e) => {
      const copy = { ...e };
      delete copy[id];
      return copy;
    });
  };

  const changeEdit = (id, k, v) =>
    setEdits((e) => ({ ...e, [id]: { ...e[id], [k]: v } }));

  const saveEdit = async (id) => {
    setSavingId(id);
    setErr(null);
    try {
      const body = {
        daily_rate: Number(edits[id].daily_rate),
        flat_fee: Number(edits[id].flat_fee),
      };
      const updated = await api.patch(`/admin/categories/${id}`, body);
      setCats((cs) => cs.map((c) => (c.id === id ? updated : c)));
      cancelEdit(id);
    } catch (e) {
      setErr(e.message);
    } finally {
      setSavingId(null);
    }
  };

  const submitNew = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    try {
      await api.post('/admin/categories', {
        name: form.name,
        daily_rate: Number(form.daily_rate),
        flat_fee: Number(form.flat_fee),
      });
      setForm({ name: '', daily_rate: '', flat_fee: '' });
      setShowForm(false);
      await load();
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="muted">Loading…</div>;

  return (
    <div>
      <div className="admin-header">
        <h2>Categories</h2>
        <button className="primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : 'Add category'}
        </button>
      </div>

      <div className="warn">
        Rate changes do not affect existing bookings (snapshotted at booking time).
      </div>

      {err && <div className="error">{err}</div>}

      {showForm && (
        <form className="card admin-form" onSubmit={submitNew}>
          <div className="admin-form-grid">
            <label>Name
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>
            <label>Daily rate
              <input
                type="number" step="0.01" required
                value={form.daily_rate}
                onChange={(e) => setForm({ ...form, daily_rate: e.target.value })}
              />
            </label>
            <label>Flat fee
              <input
                type="number" step="0.01" required
                value={form.flat_fee}
                onChange={(e) => setForm({ ...form, flat_fee: e.target.value })}
              />
            </label>
          </div>
          <button className="primary" disabled={saving}>
            {saving ? 'Saving…' : 'Create category'}
          </button>
        </form>
      )}

      <div className="card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Daily rate</th>
              <th>Flat fee</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cats.map((c) => {
              const editing = edits[c.id] != null;
              return (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>
                    {editing ? (
                      <input
                        type="number" step="0.01"
                        value={edits[c.id].daily_rate}
                        onChange={(e) => changeEdit(c.id, 'daily_rate', e.target.value)}
                      />
                    ) : (
                      `$${Number(c.daily_rate).toFixed(2)}`
                    )}
                  </td>
                  <td>
                    {editing ? (
                      <input
                        type="number" step="0.01"
                        value={edits[c.id].flat_fee}
                        onChange={(e) => changeEdit(c.id, 'flat_fee', e.target.value)}
                      />
                    ) : (
                      `$${Number(c.flat_fee).toFixed(2)}`
                    )}
                  </td>
                  <td>
                    {editing ? (
                      <>
                        <button
                          className="link-btn"
                          disabled={savingId === c.id}
                          onClick={() => saveEdit(c.id)}
                        >
                          {savingId === c.id ? 'Saving…' : 'Save'}
                        </button>
                        {' · '}
                        <button
                          className="link-btn"
                          onClick={() => cancelEdit(c.id)}
                        >Cancel</button>
                      </>
                    ) : (
                      <button className="link-btn" onClick={() => startEdit(c)}>
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
            {cats.length === 0 && (
              <tr><td colSpan={4} className="muted">No categories yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
