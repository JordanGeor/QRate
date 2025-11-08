// scripts/seed.ts
import path from 'node:path';
import { config } from 'dotenv';

// 1) Φόρτωσε .env.local πριν κάνεις οτιδήποτε
config({ path: path.resolve(process.cwd(), '.env.local') });

async function run() {
  // 2) Dynamic import ΜΕΤΑ το dotenv, αλλά μέσα στη συνάρτηση
  const { supabaseAdmin } = await import('../src/lib/supabase');

  // (προαιρετικός έλεγχος)
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    throw new Error('ENV missing: NEXT_PUBLIC_SUPABASE_URL');
  }
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error('ENV missing: SUPABASE_SERVICE_ROLE_KEY');
  }

  // 3) Demo location
  const { data: loc, error: e1 } = await supabaseAdmin
    .from('locations')
    .insert({
      name: 'Demo Cafe',
      google_review_link:
        'https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID'
    })
    .select()
    .single();
  if (e1) throw e1;

  // 4) Demo campaign
  const { data: camp, error: e2 } = await supabaseAdmin
    .from('campaigns')
    .insert({
      location_id: loc!.id,
      friendly_name: 'Table QR',
      utm_source: 'qr'
    })
    .select()
    .single();
  if (e2) throw e2;

  console.log('✅ campaignId:', camp!.id);
}

run().catch((err) => {
  console.error('Seed failed:', err);
  process.exit(1);
});
