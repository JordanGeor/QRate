// // src/app/f/[campaignId]/page.tsx
// import { notFound } from 'next/navigation';
// import { createServerSupabaseClient } from '@/lib/supabase/server';
// import FeedbackForm from './FeedbackForm';

// export default async function CampaignFeedbackPage({
//   params,
// }: { params: { campaignId: string } }) {
//   const supabase = await createServerSupabaseClient();

//   const { data: campaign, error } = await supabase
//     .from('campaigns')
//     .select('id, friendly_name, active')   // 👈 εδώ
//     .eq('id', params.campaignId)
//     .eq('active', true)
//     .single();

//   if (error || !campaign) notFound();

//   return (
//     <div className="min-h-screen p-6 flex items-center justify-center bg-gray-50">
//       <div className="w-full max-w-md bg-white rounded-2xl shadow p-6 space-y-5">
//         <div>
//           <h1 className="text-xl font-semibold">Πώς ήταν η εμπειρία σας;</h1>
//           <p className="text-sm text-gray-600">
//             {campaign.friendly_name ?? 'QRate'}
//           </p>
//         </div>
//         <FeedbackForm campaignId={campaign.id} />
//       </div>
//     </div>
//   );
// }


export default function CampaignFeedbackPage({ params }: { params: { campaignId: string } }) {
  return (
    <div style={{padding: 24}}>
      <h1>/f/{params.campaignId}</h1>
      <p>Το route δουλεύει!</p>
    </div>
  );
}
