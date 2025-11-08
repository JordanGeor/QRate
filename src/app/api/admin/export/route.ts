import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

function toCSV(rows: any[]) {
  const headers = ['id','created_at','rating','comment','contact','location','campaign'];
  const escape = (v: any) =>
    `"${String(v ?? '').replace(/"/g, '""').replace(/\r?\n/g, ' ')}"`;
  const lines = [
    headers.join(','),
    ...rows.map((r) =>
      [
        r.id,
        r.created_at,
        r.rating,
        r.comment,
        r.contact,
        r.campaigns?.locations?.name ?? '',
        r.campaigns?.friendly_name ?? '',
      ].map(escape).join(',')
    ),
  ];
  return lines.join('\r\n');
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const rating = searchParams.get('rating'); // all | low | high
  const campaign = searchParams.get('campaign');
  const q = searchParams.get('q') ?? undefined;

  let query = supabaseAdmin
    .from('feedback')
    .select(
      `
      id, rating, comment, contact, created_at,
      campaigns ( friendly_name, locations ( name ) )
    `
    )
    .order('created_at', { ascending: false })
    .limit(1000);

  if (rating === 'low') query = query.lte('rating', 3);
  if (rating === 'high') query = query.gte('rating', 4);
  if (campaign) query = query.eq('campaign_id', campaign);
  if (q) query = query.ilike('comment', `%${q}%`);

  const { data, error } = await query;
  if (error) {
    return NextResponse.json({ ok: false, error: error.message }, { status: 400 });
  }

  const csv = toCSV(data || []);
  return new NextResponse(csv, {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': 'attachment; filename="feedback-export.csv"',
    },
  });
}
