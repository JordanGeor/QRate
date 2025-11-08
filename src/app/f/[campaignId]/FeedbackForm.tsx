'use client';

import { useState } from 'react';
import Link from 'next/link';

export function FeedbackForm({ campaignId, googleLink }: { campaignId: string; googleLink: string }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [contact, setContact] = useState('');
  const [opt, setOpt] = useState(true);
  const [done, setDone] = useState(false);

  const low = rating > 0 && rating <= 3;

  async function submit() {
    const res = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId, rating, comment, contact, contactOptIn: opt })
    });
    const json = await res.json();
    if (json.ok) setDone(true);
    else alert(json.error ?? 'Σφάλμα');
  }

  if (done) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-medium">Ευχαριστούμε για το feedback!</h2>
        <a
          href={googleLink || '#'}
          target="_blank"
          rel="noreferrer"
          className="block w-full text-center rounded-xl px-4 py-3 font-medium border hover:bg-gray-50"
        >
          Αφήστε κριτική στο Google
        </a>
        {low && (
          <p className="text-sm text-gray-600">
            Κρίμα που δεν ήταν τέλεια. Θέλετε να μας δώσετε ευκαιρία να το διορθώσουμε;
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            onClick={() => setRating(n)}
            className={`h-10 w-10 rounded-full border ${rating >= n ? 'bg-black text-white' : 'bg-white'}`}
          >
            {n}
          </button>
        ))}
      </div>

      <textarea
        placeholder="Πείτε μας τι πήγε καλά ή τι να βελτιώσουμε…"
        className="w-full border rounded-xl p-3"
        value={comment}
        onChange={e => setComment(e.target.value)}
      />

      <input
        className="w-full border rounded-xl p-3"
        placeholder="Email ή τηλέφωνο (προαιρετικό)"
        value={contact}
        onChange={e => setContact(e.target.value)}
      />

      <label className="text-sm flex items-center gap-2">
        <input type="checkbox" checked={opt} onChange={e => setOpt(e.target.checked)} />
        Θέλω να επικοινωνήσετε μαζί μου αν χρειαστεί.
      </label>

      <button
        onClick={submit}
        disabled={!rating}
        className="w-full rounded-xl bg-black text-white py-3 font-medium disabled:opacity-50"
      >
        Υποβολή
      </button>
    </div>
  );
}
