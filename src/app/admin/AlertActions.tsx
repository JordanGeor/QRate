'use client';

import { useState, useTransition } from 'react';

type Status = 'open' | 'resolved' | 'ignored';

export function AlertActions({ alertId, initialStatus }: { alertId: string; initialStatus: Status }) {
  const [status, setStatus] = useState<Status>(initialStatus);
  const [isPending, start] = useTransition();

  async function set(newStatus: Status) {
    start(async () => {
      const res = await fetch(`/api/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) setStatus(newStatus);
      else alert('Αποτυχία ενημέρωσης alert.');
    });
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-600">Alert:</span>
      <span className="px-2 py-1 rounded-lg border">{status}</span>
      <button disabled={isPending} onClick={() => set('resolved')} className="px-2 py-1 rounded-lg border">Resolve</button>
      <button disabled={isPending} onClick={() => set('ignored')} className="px-2 py-1 rounded-lg border">Ignore</button>
      <button disabled={isPending} onClick={() => set('open')} className="px-2 py-1 rounded-lg border">Reopen</button>
    </div>
  );
}
