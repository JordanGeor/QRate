// scripts/qr.ts
import path from 'node:path';
import { config } from 'dotenv';
import QRCode from 'qrcode';

// Φόρτωσε .env.local
config({ path: path.resolve(process.cwd(), '.env.local') });

async function run() {
  const campaignId = process.argv[2];
  if (!campaignId) {
    console.error('❌ Χρήση: npm run qr -- <campaignId>');
    process.exit(1);
  }

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  const target = `${appUrl}/f/${campaignId}`;

  // Δημιουργία QR code (PNG και SVG)
  await QRCode.toFile(`qr-${campaignId}.png`, target, { width: 512, margin: 2 });
  await QRCode.toFile(`qr-${campaignId}.svg`, target, { margin: 1 });

  console.log('✅ QR δημιουργήθηκε για:', target);
  console.log(` - qr-${campaignId}.png`);
  console.log(` - qr-${campaignId}.svg`);
}

run().catch((e) => {
  console.error('❌ Σφάλμα QR:', e);
  process.exit(1);
});
