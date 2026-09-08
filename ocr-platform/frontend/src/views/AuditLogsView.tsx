import React, { useState, useEffect } from 'react';
import { api, AuditLog } from '../lib/api';
import { History, ShieldCheck, Activity, RefreshCw, Server, Cpu, Database } from 'lucide-react';

export const AuditLogsView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [health, setHealth] = useState<{ status: string; version: string; ocr_provider: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [logsData, healthData] = await Promise.all([
        api.listAuditLogs(100).catch(() => []),
        api.getHealth().catch(() => null),
      ]);
      setLogs(logsData);
      setHealth(healthData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 font-sans">
            Audit Logs & System Observability
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Immutable chronological audit log of all system actions, user sessions, OCR jobs, and extraction events.
          </p>
        </div>

        <button
          onClick={loadData}
          className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs font-mono text-zinc-200 flex items-center gap-1.5 transition-colors self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* System Health Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 bg-[#0c0c0e] border border-zinc-800 rounded-lg flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
            <Server className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-xs text-zinc-400 font-mono uppercase tracking-wider">FastAPI Server</div>
            <div className="text-sm font-semibold text-zinc-100 font-mono">
              {health?.status === 'ok' ? 'Healthy (v' + health.version + ')' : 'Connecting...'}
            </div>
          </div>
        </div>

        <div className="p-4 bg-[#0c0c0e] border border-zinc-800 rounded-lg flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
            <Cpu className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-xs text-zinc-400 font-mono uppercase tracking-wider">Default OCR Provider</div>
            <div className="text-sm font-semibold text-zinc-100 font-mono">
              {health?.ocr_provider || 'Tesseract OCR'}
            </div>
          </div>
        </div>

        <div className="p-4 bg-[#0c0c0e] border border-zinc-800 rounded-lg flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
            <Database className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-xs text-zinc-400 font-mono uppercase tracking-wider">Audit Security</div>
            <div className="text-sm font-semibold text-zinc-100 font-mono">
              SHA-256 / Append-Only
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg overflow-hidden">
        <div className="px-5 py-3.5 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-zinc-400" />
            <h3 className="text-sm font-semibold text-zinc-100 font-sans">
              Recorded System Events ({logs.length})
            </h3>
          </div>
          <span className="text-xs text-zinc-400 font-mono">Live Ingestion</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0e0e12] border-b border-zinc-800 text-zinc-400 text-[11px] uppercase tracking-wider">
              <tr>
                <th className="px-4 py-2.5">Timestamp</th>
                <th className="px-4 py-2.5">Event Type</th>
                <th className="px-4 py-2.5">Resource Type</th>
                <th className="px-4 py-2.5">Resource ID</th>
                <th className="px-4 py-2.5">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-400 text-xs">
                    No audit records registered yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  let parsedDetails = log.details_json;
                  try {
                    if (log.details_json) {
                      parsedDetails = JSON.stringify(JSON.parse(log.details_json));
                    }
                  } catch {}

                  return (
                    <tr key={log.id} className="hover:bg-zinc-900/30 transition-colors">
                      <td className="px-4 py-2.5 text-zinc-400 whitespace-nowrap">
                        {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'now'}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="font-semibold text-zinc-200 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">
                          {log.event_type}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-zinc-400">{log.resource_type || '-'}</td>
                      <td className="px-4 py-2.5 text-zinc-400">
                        {log.resource_id ? `${log.resource_id.slice(0, 8)}...` : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-zinc-400 truncate max-w-xs font-mono text-[11px]">
                        {parsedDetails || '-'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
