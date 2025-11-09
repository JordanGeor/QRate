import 'server-only';
import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/admin';

export async function GET() {
  const { data, error } = await supabaseAdmin
    .from('feedbacks')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const rows = data ?? [];
  const headers = ['id','created_at','name','email','rating','comment','approved','source'];
  const csv = [
    headers.join(','),
    ...rows.map(r => headers.map((h) => {
      let v = r[h];
      if (v === null || v === undefined) return '';
      // απλό escaping διπλών εισαγωγικών/κομμάτων/νέων γραμμών
      v = String(v).replace(/"/g, '""');
      return /[",\n]/.test(String(v)) ? `"${v}"` : v;
    }).join(','))
  ].join('\n');

  return new NextResponse(csv, {
    headers: {
      'content-type': 'text/csv; charset=utf-8',
      'content-disposition': 'attachment; filename="feedbacks.csv"',
    },
  });
}
