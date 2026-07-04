'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import axios from 'axios';
import { Check, Copy, CopyCheck, RefreshCcw } from 'lucide-react';
import copy from 'clipboard-copy';
import ImportantLinks from '@/components/ui/ImportantLinks/ImportantLinks';
import { VisaStatusForm } from '@/components/ui/VisaStatusForm/VisaStatusForm';

const apiBaseUrl = process.env.BASE_API_URL;

type SourceKey = 'passtrack' | 'bd' | 'gov';

interface SourceMeta {
  key: SourceKey;
  label: string;
  url: string;
}

const SOURCE_META: Record<SourceKey, SourceMeta> = {
  passtrack: { key: 'passtrack', label: 'Passtrack (IVAC)', url: 'https://www.passtrack.net' },
  bd: { key: 'bd', label: 'Indian Visa — Bangladesh', url: 'https://indianvisa-bangladesh.nic.in' },
  gov: { key: 'gov', label: 'Indian Visa — Official', url: 'https://indianvisaonline.gov.in' },
};

interface TrackData {
  passtrack?: {
    applicant_name?: string;
    received_at_center?: boolean;
    process_initiated?: boolean;
    ready_for_delivery?: boolean;
    delivered_from_center_on?: string | null;
    url?: string;
    processes?: Record<string, string>;
    statuses?: Record<string, string>;
  };
  indianvisa_bangladesh_status_nic_in?: { status?: string; url?: string };
  indianvisa_online_gov_in?: { status?: string; url?: string };
  webfile_info?: unknown;
  pending?: boolean;
}

interface StatusResponse {
  result: unknown[];
  processing_time_seconds: number;
  data: TrackData;
}

interface SourceView {
  key: SourceKey;
  label: string;
  url: string;
  status: string;
  applicant_name?: string;
  pending: boolean;
  passtrack_processes?: Record<string, string>;
  passtrack_statuses?: Record<string, string>;
}

function LoadingRow({ label, url }: { label: string; url: string }) {
  return (
    <div className="my-3 p-3 border dark:border-zinc-700 border-slate-300 rounded-md animate-pulse">
      <div className="flex justify-between items-center">
        <div>
          <p className="text-zinc-500 dark:text-zinc-400 text-sm font-medium">{label}</p>
          <p className="text-zinc-400 dark:text-zinc-500 text-xs">{url}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
          <span className="text-xs text-zinc-400">Checking…</span>
        </div>
      </div>
      <div className="mt-3 space-y-1.5">
        <div className="h-3 bg-zinc-200 dark:bg-zinc-800 rounded w-3/4" />
        <div className="h-3 bg-zinc-200 dark:bg-zinc-800 rounded w-1/2" />
      </div>
    </div>
  );
}

function ProcessTable({
  processes,
  statuses,
}: {
  processes: Record<string, string>;
  statuses: Record<string, string>;
}) {
  const keys = Object.keys(processes).sort((a, b) => Number(a) - Number(b));
  return (
    <table className="w-full mt-2 text-sm border-collapse">
      <thead>
        <tr className="border-b dark:border-zinc-700 border-zinc-300">
          <th className="text-left py-1 px-2 text-zinc-500 dark:text-zinc-400 font-medium text-xs w-8">#</th>
          <th className="text-left py-1 px-2 text-zinc-500 dark:text-zinc-400 font-medium text-xs">Process</th>
          <th className="text-left py-1 px-2 text-zinc-500 dark:text-zinc-400 font-medium text-xs">Status</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((k) => {
          const st = statuses[k];
          const isDone = st === 'Done';
          return (
            <tr key={k} className="border-b dark:border-zinc-800 border-zinc-200">
              <td className="py-1 px-2 text-zinc-500 dark:text-zinc-400">{Number(k) + 1}</td>
              <td className="py-1 px-2 text-zinc-700 dark:text-zinc-200">{processes[k]}</td>
              <td
                className={
                  'py-1 px-2 font-semibold ' +
                  (isDone
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-zinc-600 dark:text-zinc-300')
                }
              >
                {isDone ? `✓ ${st}` : st}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function ResultRow({
  label,
  url,
  status,
  applicant_name,
  pending,
  passtrack_processes,
  passtrack_statuses,
}: SourceView) {
  const done = !pending;
  const hasTable = !!passtrack_processes && Object.keys(passtrack_processes).length > 0;
  const hasContent = !!applicant_name || !!status || hasTable;
  const failed = done && !hasContent;

  return (
    <div
      className={
        'my-3 p-3 border rounded-md ' +
        (failed
          ? 'border-amber-500/40 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/20'
          : done
            ? 'border-green-600/40 dark:border-green-700 bg-green-50 dark:bg-green-950/20'
            : 'border-zinc-300 dark:border-zinc-700 animate-pulse')
      }
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="text-zinc-800 dark:text-zinc-100 text-sm font-semibold">{label}</p>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-500 dark:text-zinc-400 text-xs hover:underline"
          >
            {url}
          </a>
        </div>
        <div className="flex items-center gap-2">
          {failed ? (
            <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
              Unavailable
            </span>
          ) : done ? (
            <Check color="green" size={16} />
          ) : (
            <span className="inline-block w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
          )}
        </div>
      </div>
      {applicant_name && (
        <p className="text-zinc-700 dark:text-zinc-200 text-sm mt-2 font-medium">
          {applicant_name}
        </p>
      )}
      {status && (
        <p
          className="text-zinc-600 dark:text-zinc-300 text-sm mt-1"
          dangerouslySetInnerHTML={{ __html: status.replace(/\n/g, '<br>') }}
        />
      )}
      {hasTable && passtrack_statuses && (
        <ProcessTable processes={passtrack_processes!} statuses={passtrack_statuses} />
      )}
      {failed && (
        <p className="text-amber-700 dark:text-amber-400 text-sm mt-2">
          Couldn't retrieve your status from this source right now. Please check directly
          at the link above, or try again shortly.
        </p>
      )}
    </div>
  );
}

function StatusView({ slug }: { slug: string }) {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [done, setDone] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [copied, setCopied] = useState(false);
  const [startTime] = useState(() => Date.now());

  // This page shows someone's personal visa data looked up by a shareable
  // slug — never let it be indexed, even if a link leaks somewhere public.
  useEffect(() => {
    let meta = document.querySelector('meta[name="robots"]');
    const prevContent = meta?.getAttribute('content') ?? null;
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'robots');
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', 'noindex, nofollow');
    return () => {
      if (prevContent !== null) meta?.setAttribute('content', prevContent);
    };
  }, []);

  useEffect(() => {
    if (!slug) return;
    let timer: ReturnType<typeof setInterval> | undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const r = await axios.get<StatusResponse>(`${apiBaseUrl}/track/${slug}`);
        if (cancelled) return;
        setData(r.data);
        setElapsed((Date.now() - startTime) / 1000);
        if (!r.data?.data?.pending) {
          setDone(true);
          if (timer) clearInterval(timer);
        }
      } catch {
        if (cancelled) return;
        setDone(true);
        if (timer) clearInterval(timer);
      }
    };

    poll();
    timer = setInterval(poll, 1500);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [slug, startTime]);

  const d = data?.data ?? {};
  const sources: SourceView[] = [
    {
      key: 'passtrack',
      label: SOURCE_META.passtrack.label,
      url: SOURCE_META.passtrack.url,
      status: '',
      applicant_name: d.passtrack?.applicant_name ?? '',
      pending: d.pending === true && !d.passtrack?.applicant_name,
      passtrack_processes: d.passtrack?.processes,
      passtrack_statuses: d.passtrack?.statuses,
    },
    {
      key: 'bd',
      label: SOURCE_META.bd.label,
      url: SOURCE_META.bd.url,
      status: d.indianvisa_bangladesh_status_nic_in?.status ?? '',
      pending:
        d.pending === true && !d.indianvisa_bangladesh_status_nic_in?.status,
    },
    {
      key: 'gov',
      label: SOURCE_META.gov.label,
      url: SOURCE_META.gov.url,
      status: d.indianvisa_online_gov_in?.status ?? '',
      pending: d.pending === true && !d.indianvisa_online_gov_in?.status,
    },
  ];

  return (
    <div className="lg:max-w-4xl p-4 mx-auto my-4 rounded-md dark:text-white text-slate-900">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-3 text-sm">
          {!done && (
            <span className="text-zinc-500 dark:text-zinc-400">
              {elapsed.toFixed(1)}s elapsed
            </span>
          )}
          {done && (
            <span className="text-zinc-500 dark:text-zinc-400">
              {data?.processing_time_seconds?.toFixed(1) ?? elapsed.toFixed(1)}s total
            </span>
          )}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              copy(window.location.href);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="flex items-center gap-1 text-zinc-600 dark:text-zinc-300 hover:text-zinc-900"
          >
            {copied ? <CopyCheck size={14} /> : <Copy size={14} />}
            {copied ? 'Copied!' : 'Share'}
          </a>
          <a
            href="/"
            className="flex items-center gap-1 text-zinc-600 dark:text-zinc-300 hover:text-zinc-900"
          >
            <RefreshCcw size={14} /> New
          </a>
        </div>
      </div>

      <div>
        {sources.map(({ key, ...rest }) =>
          rest.pending ? (
            <LoadingRow key={key} label={rest.label} url={rest.url} />
          ) : (
            <ResultRow key={key} {...rest} />
          )
        )}
      </div>
    </div>
  );
}

function HomeContent() {
  const searchParams = useSearchParams();
  const slug = searchParams?.get('slug') ?? null;

  if (slug) {
    return <StatusView slug={slug} />;
  }

  return (
    <>
      <div className="lg:max-w-4xl p-4 mx-auto my-4 rounded-md dark:text-white text-slate-900">
        <div className="py-4">
          <p className="dark:text-zinc-300 text-zinc-600 text-sm">
            Monitor the status of your Indian visa application from various sources.
          </p>
        </div>
        <VisaStatusForm />
      </div>
      <ImportantLinks />
    </>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="p-4">Loading…</div>}>
      <HomeContent />
    </Suspense>
  );
}
