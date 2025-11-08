'use client';

import { supabaseBrowser } from '@/lib/supabase-browser';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { useEffect, useState } from 'react';

export default function LoginPage() {
  const [origin, setOrigin] = useState<string>('');
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow p-6">
        <h1 className="text-xl font-semibold mb-4">Σύνδεση διαχειριστή</h1>
        <Auth
          supabaseClient={supabaseBrowser}
          appearance={{ theme: ThemeSupa }}
          providers={['google']}
          redirectTo={origin ? `${origin}/auth/callback` : undefined}
          view="sign_in"
          localization={{
            variables: {
              sign_in: { email_label: 'Email', password_label: 'Κωδικός' }
            }
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
