import { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../auth.jsx';

// F.R 1.1: must be 21+ with valid driver's licence. Client checks are warnings only;
// the server is the source of truth.
function yearsBetween(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - d.getFullYear();
  const m = now.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age--;
  return age;
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    phone: '',
    licenceNumber: '',
    issuingState: '',
    expiresOn: '',
  });
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const upd = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const age = useMemo(() => yearsBetween(form.dateOfBirth), [form.dateOfBirth]);
  const licenceExpired = useMemo(() => {
    if (!form.expiresOn) return false;
    return new Date(form.expiresOn) < new Date();
  }, [form.expiresOn]);

  const warnings = [];
  if (age !== null && age < 21) warnings.push(`You appear to be ${age}. Customers must be 21+.`);
  if (licenceExpired) warnings.push('Your driver licence appears to be expired.');

  const submit = async (e) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await register({
        email: form.email,
        password: form.password,
        firstName: form.firstName,
        lastName: form.lastName,
        dateOfBirth: form.dateOfBirth,
        phone: form.phone,
        licence: {
          number: form.licenceNumber,
          issuingState: form.issuingState,
          expiresOn: form.expiresOn,
        },
      });
      navigate('/search', { replace: true });
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-card card wide">
      <h2>Create account</h2>
      <form onSubmit={submit}>
        <div className="row">
          <label>First name
            <input value={form.firstName} onChange={upd('firstName')} required />
          </label>
          <label>Last name
            <input value={form.lastName} onChange={upd('lastName')} required />
          </label>
        </div>
        <label>Email
          <input type="email" value={form.email} onChange={upd('email')} required />
        </label>
        <label>Password
          <input type="password" value={form.password} onChange={upd('password')} required minLength={8} />
        </label>
        <div className="row">
          <label>Date of birth
            <input type="date" value={form.dateOfBirth} onChange={upd('dateOfBirth')} required />
          </label>
          <label>Phone
            <input value={form.phone} onChange={upd('phone')} required />
          </label>
        </div>
        <fieldset>
          <legend>Driver's licence</legend>
          <div className="row">
            <label>Number
              <input value={form.licenceNumber} onChange={upd('licenceNumber')} required />
            </label>
            <label>Issuing state
              <input value={form.issuingState} onChange={upd('issuingState')} required maxLength={2} />
            </label>
            <label>Expires on
              <input type="date" value={form.expiresOn} onChange={upd('expiresOn')} required />
            </label>
          </div>
        </fieldset>

        {warnings.length > 0 && (
          <div className="warn">
            {warnings.map((w, i) => <div key={i}>{w}</div>)}
            <div className="muted">You can still submit; the server will make the final decision.</div>
          </div>
        )}
        {err && <div className="error">{err}</div>}
        <button className="primary" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
      </form>
      <p className="muted">Already have an account? <Link to="/login">Log in</Link></p>
    </div>
  );
}
