import { useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'AED', 'SGD'];

export default function TripForm({ onDone, onCancel }) {
  const { createTrip } = useTrip();
  const [form, setForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
    budget_total: '',
    currency: 'INR',
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await createTrip({
        name: form.name.trim(),
        start_date: form.start_date,
        end_date: form.end_date,
        budget_total: form.budget_total === '' ? 0 : Number(form.budget_total),
        currency: form.currency,
      });
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="card form-grid trip-form" onSubmit={submit}>
      <h2>New trip</h2>
      <label>
        Name
        <input required maxLength={120} value={form.name} onChange={set('name')} placeholder="Goa getaway" />
      </label>
      <div className="row">
        <label>
          Start date
          <input required type="date" value={form.start_date} onChange={set('start_date')} />
        </label>
        <label>
          End date
          <input required type="date" min={form.start_date} value={form.end_date} onChange={set('end_date')} />
        </label>
      </div>
      <div className="row">
        <label>
          Total budget
          <input type="number" min="0" step="0.01" value={form.budget_total} onChange={set('budget_total')} placeholder="0" />
        </label>
        <label>
          Currency
          <select value={form.currency} onChange={set('currency')}>
            {CURRENCIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      {error && <p className="error-text">{error}</p>}
      <div className="actions">
        {onCancel && (
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button className="primary" disabled={saving}>
          {saving ? 'Creating…' : 'Create trip'}
        </button>
      </div>
    </form>
  );
}