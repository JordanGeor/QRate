import 'server-only';
import { redirect } from 'next/navigation';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import LogoutButton from '@/components/LogoutButton';
import AdminFilters from './AdminFilters';
import FeedbackTable from './FeedbackTable';

type Props = {
  searchParams: {
    q?: string;
    status?: 'all' | 'approved' | 'pending';
    p?: string;   // page
    ps?: string;  // pageSize
  };
};

export default async function AdminPanelPage({ searchParams }: Props) {
  const supabase = await createServerSupabaseClient();
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) redirect('/admin');

  const meta = (session.user.app_metadata ?? {}) as Record<string, any>;
  const isAdmin = meta.role === 'admin' || meta.is_admin === true;
  if (!isAdmin) redirect('/admin');

  const page = Math.max(1, parseInt(searchParams.p ?? '1', 10));
  const pageSize = Math.min(100, Math.max(1, parseInt(searchParams.ps ?? '20', 10)));

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Admin Panel</h1>
        <LogoutButton />
      </div>

      <AdminFilters />

      <FeedbackTable
        q={searchParams.q}
        status={searchParams.status === 'all' ? null : searchParams.status}
        page={page}
        pageSize={pageSize}
      />
    </div>
  );
}
