import { supabaseAdmin } from '@/lib/supabase';
import { FeedbackForm } from './FeedbackForm';

async function getCampaign(campaignId: string) {
  const { data, error } = await supabaseAdmin
    .from('campaigns')
    .select('id, friendly_name, locations(name, google_review_link)')
    .eq('id', campaignId)
    .single();
  if (error) return null;
  return data as any;
}

export default async function FeedbackPage({
  params,
}: {
  // 👇 στο Next 16 τα params είναι Promise
  params: Promise<{ campaignId: string }>;
}) {
  // 👇 κάνε await πρώτα
  const { campaignId } = await params;

  const campaign = await getCampaign(campaignId);
  if (!campaign) return <div className="p-6">Καμπάνια δεν βρέθηκε.</div>;

  const googleLink = campaign.locations?.google_review_link ?? '';

  return (
    <div className="min-h-screen p-6 flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-2xl shadow p-6 space-y-5">
        <div>
          <h1 className="text-xl font-semibold">Πώς ήταν η εμπειρία σας;</h1>
          <p className="text-sm text-gray-600">
            {campaign.locations?.name} — {campaign.friendly_name ?? 'QRate'}
          </p>
        </div>
        <FeedbackForm campaignId={campaign.id} googleLink={googleLink} />
      </div>
    </div>
  );
}
