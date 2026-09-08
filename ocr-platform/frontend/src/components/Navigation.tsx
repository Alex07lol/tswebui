import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  ScanEye,
  Sliders,
  BrainCircuit,
  FileSpreadsheet,
  CheckCircle,
  History,
  Activity,
} from 'lucide-react';

export type TabType =
  | 'overview'
  | 'playground'
  | 'rules'
  | 'trainer'
  | 'results'
  | 'regression'
  | 'audit';

interface NavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  apiHealthy?: boolean;
}

const TABS: Array<{ id: TabType; label: string; icon: React.FC<{ className?: string }> }> = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'playground', label: 'OCR Playground', icon: ScanEye },
  { id: 'rules', label: 'Rule Builder', icon: Sliders },
  { id: 'trainer', label: 'Pattern Trainer', icon: BrainCircuit },
  { id: 'results', label: 'Results & Export', icon: FileSpreadsheet },
  { id: 'regression', label: 'Regression Suite', icon: CheckCircle },
  { id: 'audit', label: 'Audit Logs', icon: History },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
  apiHealthy = true,
}) => {
  return (
    <header className="bg-[#09090b] border-b border-zinc-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-zinc-100 flex items-center justify-center text-zinc-950 font-mono font-bold text-sm select-none">
              ts
            </div>
            <span className="font-semibold text-sm tracking-tight text-white font-sans">
              tswebui
            </span>
          </div>

          <span className="hidden sm:inline-block font-mono text-[10px] text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-800 bg-zinc-900">
            Tesseract OCR
          </span>
        </div>

        {/* Tab Items */}
        <nav className="flex items-center space-x-1 overflow-x-auto no-scrollbar py-1">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors select-none ${
                  isActive ? 'text-white' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>

                {/* Minimal Active Indicator */}
                {isActive && (
                  <motion.div
                    layoutId="activeTabIndicator"
                    className="absolute inset-0 bg-zinc-800/90 rounded-md border border-zinc-700 -z-10"
                    transition={{ type: 'spring', stiffness: 450, damping: 30 }}
                  />
                )}
              </button>
            );
          })}
        </nav>

        {/* Backend Status indicator */}
        <div className="hidden md:flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400 bg-zinc-900/80 px-2 py-1 rounded border border-zinc-800">
            <Activity className="w-3 h-3 text-zinc-400" />
            <span>API:</span>
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                apiHealthy ? 'bg-emerald-400' : 'bg-rose-500'
              }`}
            />
            <span className={apiHealthy ? 'text-zinc-300' : 'text-rose-400'}>
              {apiHealthy ? ':8000' : 'offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
