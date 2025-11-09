'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { createBrowserSupabaseClient } from '@/lib/supabase/client';
import LogoutButton from '@/components/LogoutButton';

export default function AdminLoginPage() {
  const router = useRouter();
  const [origin, setOrigin] = useState<string>('');
  useEffect(() => setOrigin(window.location.origin), []);

  const supabase = useMemo(() => createBrowserSupabaseClient(), []);

  // αν γίνει SIGNED_IN, στείλ' τον στο panel (αν είναι admin, θα περάσει)
  useEffect(() => {
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        router.push('/admin/panel');
      }
    });
    return () => sub.subscription.unsubscribe();
  }, [supabase, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow p-6">
        <h1 className="text-xl font-semibold mb-4">Σύνδεση διαχειριστή</h1>

        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={['google']}
          redirectTo={origin ? `${origin}/auth/callback?next=/admin/panel` : undefined}
          view="sign_in"
          localization={{
            variables: {
              sign_in: { email_label: 'Email', password_label: 'Κωδικός' },
            },
          }}
          magicLink
        />

        {/* Αν ο χρήστης είναι συνδεδεμένος αλλά ΔΕΝ είναι admin, δείξε καθαρό μήνυμα */}
        <NotAdminBanner />
      </div>
    </div>
  );
}

function NotAdminBanner() {
  const supabase = useMemo(() => createBrowserSupabaseClient(), []);
  const [state, setState] = useState<
    { status: 'checking' | 'no-session' | 'admin' | 'not-admin'; email?: string }
  >({ status: 'checking' });

  useEffect(() => {
    let mounted = true;
    supabase.auth.getUser().then(({ data }) => {
      if (!mounted) return;
      const user = data.user;
      if (!user) return setState({ status: 'no-session' });
      const meta = (user.app_metadata ?? {}) as Record<string, any>;
      const isAdmin = meta.role === 'admin' || meta.is_admin === true;
      setState({ status: isAdmin ? 'admin' : 'not-admin', email: user.email ?? undefined });
    });
    return () => {
      mounted = false;
    };
  }, [supabase]);

  if (state.status !== 'not-admin') return null;

  return (
    <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      <div className="font-medium mb-1">Δεν έχεις εξουσιοδότηση διαχειριστή</div>
     
      <div className="mt-3 flex items-center gap-2">
        <LogoutButton />
        <span className="text-xs text-amber-800">
          Κάνε έξοδο και δοκίμασε με άλλον λογαριασμό ή ζήτησε να σε ενεργοποιήσουν ως admin.
        </span>
      </div>
    </div>
  );
}
