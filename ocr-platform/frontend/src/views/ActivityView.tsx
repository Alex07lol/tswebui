import React, { useState } from 'react';
import { AuditLogsView } from './AuditLogsView';
import { OverviewView } from './OverviewView';
import { Activity, History, Server } from 'lucide-react';

interface ActivityViewProps {
  onNavigateTab?: (tab: any) => void;
}

export const ActivityView: React.FC<ActivityViewProps> = ({ onNavigateTab }) => {
  const [subTab, setSubTab] = useState<'activity' | 'system'>('activity');

  return (
    <div className="space-y-6 font-sans">
      {/* View Header with Sub-tab Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-zinc-100">
            Activity & System
          </h1>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Audit logs, system events, server observability, and throughput metrics.
          </p>
        </div>

        <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 text-xs font-mono">
          <button
            onClick={() => setSubTab('activity')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
              subTab === 'activity'
                ? 'bg-zinc-800 text-white font-semibold'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Activity Logs</span>
          </button>
          <button
            onClick={() => setSubTab('system')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
              subTab === 'system'
                ? 'bg-zinc-800 text-white font-semibold'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>System Metrics</span>
          </button>
        </div>
      </div>

      {/* Render selected view */}
      {subTab === 'activity' ? (
        <AuditLogsView />
      ) : (
        <OverviewView onNavigate={onNavigateTab || (() => {})} />
      )}
    </div>
  );
};
