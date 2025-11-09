import { NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase/admin';

const bodySchema = z.object({
  campaignId: z.string().uuid(),
  rating: z.number().int().min(1).max(5),
  comment: z.string().max(500).optional(),
  contact: z.string().max(120).optional(),
  contactOptIn: z.boolean().optional()
});

export async function POST(req: Request) {
  try {
    const json = await req.json();
    const data = bodySchema.parse(json);

    const { data: fb, error } = await supabaseAdmin
      .from('feedback')
      .insert({
        campaign_id: data.campaignId,
        rating: data.rating,
        comment: data.comment ?? null,
        contact: data.contact ?? null,
        contact_opt_in: !!data.contactOptIn
      })
      .select()
      .single();

    if (error) throw error;

    // Δημιούργησε alert αν rating ≤ 3
    if (data.rating <= 3) {
      await supabaseAdmin.from('alerts').insert({ feedback_id: fb.id });
    }

    return NextResponse.json({ ok: true, id: fb.id });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 400 });
  }
}
