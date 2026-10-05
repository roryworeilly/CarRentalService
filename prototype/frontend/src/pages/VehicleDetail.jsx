import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../api.js';

// F.R 3.2 cost snapshot: quote is pulled from POST /bookings/quote.
export default function VehicleDetail() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const pickupDate = params.get('pickupDate');
  const returnDate = params.get('returnDate');
  const pickupLocationId = params.get('locationId');
  const returnLocationId = params.get('locationId'); // same for prototype

  const [vehicle, setVehicle] = useState(null);
  const [quote, setQuote] = useState(null);
  const [err, setErr] = useState(null);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // reuse the search endpoint — simplest since there is no GET /vehicles/{id} spec
        const list = await api.get(`/vehicles?pickupDate=${pickupDate}&returnDate=${returnDate}&locationId=${pickupLocationId}`);
        const v = (Array.isArray(list) ? list : []).find((x) => String(x.id) === String(id));
        setVehicle(v || null);
        if (v && pickupDate && returnDate) {
          const q = await api.post('/bookings/quote', {
            vehicleId: v.id,
            pickupDate,
            returnDate,
            pickupLocationId,
            returnLocationId,
          });
          setQuote(q);
        }
      } catch (e) {
        setErr(e.message);
      }
    })();
  }, [id, pickupDate, returnDate, pickupLocationId, returnLocationId]);

  const reserve = async () => {
    setBooking(true);
    setErr(null);
    try {
      const b = await api.post('/bookings', {
        vehicleId: vehicle.id,
        pickupDate,
        returnDate,
        pickupLocationId,
        returnLocationId,
      });
      navigate(`/checkout/${b.id}`, { state: { booking: b } });
    } catch (e) {
      // 409 = double-book; bounce back to Search with a notice.
      if (e instanceof ApiError && e.status === 409) {
        const qp = new URLSearchParams({
          pickupDate: pickupDate || '',
          returnDate: returnDate || '',
          locationId: pickupLocationId || '',
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
        {vehicle.imageUrl && <img src={vehicle.imageUrl} alt="" />}
        <div>
          <h2>{vehicle.make} {vehicle.model}</h2>
          <div className="muted">{vehicle.year} · {vehicle.category} · {vehicle.seats} seats</div>
          <div className="price">${vehicle.dailyRate}/day</div>
        </div>
      </div>

      <div className="card">
        <h3>Quote</h3>
        {quote ? (
          <table className="quote">
            <tbody>
              <tr><td>Daily rate</td><td>${quote.dailyRate}</td></tr>
              <tr><td>Days</td><td>{quote.days}</td></tr>
              <tr><td>Flat fee</td><td>${quote.flatFee}</td></tr>
              {quote.discountPct > 0 && (
                <tr><td>Subscription discount</td><td>-{quote.discountPct}%</td></tr>
              )}
              <tr><td>Subtotal</td><td>${quote.subtotal}</td></tr>
              <tr className="total"><td>Total</td><td>${quote.total}</td></tr>
            </tbody>
          </table>
        ) : (
          <div className="muted">Calculating…</div>
        )}
        <button className="primary" disabled={!quote || booking} onClick={reserve}>
          {booking ? 'Reserving…' : 'Reserve'}
        </button>
      </div>
    </div>
  );
}
