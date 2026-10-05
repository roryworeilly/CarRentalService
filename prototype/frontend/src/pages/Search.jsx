import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import VehicleCard from '../components/VehicleCard.jsx';

// F.R 2.4: only AVAILABLE + non-overlapping vehicles are returned by the backend.
const LOCATIONS = [
  { id: '1', name: 'Downtown — Pittsburgh' },
  { id: '2', name: 'Airport — PIT' },
  { id: '3', name: 'Oakland Campus' },
];
const CATEGORIES = ['', 'ECONOMY', 'COMPACT', 'SUV', 'LUXURY', 'VAN'];

function todayISO(offset = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}

export default function Search() {
  const [params, setParams] = useSearchParams();
  const [pickupDate, setPickupDate] = useState(params.get('pickupDate') || todayISO(1));
  const [returnDate, setReturnDate] = useState(params.get('returnDate') || todayISO(4));
  const [locationId, setLocationId] = useState(params.get('locationId') || LOCATIONS[0].id);
  const [category, setCategory] = useState(params.get('category') || '');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [notice, setNotice] = useState(params.get('notice'));

  const buildQS = () => {
    const qp = new URLSearchParams({ pickupDate, returnDate, locationId });
    if (category) qp.set('category', category);
    return qp.toString();
  };

  const runSearch = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const qs = buildQS();
      setParams(qs);
      const data = await api.get(`/vehicles?${qs}`);
      setResults(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { runSearch(); /* eslint-disable-next-line */ }, []);

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
          <select value={locationId} onChange={(e) => setLocationId(e.target.value)}>
            {LOCATIONS.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
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
