import { Link } from 'react-router-dom';

const CATEGORY_IMAGE = {
  Economy: 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=640&q=70',
  Sedan:   'https://images.unsplash.com/photo-1550355291-bbee04a92027?auto=format&fit=crop&w=640&q=70',
  SUV:     'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=640&q=70',
  Truck:   'https://images.unsplash.com/photo-1595758228888-98f61b8d1b73?auto=format&fit=crop&w=640&q=70',
};

function imageFor(vehicle) {
  const category = vehicle.category_name || vehicle.category;
  return (
    vehicle.image_url ||
    vehicle.imageUrl ||
    CATEGORY_IMAGE[category] ||
    `https://placehold.co/640x360/1f2937/e5e7eb?text=${encodeURIComponent(category || 'Vehicle')}`
  );
}

export default function VehicleCard({ vehicle, qs }) {
  const to = `/vehicles/${vehicle.id}${qs ? `?${qs}` : ''}`;
  const category = vehicle.category_name || vehicle.category;
  const dailyRate = vehicle.daily_rate ?? vehicle.dailyRate;
  return (
    <Link to={to} className="card vehicle-card">
      <img
        src={imageFor(vehicle)}
        alt={`${vehicle.make} ${vehicle.model}`}
        onError={(e) => {
          e.currentTarget.src = `https://placehold.co/640x360/1f2937/e5e7eb?text=${encodeURIComponent(category || 'Vehicle')}`;
        }}
      />
      <div className="card-body">
        <h3>{vehicle.make} {vehicle.model}</h3>
        <div className="muted">
          {vehicle.year} &middot; {category} &middot; {vehicle.seats} seats
        </div>
        <div className="price">${dailyRate}/day</div>
      </div>
    </Link>
  );
}
