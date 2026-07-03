import { Metadata } from 'next';
import Footer from '@/components/ui/Footer';
import Navbar from '@/components/ui/Navbar';
import { ToastContainer } from 'react-toastify';

import { PropsWithChildren } from 'react';

import 'styles/main.css';
import 'react-toastify/dist/ReactToastify.css';
import { GoogleTagManager } from '@next/third-parties/google';

import ReactQueryProvider from '@/components/provider';
import { Providers } from '@/components/themeprovider';
import GoogleAdsense from '@/components/googlead';

const meta = {
  title: 'Indian Visa Status',
  description: 'Check Your Indian Visa Status in 2 Seconds!',
  cardImage: '/og.png',
  robots: 'follow, index',
  favicon: '/favicon.ico'
};

export async function generateMetadata(): Promise<Metadata> {
  return {
    metadataBase: new URL('https://track.easyindianvisa.com'),
    title: meta.title,
    description: meta.description,
    referrer: 'origin-when-cross-origin',
    keywords: ['Indian', 'Visa', 'IVAC', 'Visa Status', 'Visa Application', 'Track Indian Visa', 'Tracking', "Indian"],
    authors: [{ name: 'Indian Visa Status', url: 'https://track.easyindianvisa.com' }],
    creator: 'Indian Visa Status',
    publisher: 'Indian Visa Status',
    robots: meta.robots,
    icons: { icon: meta.favicon },
    openGraph: {
      title: meta.title,
      description: meta.description,
      images: [meta.cardImage],
      type: 'website',
      siteName: meta.title
    },
    twitter: {
      card: 'summary_large_image',
      site: meta.title,
      creator: meta.title,
      title: meta.title,
      description: meta.description,
      images: [meta.cardImage]
    }
  };
}

export default async function RootLayout({ children }: PropsWithChildren) {
  const gtag = 'G-P16Y2TPP5S';

  return (
    <html lang="en">
      <GoogleTagManager gtmId={gtag} />
      <body className="dark:bg-black loading">
        <Providers>
          <Navbar />
          <ReactQueryProvider>
            <main
              id="skip"
              className="min-h-[calc(86vh-4rem)] md:min-h[calc(100dvh-5rem)]"
            >
              {children}
            </main>
          </ReactQueryProvider>
          <Footer />
          <ToastContainer />
        </Providers>
        <GoogleAdsense />
      </body>
    </html>
  );
}
