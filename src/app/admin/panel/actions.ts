'use server';

import { revalidatePath } from 'next/cache';
import { supabaseAdmin } from '@/lib/supabase/admin';

export async function bulkSetApproval(formData: FormData) {
  const approved = String(formData.get('approved')) === 'true';
  const ids = formData.getAll('ids').map(String).filter(Boolean);

  if (ids.length === 0) {
    // προαιρετικά: απλά revalidate χωρίς αλλαγή
    revalidatePath('/admin/panel');
    return;
  }

  const { error } = await supabaseAdmin
    .from('feedbacks')
    .update({ approved })
    .in('id', ids);

  if (error) throw new Error(error.message);

  revalidatePath('/admin/panel');
}
