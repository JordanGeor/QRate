import { createSupabaseServerClient } from '@/lib/supabase-ssr';
import { redirect } from 'next/navigation';
import { supabaseAdmin } from '@/lib/supabase';
import Link from 'next/link';
import { AlertActions } from './AlertActions';


type SearchParams = {
  rating?: 'all' | 'low' | 'high';
  campaign?: string;
  q?: string;
};

// Guard: απαιτεί login, προαιρετικά ελέγχει allowlist emails
async function requireUser() {
  const supa = await createSupabaseServerClient(); // ✅ τώρα είναι async
  const { data: { user } } = await supa.auth.getUser();

  if (!user) redirect('/login');

  const allow = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || '')
    .split(',').map(s => s.trim()).filter(Boolean);
  if (allow.length && user.email && !allow.includes(user.email)) {
    redirect('/login');
  }
  return user;
}



async function fetchData(filters: SearchParams) {
  let query = supabaseAdmin
    .from('feedback')
    .select(
      `
      id, rating, comment, contact, created_at, campaign_id,
      campaigns ( friendly_name, locations ( name ) ),
      alerts ( id, status )
    `
    )
    .order('created_at', { ascending: false })
    .limit(100);

  if (filters.rating === 'low') query = query.lte('rating', 3);
  if (filters.rating === 'high') query = query.gte('rating', 4);
  if (filters.campaign) query = query.eq('campaign_id', filters.campaign);
  if (filters.q) query = query.ilike('comment', `%${filters.q}%`);

  const { data, error } = await query;
  if (error) throw error;
  return (data ?? []) as any[];
}

async function fetchCampaigns() {
  const { data, error } = await supabaseAdmin
    .from('campaigns')
    .select('id, friendly_name, locations(name)')
    .order('created_at', { ascending: false });
  if (error) throw error;
  return (data ?? []) as any[];
}

export default async function AdminPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  await requireUser();  // redirect σε /login αν δεν υπάρχει session

  const sp = { ...(await searchParams) };
  const rating = sp.rating ?? 'all';

  const [rows, campaigns] = await Promise.all([fetchData(sp), fetchCampaigns()]);

  const kpiTotal = rows.length;
  const kpiPos = rows.filter((r) => r.rating >= 4).length;
  const kpiNeg = rows.filter((r) => r.rating <= 3).length;
  const avg =
    rows.length > 0
      ? (rows.reduce((a, r) => a + (r.rating ?? 0), 0) / rows.length).toFixed(2)
      : '—';

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">QRate · Admin</h1>
        <Link href="/logout" className="text-sm text-gray-600 underline">
          Αποσύνδεση
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid sm:grid-cols-4 gap-3">
        <div className="rounded-xl border p-4">
          <div className="text-sm text-gray-600">Σύνολο</div>
          <div className="text-2xl font-semibold">{kpiTotal}</div>
        </div>
        <div className="rounded-xl border p-4">
          <div className="text-sm text-gray-600">Μ.Ο. Βαθμολογίας</div>
          <div className="text-2xl font-semibold">{avg}</div>
        </div>
        <div className="rounded-xl border p-4">
          <div className="text-sm text-gray-600">Θετικά (≥4)</div>
          <div className="text-2xl font-semibold">{kpiPos}</div>
        </div>
        <div className="rounded-xl border p-4">
          <div className="text-sm text-gray-600">Αρνητικά (≤3)</div>
          <div className="text-2xl font-semibold">{kpiNeg}</div>
        </div>
      </div>

      {/* Filters */}
      <form className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col">
          <label className="text-xs text-gray-600">Rating</label>
          <select name="rating" defaultValue={rating} className="border rounded-lg px-3 py-2">
            <option value="all">Όλα</option>
            <option value="high">Μόνο ≥4</option>
            <option value="low">Μόνο ≤3</option>
          </select>
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-gray-600">Καμπάνια</label>
          <select name="campaign" defaultValue={sp.campaign ?? ''} className="border rounded-lg px-3 py-2">
            <option value="">Όλες</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.locations?.name ?? '—'} · {c.friendly_name ?? '—'}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-gray-600">Αναζήτηση</label>
          <input
            name="q"
            defaultValue={sp.q ?? ''}
            placeholder="Κείμενο σχολίου…"
            className="border rounded-lg px-3 py-2"
          />
        </div>

        <button className="px-4 py-2 rounded-lg bg-black text-white">Φιλτράρισμα</button>

        <Link
          href={{ pathname: '/api/admin/export', query: sp as any }}
          className="px-4 py-2 rounded-lg border"
        >
          Export CSV
        </Link>
      </form>

      {/* List */}
      <div className="grid gap-3">
        {rows.map((f) => {
          const loc = f.campaigns?.locations?.name ?? '—';
          const camp = f.campaigns?.friendly_name ?? '—';
          const alert = Array.isArray(f.alerts) && f.alerts.length > 0 ? f.alerts[0] : null;

          return (
            <div key={f.id} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm text-gray-600">
                  {loc} · {camp}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(f.created_at).toLocaleString()}
                </div>
              </div>

              <div className="mt-1 text-lg">⭐ {f.rating}</div>
              {f.comment && <div className="mt-2">{f.comment}</div>}
              {f.contact && <div className="mt-1 text-sm text-gray-600">Contact: {f.contact}</div>}

              <div className="mt-3">
                {alert ? (
                  <AlertActions alertId={alert.id} initialStatus={alert.status} />
                ) : f.rating <= 3 ? (
                  <div className="text-sm text-amber-700">
                    Χωρίς alert (τα νέα feedback ≤3 δημιουργούν αυτόματα alert)
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
