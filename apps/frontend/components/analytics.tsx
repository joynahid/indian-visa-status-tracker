'use client';

import { useEffect } from 'react';

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

// Fires a page_view with the query string stripped, so slugs (lookup keys for
// someone's personal visa data) never reach Google Analytics.
export default function AnalyticsPageView() {
  useEffect(() => {
    window.gtag?.('event', 'page_view', {
      page_path: window.location.pathname,
      page_location: window.location.origin + window.location.pathname,
    });
  }, []);

  return null;
}
