import { useEffect, useState } from 'react';
import { api } from '../../api.js';

// F.R 5.2 / UC-20: fleet management — add vehicles, change status.
const STATUSES = ['AVAILABLE', 'RENTED', 'IN_MAINTENANCE', 'RETIRED'];

const emptyForm = {
  vin: '',
  make: '',
  model: '',
  year: new Date().getFullYear(),
  seats: 5,
  category_id: '',
  home_location_id: '',
  status: 'AVAILABLE',
};

export default function AdminFleet() {
  const [vehicles, setVehicles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [patchingId, setPatchingId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [v, c, l] = await Promise.all([
        api.get('/admin/vehicles'),
        api.get('/admin/categories'),
        api.get('/locations'),
      ]);
      setVehicles(Array.isArray(v) ? v : []);
      setCategories(Array.isArray(c) ? c : []);
      setLocations(Array.isArray(l) ? l : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const changeStatus = async (id, status) => {
    setPatchingId(id);
    setErr(null);
    try {
      const updated = await api.patch(`/admin/vehicles/${id}`, { status });
      setVehicles((vs) => vs.map((v) => (v.id === id ? updated : v)));
    } catch (e) {
      setErr(e.message);
    } finally {
      setPatchingId(null);
    }
  };

  const onFormChange = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submitForm = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    try {
      const payload = {
        ...form,
        year: Number(form.year),
        seats: Number(form.seats),
        category_id: Number(form.category_id),
        home_location_id: Number(form.home_location_id),
      };
      await api.post('/admin/vehicles', payload);
      setForm(emptyForm);
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
        <h2>Fleet</h2>
        <button
          className="primary"
          onClick={() => setShowForm((s) => !s)}
        >
          {showForm ? 'Cancel' : 'Add vehicle'}
        </button>
      </div>

      {err && <div className="error">{err}</div>}

      {showForm && (
        <form className="card admin-form" onSubmit={submitForm}>
          <div className="admin-form-grid">
            <label>VIN
              <input
                required
                value={form.vin}
                onChange={(e) => onFormChange('vin', e.target.value)}
              />
            </label>
            <label>Make
              <input
                required
                value={form.make}
                onChange={(e) => onFormChange('make', e.target.value)}
              />
            </label>
            <label>Model
              <input
                required
                value={form.model}
                onChange={(e) => onFormChange('model', e.target.value)}
              />
            </label>
            <label>Year
              <input
                type="number"
                required
                value={form.year}
                onChange={(e) => onFormChange('year', e.target.value)}
              />
            </label>
            <label>Seats
              <input
                type="number"
                required
                value={form.seats}
                onChange={(e) => onFormChange('seats', e.target.value)}
              />
            </label>
            <label>Category
              <select
                required
                value={form.category_id}
                onChange={(e) => onFormChange('category_id', e.target.value)}
              >
                <option value="">Select…</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </label>
            <label>Location
              <select
                required
                value={form.home_location_id}
                onChange={(e) => onFormChange('home_location_id', e.target.value)}
              >
                <option value="">Select…</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </label>
            <label>Status
              <select
                value={form.status}
                onChange={(e) => onFormChange('status', e.target.value)}
              >
                {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
          </div>
          <button className="primary" disabled={saving}>
            {saving ? 'Saving…' : 'Create vehicle'}
          </button>
        </form>
      )}

      <div className="card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>VIN</th>
              <th>Vehicle</th>
              <th>Year</th>
              <th>Seats</th>
              <th>Category</th>
              <th>Location</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map((v) => (
              <tr key={v.id}>
                <td className="ref">{v.vin}</td>
                <td>{v.make} {v.model}</td>
                <td>{v.year}</td>
                <td>{v.seats}</td>
                <td>{v.category?.name || '—'}</td>
                <td>{v.location?.name || v.location?.code || '—'}</td>
                <td>
                  <select
                    value={v.status}
                    disabled={patchingId === v.id}
                    onChange={(e) => changeStatus(v.id, e.target.value)}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
            {vehicles.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">No vehicles in fleet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
