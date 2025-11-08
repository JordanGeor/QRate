// src/lib/supabase-ssr.ts
import { createServerClient, createBrowserClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

/**
 * Next 16: cookies() είναι async -> πρέπει να το κάνουμε await εδώ.
 * Επιστρέφουμε client έτοιμο για Server Components / Route Handlers.
 */
export async function createSupabaseServerClient() {
  const cookieStore = await cookies(); // ✅ ΑΠΟΛΥΤΟ ΣΗΜΕΙΟ-ΚΛΕΙΔΙ

  return createServerClient(url, anon, {
    cookies: {
      get(name: string) {
        // cookieStore είναι ήδη resolved αντικείμενο
        return cookieStore.get(name)?.value;
      },
      set(name: string, value: string, options: CookieOptions) {
        try {
          cookieStore.set({ name, value, ...options });
        } catch {
          // Σε RSC ίσως δεν επιτρέπεται write - απλώς αγνόησέ το
        }
      },
      remove(name: string, options: CookieOptions) {
        try {
          cookieStore.set({ name, value: '', ...options, maxAge: 0 });
        } catch {
          // Σε RSC ίσως δεν επιτρέπεται write - αγνόησέ το
        }
      },
    },
  });
}

/** Browser client για client components (login/logout UI) */
export function createSupabaseBrowserClient() {
  return createBrowserClient(url, anon);
}
