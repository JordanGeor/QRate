// middleware.ts (root)
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient, type CookieOptions } from '@supabase/ssr';

export const config = { matcher: ['/admin/:path*'] };

export async function middleware(req: NextRequest) {
  // Αφησε δημόσιο μόνο το /admin (login)
  if (req.nextUrl.pathname === '/admin') return NextResponse.next();

  const res = NextResponse.next();
  // Debug header: για να δεις ότι το middleware «πιάνει»
  res.headers.set('x-mw', 'admin-guard');

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get: (name: string) => req.cookies.get(name)?.value,
        set: (name: string, value: string, options: CookieOptions) => {
          res.cookies.set({ name, value, ...options });
        },
        remove: (name: string, options: CookieOptions) => {
          res.cookies.set({ name, value: '', ...options, maxAge: 0 });
        },
      },
    }
  );

  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    return NextResponse.redirect(new URL('/admin', req.url));
  }

  const meta = (session.user.app_metadata ?? {}) as Record<string, any>;
  const isAdmin = meta.role === 'admin' || meta.is_admin === true;

  if (!isAdmin) {
    return NextResponse.redirect(new URL('/admin', req.url));
  }

  return res;
}
