import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api, ApiError } from '../api.js';

// F.R 3.2 cost snapshot: quote is pulled from POST /bookings/quote.
export default function VehicleDetail() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  // Param names match Search.jsx links.
  const pickupDate = params.get('period_start');
  const returnDate = params.get('period_end');
  const pickupLocationId = params.get('location_id');
  const returnLocationId = params.get('location_id'); // same for prototype
  const hasDates = Boolean(pickupDate && returnDate);

  const [vehicle, setVehicle] = useState(null);
  const [quote, setQuote] = useState(null);
  const [err, setErr] = useState(null);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const v = await api.get(`/vehicles/${id}`);
        setVehicle(v);
        if (pickupDate && returnDate) {
          const q = await api.post('/bookings/quote', {
            vehicle_id: v.id,
            period_start: new Date(pickupDate).toISOString(),
            period_end: new Date(returnDate).toISOString(),
          });
          setQuote(q);
        }
      } catch (e) {
        setErr(e.message);
      }
    })();
  }, [id, pickupDate, returnDate]);

  const reserve = async () => {
    setBooking(true);
    setErr(null);
    try {
      const b = await api.post('/bookings', {
        vehicle_id: vehicle.id,
        period_start: new Date(pickupDate).toISOString(),
        period_end: new Date(returnDate).toISOString(),
        pickup_location_id: Number(pickupLocationId),
        return_location_id: Number(returnLocationId),
      });
      navigate(`/checkout/${b.id}`, { state: { booking: b } });
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        const qp = new URLSearchParams({
          period_start: pickupDate || '',
          period_end: returnDate || '',
          location_id: pickupLocationId || '',
          notice: 'This vehicle was just booked — please pick another date or vehicle.',
        });
        navigate(`/search?${qp.toString()}`, { replace: true });
        return;
      }
      setErr(e.message);
    } finally {
      setBooking(false);
    }
  };

  if (err) return <div className="error">{err}</div>;
  if (!vehicle) return <div className="muted">Loading vehicle…</div>;

  return (
    <div className="detail">
      <div className="card detail-main">
        <div>
          <h2>{vehicle.make} {vehicle.model}</h2>
          <div className="muted">{vehicle.year} · {vehicle.category_name} · {vehicle.seats} seats</div>
          <div className="price">${vehicle.daily_rate}/day</div>
        </div>
      </div>

      <div className="card">
        <h3>Quote</h3>
        {!hasDates ? (
          <div className="warn">
            Choose pickup and return dates to see a quote. <Link to="/search">Back to search</Link>
          </div>
        ) : quote ? (
          <table className="quote">
            <tbody>
              <tr><td>Daily rate</td><td>${quote.daily_rate}</td></tr>
              <tr><td>Days</td><td>{quote.days}</td></tr>
              <tr><td>Flat fee</td><td>${quote.flat_fee}</td></tr>
              {Number(quote.discount_pct) > 0 && (
                <tr><td>Subscription discount</td><td>-{quote.discount_pct}%</td></tr>
              )}
              <tr><td>Subtotal</td><td>${quote.subtotal}</td></tr>
              <tr className="total"><td>Total</td><td>${quote.total}</td></tr>
            </tbody>
          </table>
        ) : (
          <div className="muted">Calculating…</div>
        )}
        {hasDates && !pickupLocationId && (
          <div className="warn">Select a pickup location on the search page to reserve. <Link to="/search">Back to search</Link></div>
        )}
        <button className="primary" disabled={!quote || booking || !pickupLocationId} onClick={reserve}>
          {booking ? 'Reserving…' : 'Reserve'}
        </button>
      </div>
    </div>
  );
}
