import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="card">
      <h2>Not found</h2>
      <p className="muted">That page does not exist.</p>
      <Link to="/search">Back to search</Link>
    </div>
  );
}
