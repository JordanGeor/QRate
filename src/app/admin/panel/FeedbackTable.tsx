import { BulkButton } from './BulkButton';
import { supabaseAdmin } from '@/lib/supabase/admin';
import Link from 'next/link';
import { bulkSetApproval } from './actions';
import SelectAll from './SelectAll';




type Props = {
  q?: string | null;
  status?: string | null;
  page?: number;
  pageSize?: number;
};

export default async function FeedbackTable({ q, status, page = 1, pageSize = 20 }: Props) {
  let query = supabaseAdmin
    .from('feedbacks')
    .select('*', { count: 'exact' })
    .order('created_at', { ascending: false });

  if (status === 'approved') query = query.eq('approved', true);
  if (status === 'pending') query = query.eq('approved', false);

  if (q && q.trim()) {
    const s = `%${q.trim()}%`;
    query = query.or(`name.ilike.${s},email.ilike.${s},comment.ilike.${s}`);
  }

  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;

  const { data, error, count } = await query.range(from, to);
  if (error) {
    return <div className="text-red-600 text-sm">Σφάλμα φόρτωσης: {error.message}</div>;
  }

  const total = count ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const formId = 'bulk-approval-form';

  return (
    <div className="space-y-3">
      {/* Bulk toolbar */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Σύνολο: <span className="font-medium">{total}</span> αποτελέσματα
        </div>

        <div className="flex items-center gap-3">
          <SelectAll formId={formId} />
          <form id={formId} action={bulkSetApproval} className="flex items-center gap-2">
            {/* αυτά τα buttons στέλνουν approved=true/false μαζί με τα ids που είναι checked */}
            <BulkButton name="approved" value="true" label="Bulk Approve" />
            <BulkButton name="approved" value="false" label="Bulk Reject" />
          </form>
        </div>
      </div>

      {/* Table wrapped by the same form (so that ids belong to the form) */}
      <form action={bulkSetApproval} className="overflow-x-auto border rounded-xl">
        <input type="hidden" name="approved" value="" />
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100">
            <tr className="text-left">
              <th className="px-3 py-2 w-10">#</th>
              <th className="px-3 py-2">Ημ/νία</th>
              <th className="px-3 py-2">Όνομα</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Rating</th>
              <th className="px-3 py-2">Σχόλιο</th>
              <th className="px-3 py-2">Κατάσταση</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((row) => (
              <tr key={row.id} className="border-t align-top">
                <td className="px-3 py-2">
                  <input type="checkbox" name="ids" value={row.id} className="h-4 w-4" />
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  {new Date(row.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-2">{row.name ?? '—'}</td>
                <td className="px-3 py-2">{row.email ?? '—'}</td>
                <td className="px-3 py-2">{row.rating ?? '—'}</td>
                <td className="px-3 py-2 max-w-[28rem]">
                  <span className="line-clamp-2">{row.comment ?? '—'}</span>
                </td>
                <td className="px-3 py-2">
                  {row.approved ? (
                    <span className="rounded-md bg-emerald-100 text-emerald-800 px-2 py-0.5">Approved</span>
                  ) : (
                    <span className="rounded-md bg-amber-100 text-amber-800 px-2 py-0.5">Pending</span>
                  )}
                </td>
              </tr>
            ))}
            {!data?.length && (
              <tr>
                <td colSpan={7} className="px-3 py-8 text-center text-gray-500">
                  Δεν βρέθηκαν αποτελέσματα.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </form>

      <Pagination
        current={page}
        totalPages={totalPages}
        q={q}
        status={status}
        pageSize={pageSize}
      />
    </div>
  );
}

/* ---------- Pagination ---------- */

function Pagination({ current, totalPages, q, status, pageSize }: { current: number; totalPages: number; q?: string | null; status?: string | null; pageSize: number; }) {
  const prev = Math.max(1, current - 1);
  const next = Math.min(totalPages, current + 1);
  const build = (p: number) => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (status) params.set('status', status);
    if (pageSize !== 20) params.set('ps', String(pageSize));
    params.set('p', String(p));
    return `/admin/panel?${params.toString()}`;
  };
  return (
    <div className="flex items-center gap-2 justify-end text-sm">
      <span className="text-gray-500">Σελίδα {current} / {totalPages}</span>
      <Link href={build(prev)} className="border rounded-lg px-2 py-1 disabled:opacity-50" aria-disabled={current<=1}>Προηγούμενη</Link>
      <Link href={build(next)} className="border rounded-lg px-2 py-1 disabled:opacity-50" aria-disabled={current>=totalPages}>Επόμενη</Link>
    </div>
  );
}
