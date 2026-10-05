import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import VehicleCard from '../components/VehicleCard.jsx';

// F.R 2.2/2.4: backend filters by exact VehicleCategory.name (case-sensitive); values match db/seed.sql.
// No categories endpoint exists, so the list is hardcoded.
const CATEGORIES = ['', 'Economy', 'Sedan', 'SUV', 'Truck'];

function todayISO(offset = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}

export default function Search() {
  const [params, setParams] = useSearchParams();
  const [locations, setLocations] = useState([]);
  const [pickupDate, setPickupDate] = useState(params.get('period_start') || todayISO(1));
  const [returnDate, setReturnDate] = useState(params.get('period_end') || todayISO(4));
  const [locationId, setLocationId] = useState(params.get('location_id') || '');
  const [category, setCategory] = useState(params.get('category') || '');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [notice, setNotice] = useState(params.get('notice'));

  const [ready, setReady] = useState(false);
  const [initialLoc, setInitialLoc] = useState(null);

  // Default to a real location (first from /locations) so search/quote/reserve work (F.R 2.3).
  useEffect(() => {
    api.get('/locations')
      .then((ls) => {
        const list = Array.isArray(ls) ? ls : [];
        setLocations(list);
        const chosen = params.get('location_id') || (list[0] ? String(list[0].id) : '');
        setLocationId(chosen);
        setInitialLoc(chosen);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setReady(true));
    // eslint-disable-next-line
  }, []);

  const buildQS = (loc = locationId) => {
    const qp = new URLSearchParams({ period_start: pickupDate, period_end: returnDate });
    if (loc) qp.set('location_id', loc);
    if (category) qp.set('category', category);
    return qp.toString();
  };

  const runSearch = async (e, loc = locationId) => {
    if (e && e.preventDefault) e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const qs = buildQS(loc);
      setParams(qs);
      const data = await api.get(`/vehicles?${qs}`);
      setResults(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (ready) runSearch(null, initialLoc || ''); /* eslint-disable-next-line */ }, [ready]);

  const qs = buildQS();

  return (
    <div>
      <h2>Find a vehicle</h2>
      {notice && <div className="warn" onClick={() => setNotice(null)}>{notice}</div>}
      <form className="search-form card" onSubmit={runSearch}>
        <label>Pickup
          <input type="date" value={pickupDate} onChange={(e) => setPickupDate(e.target.value)} required />
        </label>
        <label>Return
          <input type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} required />
        </label>
        <label>Location
          <select value={locationId} required onChange={(e) => setLocationId(e.target.value)}>
            {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </label>
        <label>Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c || 'Any'}</option>)}
          </select>
        </label>
        <button className="primary" disabled={loading}>{loading ? 'Searching…' : 'Search'}</button>
      </form>

      {err && <div className="error">{err}</div>}

      <div className="grid">
        {results.map((v) => <VehicleCard key={v.id} vehicle={v} qs={qs} />)}
        {!loading && results.length === 0 && <div className="muted">No vehicles available for those dates.</div>}
      </div>
    </div>
  );
}
