import { cookies } from 'next/headers';
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs';

async function requireUser() {
  // ❌ ΛΑΘΟΣ:
  // const cookieStore = cookies();
  // const supabase = createServerComponentClient({ cookies: () => cookieStore });

  // ✅ ΣΩΣΤΟ: Πέρνα τη συνάρτηση ως reference
  const supabase = createServerComponentClient({ cookies });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect('/login');

  const allowed = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  if (allowed.length && user?.email && !allowed.includes(user.email)) {
    redirect('/login');
  }

  return user;
}
