// C:\Users\user1\Desktop\QRate\src\app\auth\callback\route.ts
import 'server-only';
import { NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const next = url.searchParams.get('next') || '/admin/panel';

  const supabase = createServerSupabaseClient();

  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      // Αν αποτύχει το exchange, γύρνα στο login
      return NextResponse.redirect(new URL('/admin', url.origin));
    }
  }

  // Αν δεν υπάρχει code (ή όλα καλά), προχώρα στο next
  return NextResponse.redirect(new URL(next, url.origin));
}
