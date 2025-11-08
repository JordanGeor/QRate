'use client';

import { useEffect, useMemo, useState } from 'react';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { createBrowserSupabaseClient } from '@/lib/supabase/client';

export default function AdminLoginPage() {
  const [origin, setOrigin] = useState<string>('');
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  const supabase = useMemo(() => createBrowserSupabaseClient(), []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow p-6">
        <h1 className="text-xl font-semibold mb-4">Σύνδεση διαχειριστή</h1>

        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={['google']}
          // Μετά το login θα πάει στο /admin/panel
          redirectTo={
            origin ? `${origin}/auth/callback?next=/admin/panel` : undefined
          }
          view="sign_in"
          localization={{
            variables: {
              sign_in: { email_label: 'Email', password_label: 'Κωδικός' },
            },
          }}
          magicLink
        />

        <p className="text-xs text-gray-500 mt-4">
          Επιτρέπεται πρόσβαση μόνο σε εξουσιοδοτημένους λογαριασμούς.
        </p>
      </div>
    </div>
  );
}
