import { useMemo, useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';
import { formatDate } from '../../utils/format.js';
import ActivityForm from './ActivityForm.jsx';
import ActivityItem from './ActivityItem.jsx';

export default function Timeline() {
  const { trip } = useTrip();
  const [adding, setAdding] = useState(false);

  // The server returns activities sorted by date then time; this only groups them for display.
  const days = useMemo(() => {
    const byDate = new Map();
    for (const activity of trip.activities) {
      if (!byDate.has(activity.date)) byDate.set(activity.date, []);
      byDate.get(activity.date).push(activity);
    }
    return [...byDate.entries()];
  }, [trip.activities]);

  return (
    <section className="card">
      <div className="card-head">
        <h2>Itinerary</h2>
        {!adding && (
          <button className="primary" onClick={() => setAdding(true)}>
            + Add activity
          </button>
        )}
      </div>

      {adding && <ActivityForm onDone={() => setAdding(false)} onCancel={() => setAdding(false)} />}

      {days.length === 0 ? (
        <p className="muted">
          No activities yet. Add one, or let the AI assistant draft an itinerary for you.
        </p>
      ) : (
        <ol className="timeline">
          {days.map(([date, activities]) => (
            <li key={date} className="day">
              <h3>{formatDate(date)}</h3>
              <ul>
                {activities.map((a) => (
                  <ActivityItem key={a.id} activity={a} />
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}