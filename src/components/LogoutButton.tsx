'use client';
import { createBrowserSupabaseClient } from '@/lib/supabase/client';

export default function LogoutButton() {
  const supabase = createBrowserSupabaseClient();
  return (
    <button
      onClick={async () => {
        await supabase.auth.signOut();
        window.location.href = '/admin'; // γυρνά στο login
      }}
      className="border px-3 py-1 rounded"
    >
      Logout
    </button>
  );
}
