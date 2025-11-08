// src/app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'QRate',
  description: 'Εύκολη διαχείριση feedback & reviews για επιχειρήσεις.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="el">
      <body className="bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  );
}
