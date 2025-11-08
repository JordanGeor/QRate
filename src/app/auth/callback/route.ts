import { NextResponse } from 'next/server';
import { createSupabaseServerClient } from '@/lib/supabase-ssr';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');

  const supa = await createSupabaseServerClient(); // ✅ await
  if (code) {
    await supa.auth.exchangeCodeForSession(code);
  }
  return NextResponse.redirect(new URL('/admin', url.origin));
}
