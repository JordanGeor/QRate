'use client';

import { useMemo, useState } from 'react';
import { createBrowserSupabaseClient } from '@/lib/supabase/client';

export default function FeedbackForm({ campaignId }: { campaignId: string }) {
  const supabase = useMemo(() => createBrowserSupabaseClient(), []);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [rating, setRating] = useState<number | ''>('');
  const [comment, setComment] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'ok' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('submitting');
    setError(null);

    const r = Number(rating);
    if (!r || r < 1 || r > 5) {
      setStatus('error');
      setError('Επίλεξε βαθμολογία 1–5');
      return;
    }

    if (!comment.trim()) {
      setStatus('error');
      setError('Το σχόλιο είναι υποχρεωτικό');
      return;
    }

    // 👇 ΕΔΩ ΜΠΑΙΝΕΙ ΤΟ insert
    const { error } = await supabase
      .from('feedbacks')
      .insert({
        campaign_id: campaignId,
        name: name || null,
        email: email || null,
        rating: r,
        comment: comment.trim(),
        source: 'qr',
      });

    if (error) {
      setStatus('error');
      setError(error.message);
      return;
    }

    setStatus('ok');
  }

  if (status === 'ok') {
    return (
      <div className="text-center py-12">
        <h1 className="text-xl font-semibold mb-2">Ευχαριστούμε! ✅</h1>
        <p className="text-gray-600">Η κριτική σου καταχωρήθηκε.</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label className="block text-sm mb-1">Όνομα (προαιρετικό)</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border rounded-lg px-3 py-2"
        />
      </div>

      <div>
        <label className="block text-sm mb-1">Email (προαιρετικό)</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border rounded-lg px-3 py-2"
        />
      </div>

      <div>
        <label className="block text-sm mb-1">Βαθμολογία (1–5)</label>
        <select
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
          className="w-full border rounded-lg px-3 py-2"
        >
          <option value="">Επίλεξε...</option>
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm mb-1">Σχόλιο</label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          className="w-full border rounded-lg px-3 py-2"
          rows={4}
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={status === 'submitting'}
        className="w-full border rounded-lg px-3 py-2 hover:bg-gray-50 disabled:opacity-50"
      >
        {status === 'submitting' ? 'Αποστολή...' : 'Υποβολή'}
      </button>
    </form>
  );
}
