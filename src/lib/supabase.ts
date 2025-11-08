import { createClient } from '@supabase/supabase-js';

// Διαβάζουμε τα env vars
const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

// Έλεγχος: αν λείπει κάτι, ρίξε καθαρό error
if (!url) throw new Error('❌ Missing env: NEXT_PUBLIC_SUPABASE_URL');
if (!anonKey) throw new Error('❌ Missing env: NEXT_PUBLIC_SUPABASE_ANON_KEY');
if (!serviceKey) throw new Error('❌ Missing env: SUPABASE_SERVICE_ROLE_KEY');

// Δημόσιος client — για frontend
export const supabaseAnon = createClient(url, anonKey, {
  auth: { persistSession: false },
});

// Server-side client — για scripts & API routes
export const supabaseAdmin = createClient(url, serviceKey, {
  auth: { persistSession: false },
});
