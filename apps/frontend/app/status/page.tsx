'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { CheckCircle2, HelpCircle, XCircle } from 'lucide-react';

const apiBaseUrl = process.env.BASE_API_URL;

type SourceKey = 'passtrack' | 'indian_gov' | 'bd_nic';

interface SourceStatus {
  up: boolean | null;
  last_checked: string | null;
  latency_ms: number | null;
  error: string | null;
  uptime_percent: number | null;
  sample_size: number;
}

interface SummaryResponse {
  sources: Record<SourceKey, SourceStatus>;
}

const SOURCE_KEYS: SourceKey[] = ['passtrack', 'indian_gov', 'bd_nic'];

const SOURCE_LABELS: Record<SourceKey, string> = {
  passtrack: 'Passtrack (IVAC)',
  indian_gov: 'Indian Visa — Official',
  bd_nic: 'Indian Visa — Bangladesh',
};

function timeAgo(iso: string | null): string {
  if (!iso) return 'never';
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function StatusBadge({ up }: { up: boolean | null }) {
  if (up === null) {
    return (
      <span className="flex items-center gap-1 text-zinc-400 text-xs font-medium">
        <HelpCircle size={14} /> No data
      </span>
    );
  }
  return up ? (
    <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-xs font-medium">
      <CheckCircle2 size={14} /> Operational
    </span>
  ) : (
    <span className="flex items-center gap-1 text-red-600 dark:text-red-400 text-xs font-medium">
      <XCircle size={14} /> Down
    </span>
  );
}

function SourceCard({ name, status }: { name: SourceKey; status: SourceStatus }) {
  return (
    <div
      className={
        'p-4 border rounded-md ' +
        (status.up === false
          ? 'border-red-600/40 bg-red-50 dark:bg-red-950/20'
          : status.up === true
            ? 'border-green-600/40 bg-green-50 dark:bg-green-950/20'
            : 'border-zinc-300 dark:border-zinc-700')
      }
    >
      <div className="flex justify-between items-start mb-2">
        <p className="text-zinc-800 dark:text-zinc-100 text-sm font-semibold">
          {SOURCE_LABELS[name]}
        </p>
        <StatusBadge up={status.up} />
      </div>
      <div className="text-xs text-zinc-500 dark:text-zinc-400 space-y-0.5">
        <p>
          Uptime: {status.uptime_percent !== null ? `${status.uptime_percent}%` : '—'}{' '}
          ({status.sample_size} checks)
        </p>
        <p>Latency: {status.latency_ms !== null ? `${status.latency_ms}ms` : '—'}</p>
        <p>Last checked: {timeAgo(status.last_checked)}</p>
        {status.error && <p className="text-red-500">{status.error}</p>}
      </div>
    </div>
  );
}

export default function StatusPage() {
  const [data, setData] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const fetchOnce = () => axios.get<SummaryResponse>(`${apiBaseUrl}/status/summary`);

    const load = async () => {
      // Retry a couple times before giving up. Any cold backend can transiently
      // fail the very first request after being idle.
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const r = await fetchOnce();
          if (!cancelled) {
            setData(r.data);
            setError(false);
          }
          return;
        } catch {
          if (attempt < 2) await new Promise((res) => setTimeout(res, 1500 * (attempt + 1)));
        }
      }
      if (!cancelled) setError(true);
    };

    load();
    const timer = setInterval(load, 60000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="lg:max-w-4xl p-4 mx-auto my-4 rounded-md dark:text-white text-slate-900">
      <h3 className="text-2xl font-medium mb-4">System Status</h3>

      {error && (
        <p className="text-red-500 text-sm mb-4">
          {data
            ? 'Could not refresh status data — showing the last known result.'
            : 'Failed to load status data. Will retry shortly.'}
        </p>
      )}
      {!data && !error && (
        <p className="text-zinc-500 dark:text-zinc-400 text-sm">Loading…</p>
      )}

      {data && (
        <div className="grid gap-3 sm:grid-cols-3">
          {SOURCE_KEYS.map((key) => (
            <SourceCard key={key} name={key} status={data.sources[key]} />
          ))}
        </div>
      )}
    </div>
  );
}
