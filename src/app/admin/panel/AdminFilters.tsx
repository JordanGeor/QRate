'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';

export default function AdminFilters() {
  const router = useRouter();
  const sp = useSearchParams();

  const [q, setQ] = useState(sp.get('q') ?? '');
  const [status, setStatus] = useState(sp.get('status') ?? 'all');
  const [pageSize, setPageSize] = useState(sp.get('ps') ?? '20');

  useEffect(() => {
    setQ(sp.get('q') ?? '');
    setStatus(sp.get('status') ?? 'all');
    setPageSize(sp.get('ps') ?? '20');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sp.toString()]);

  function apply() {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (status !== 'all') params.set('status', status);
    if (pageSize !== '20') params.set('ps', pageSize);
    // reset page when applying filters
    params.set('p', '1');
    router.push(`/admin/panel?${params.toString()}`);
  }

  return (
    <div className="mb-4 grid grid-cols-1 sm:grid-cols-4 gap-2">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Αναζήτηση σε όνομα/σχόλιο/email…"
        className="border rounded-lg px-3 py-2"
      />
      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="border rounded-lg px-3 py-2"
      >
        <option value="all">Όλα</option>
        <option value="approved">Εγκεκριμένα</option>
        <option value="pending">Σε εκκρεμότητα</option>
      </select>
      <select
        value={pageSize}
        onChange={(e) => setPageSize(e.target.value)}
        className="border rounded-lg px-3 py-2"
      >
        <option value="10">10 / σελίδα</option>
        <option value="20">20 / σελίδα</option>
        <option value="50">50 / σελίδα</option>
      </select>
      <button
        onClick={apply}
        className="border rounded-lg px-3 py-2 hover:bg-gray-50"
      >
        Εφαρμογή
      </button>
    </div>
  );
}
