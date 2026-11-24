import { useEffect, useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';
import { formatMoney } from '../../utils/format.js';
import ActivityForm from './ActivityForm.jsx';

export default function ActivityItem({ activity }) {
  const { trip, updateActivity, deleteActivity } = useTrip();
  const [editing, setEditing] = useState(false);
  const [actual, setActual] = useState(activity.actual_cost ?? '');
  const [error, setError] = useState('');

  useEffect(() => {
    setActual(activity.actual_cost ?? '');
  }, [activity.actual_cost]);

  const destination = trip.destinations.find((d) => d.id === activity.destination_id);

  const saveActual = async () => {
    const stored = activity.actual_cost ?? '';
    if (String(actual) === String(stored)) return;
    setError('');
    try {
      await updateActivity(activity.id, { actual_cost: actual === '' ? null : Number(actual) });
    } catch (e) {
      setError(e.message);
      setActual(stored);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete "${activity.title}"?`)) return;
    setError('');
    try {
      await deleteActivity(activity.id);
    } catch (e) {
      setError(e.message);
    }
  };

  if (editing) {
    return (
      <li className="activity editing">
        <ActivityForm activity={activity} onDone={() => setEditing(false)} onCancel={() => setEditing(false)} />
      </li>
    );
  }

  return (
    <li className="activity">
      <div className="activity-time">{activity.start_time ?? 'Anytime'}</div>
      <div className="activity-body">
        <div className="activity-title">{activity.title}</div>
        {destination && <span className="chip">{destination.name}</span>}
        {activity.notes && <p className="muted">{activity.notes}</p>}
        <div className="activity-costs">
          <span>Est. {formatMoney(activity.estimated_cost, trip.currency)}</span>
          <label className="actual">
            Actual
            <input
              type="number"
              min="0"
              step="0.01"
              value={actual}
              placeholder="-"
              onChange={(e) => setActual(e.target.value)}
              onBlur={saveActual}
            />
          </label>
        </div>
        {error && <p className="error-text">{error}</p>}
      </div>
      <div className="activity-actions">
        <button className="link" onClick={() => setEditing(true)}>
          Edit
        </button>
        <button className="link danger-text" onClick={remove}>
          Delete
        </button>
      </div>
    </li>
  );
}