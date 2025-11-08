import 'server-only';
import { createClient } from '@supabase/supabase-js';

// Χρησιμοποίησε ΜΗ-δημόσιο URL αν το έχεις, αλλιώς κάνε fallback στο public.
const url =
  process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL!;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

if (!url) throw new Error('❌ Missing env: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');
if (!serviceKey) throw new Error('❌ Missing env: SUPABASE_SERVICE_ROLE_KEY');

export const supabaseAdmin = createClient(url, serviceKey, {
  auth: { persistSession: false },
});
