import { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api.js';

// Mock card form. Test cards:
//   4242 4242 4242 4242 -> success
//   4000 0000 0000 0002 -> declines (FAILED_PAYMENT)
// On FAILED_PAYMENT we show a countdown to holdExpiresAt (15 min, F.R booking states).

function useCountdown(expiresAt) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!expiresAt) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [expiresAt]);
  if (!expiresAt) return null;
  const remaining = Math.max(0, new Date(expiresAt).getTime() - now);
  const mins = Math.floor(remaining / 60000);
  const secs = Math.floor((remaining % 60000) / 1000);
  return { remaining, label: `${mins}:${String(secs).padStart(2, '0')}` };
}

export default function Checkout() {
  const { bookingId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [booking, setBooking] = useState(location.state?.booking || null);
  const [card, setCard] = useState({ cardNumber: '4242424242424242', expMonth: '12', expYear: '2030', cvc: '123' });
  const [status, setStatus] = useState(null); // 'CONFIRMED' | 'FAILED_PAYMENT'
  const [holdExpiresAt, setHoldExpiresAt] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const countdown = useCountdown(holdExpiresAt);

  const upd = (k) => (e) => setCard({ ...card, [k]: e.target.value });

  const pay = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const res = await api.post(`/bookings/${bookingId}/pay`, {
        cardNumber: card.cardNumber.replace(/\s+/g, ''),
        expMonth: Number(card.expMonth),
        expYear: Number(card.expYear),
        cvc: card.cvc,
      });
      setStatus(res.status);
      setHoldExpiresAt(res.holdExpiresAt || null);
      if (res.status === 'CONFIRMED') {
        setTimeout(() => navigate('/bookings'), 1500);
      }
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const expired = countdown && countdown.remaining === 0;

  return (
    <div className="checkout">
      <h2>Checkout</h2>
      {booking && (
        <div className="card">
          <div className="muted">Booking reference</div>
          <div className="ref">{booking.reference || booking.id}</div>
          {booking.quote && (
            <div className="total">Total due: ${booking.quote.total}</div>
          )}
        </div>
      )}

      {status === 'CONFIRMED' ? (
        <div className="card success">
          <h3>Payment confirmed</h3>
          <p>Taking you to your bookings…</p>
        </div>
      ) : (
        <form className="card" onSubmit={pay}>
          <p className="muted">
            Test cards: <code>4242 4242 4242 4242</code> succeeds, <code>4000 0000 0000 0002</code> declines.
          </p>
          <label>Card number
            <input value={card.cardNumber} onChange={upd('cardNumber')} required />
          </label>
          <div className="row">
            <label>Exp month
              <input value={card.expMonth} onChange={upd('expMonth')} required maxLength={2} />
            </label>
            <label>Exp year
              <input value={card.expYear} onChange={upd('expYear')} required maxLength={4} />
            </label>
            <label>CVC
              <input value={card.cvc} onChange={upd('cvc')} required maxLength={4} />
            </label>
          </div>

          {status === 'FAILED_PAYMENT' && (
            <div className="warn">
              <strong>Payment failed.</strong>{' '}
              {holdExpiresAt && !expired && (
                <>Hold expires in <strong>{countdown.label}</strong>. You can retry below.</>
              )}
              {expired && <>The 15-minute hold has expired. Please start a new booking.</>}
            </div>
          )}

          {err && <div className="error">{err}</div>}

          <button className="primary" disabled={busy || expired}>
            {busy ? 'Processing…' : status === 'FAILED_PAYMENT' ? 'Retry payment' : 'Pay now'}
          </button>
        </form>
      )}
    </div>
  );
}
