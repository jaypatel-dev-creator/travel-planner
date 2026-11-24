import { useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';

export default function ActivityForm({ activity, onDone, onCancel }) {
  const { trip, addActivity, updateActivity } = useTrip();
  const isEdit = Boolean(activity);

  const [form, setForm] = useState({
    title: activity?.title ?? '',
    date: activity?.date ?? trip.start_date,
    start_time: activity?.start_time ?? '',
    destination_id: activity?.destination_id ?? '',
    estimated_cost: activity?.estimated_cost ?? '',
    actual_cost: activity?.actual_cost ?? '',
    notes: activity?.notes ?? '',
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    const payload = {
      title: form.title.trim(),
      date: form.date,
      start_time: form.start_time || null,
      destination_id: form.destination_id || null,
      estimated_cost: form.estimated_cost === '' ? 0 : Number(form.estimated_cost),
      notes: form.notes.trim(),
    };
    if (form.actual_cost !== '') payload.actual_cost = Number(form.actual_cost);
    else if (isEdit) payload.actual_cost = null; // clear it

    try {
      if (isEdit) await updateActivity(activity.id, payload);
      else await addActivity(payload);
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="form-grid activity-form" onSubmit={submit}>
      <label>
        Title
        <input required maxLength={120} value={form.title} onChange={set('title')} placeholder="Visit Gateway of India" />
      </label>
      <div className="row">
        <label>
          Date
          <input required type="date" min={trip.start_date} max={trip.end_date} value={form.date} onChange={set('date')} />
        </label>
        <label>
          Time
          <input type="time" value={form.start_time} onChange={set('start_time')} />
        </label>
      </div>
      <label>
        Destination
        <select value={form.destination_id} onChange={set('destination_id')}>
          <option value="">None</option>
          {trip.destinations.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </label>
      <div className="row">
        <label>
          Estimated cost ({trip.currency})
          <input type="number" min="0" step="0.01" value={form.estimated_cost} onChange={set('estimated_cost')} placeholder="0" />
        </label>
        <label>
          Actual cost ({trip.currency})
          <input type="number" min="0" step="0.01" value={form.actual_cost} onChange={set('actual_cost')} placeholder="optional" />
        </label>
      </div>
      <label>
        Notes
        <textarea rows={2} maxLength={1000} value={form.notes} onChange={set('notes')} />
      </label>
      {error && <p className="error-text">{error}</p>}
      <div className="actions">
        <button type="button" onClick={onCancel}>
          Cancel
        </button>
        <button className="primary" disabled={saving}>
          {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add activity'}
        </button>
      </div>
    </form>
  );
}