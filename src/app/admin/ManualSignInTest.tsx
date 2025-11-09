'use client';
import { useMemo, useState } from 'react';
import { createBrowserSupabaseClient } from '@/lib/supabase/client';

export default function ManualSignInTest() {
  const supabase = useMemo(() => createBrowserSupabaseClient(), []);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState<string | null>(null);

  return (
    <div className="mt-6 border-t pt-4">
      <h2 className="text-sm font-medium mb-2">Manual sign-in test</h2>
      <input className="border px-2 py-1 w-full mb-2" placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
      <input className="border px-2 py-1 w-full mb-2" placeholder="password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button
        className="px-3 py-1 border rounded"
        onClick={async () => {
          const { data, error } = await supabase.auth.signInWithPassword({ email, password });
          if (error) setMsg(`Error: ${error.message}`);
          else setMsg(`OK: ${data.session?.user.email}`);
        }}
      >
        Sign in
      </button>
      {msg && <p className="text-xs text-gray-600 mt-2">{msg}</p>}
    </div>
  );
}
