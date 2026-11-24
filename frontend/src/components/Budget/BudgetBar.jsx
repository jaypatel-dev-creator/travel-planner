import { useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';
import { formatMoney } from '../../utils/format.js';

const STATUS_LABEL = {
  no_budget: 'No budget set',
  on_track: 'On track',
  near_limit: 'Nearing limit',
  over_budget: 'Over budget',
};

export default function BudgetBar() {
  const { trip, updateTrip } = useTrip();
  const b = trip.budget; // every figure below is computed by the server
  const money = (n) => formatMoney(n, trip.currency);

  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const startEdit = () => {
    setValue(String(b.budget_total));
    setError('');
    setEditing(true);
  };

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await updateTrip({ budget_total: value === '' ? 0 : Number(value) });
      setEditing(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Display clamp only: the bar cannot draw past 100%, the real percentage is shown as text.
  const width = Math.min(b.percent_used, 100);

  return (
    <section className="budget" aria-label="Trip budget">
      <div className="budget-top">
        <strong>Trip Budget</strong>
        <span className={`pill ${b.status}`}>{STATUS_LABEL[b.status] ?? b.status}</span>
        <span className="muted">{b.percent_used}% of budget estimated</span>
      </div>

      <div
        className="bar"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={width}
      >
        <div className={`bar-fill ${b.status}`} style={{ width: `${width}%` }} />
      </div>

      <div className="budget-stats">
        <div>
          <span className="label">Estimated</span>
          <span>{money(b.total_estimated)}</span>
        </div>
        <div>
          <span className="label">Budget</span>
          {editing ? (
            <form className="inline-form" onSubmit={save}>
              <input
                type="number"
                min="0"
                step="0.01"
                autoFocus
                value={value}
                onChange={(e) => setValue(e.target.value)}
              />
              <button className="primary" disabled={saving}>
                Save
              </button>
              <button type="button" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </form>
          ) : (
            <span>
              {money(b.budget_total)}{' '}
              <button className="link" onClick={startEdit}>
                Edit
              </button>
            </span>
          )}
        </div>
        <div>
          <span className="label">{b.remaining < 0 ? 'Over by' : 'Remaining'}</span>
          <span>{money(Math.abs(b.remaining))}</span>
        </div>
        <div>
          <span className="label">Actual so far</span>
          <span>{money(b.total_actual)}</span>
        </div>
        <div>
          <span className="label">Actual vs estimate</span>
          <span>{money(b.actual_variance)}</span>
        </div>
      </div>
      {error && <p className="error-text">{error}</p>}
    </section>
  );
}