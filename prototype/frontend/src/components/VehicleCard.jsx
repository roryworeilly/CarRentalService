import { Link } from 'react-router-dom';

export default function VehicleCard({ vehicle, qs }) {
  const to = `/vehicles/${vehicle.id}${qs ? `?${qs}` : ''}`;
  return (
    <Link to={to} className="card vehicle-card">
      {vehicle.imageUrl ? (
        <img src={vehicle.imageUrl} alt={`${vehicle.make} ${vehicle.model}`} />
      ) : (
        <div className="img-placeholder">No image</div>
      )}
      <div className="card-body">
        <h3>{vehicle.make} {vehicle.model}</h3>
        <div className="muted">
          {vehicle.year} &middot; {vehicle.category} &middot; {vehicle.seats} seats
        </div>
        <div className="price">${vehicle.dailyRate}/day</div>
      </div>
    </Link>
  );
}
