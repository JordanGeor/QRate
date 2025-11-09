import 'server-only';
import { NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const next = url.searchParams.get('next') || '/admin/panel';

  const supabase = await createServerSupabaseClient(); // ⬅️ await

  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) return NextResponse.redirect(new URL('/admin', url.origin));
  }
  return NextResponse.redirect(new URL(next, url.origin));
}
