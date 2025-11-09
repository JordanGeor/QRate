import { NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';

export async function GET() {
  const supabase = await createServerSupabaseClient();
  const { data: { session } } = await supabase.auth.getSession();
  return NextResponse.json({
    email: session?.user.email,
    app_metadata: session?.user.app_metadata,
  });
}
