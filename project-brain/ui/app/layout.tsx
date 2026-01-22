import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'Project Brain',
  description: 'AI-powered document analysis and entity management system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto py-8 px-4">
          {children}
        </main>
        <footer className="bg-gray-800 text-white text-center py-4 mt-8">
          <p>&copy; 2024 Project Brain. All rights reserved.</p>
        </footer>
      </body>
    </html>
  );
}
