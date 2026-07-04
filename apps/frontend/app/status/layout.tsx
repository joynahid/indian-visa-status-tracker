import { Metadata } from 'next';
import { PropsWithChildren } from 'react';

export const metadata: Metadata = {
  title: 'System Status — Indian Visa Status',
  description: 'Live uptime and health of each Indian visa status data source, checked automatically every 2 hours.',
  alternates: { canonical: '/status' }
};

export default function StatusLayout({ children }: PropsWithChildren) {
  return children;
}
