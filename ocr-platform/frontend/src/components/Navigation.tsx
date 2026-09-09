import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Scan,
  Sparkles,
  Layers,
  FileCheck2,
  ChevronDown,
  ChevronUp,
  ScanEye,
  Sliders,
  BrainCircuit,
  CheckCircle,
  Activity,
  Wrench,
  MousePointerClick,
  Globe,
} from 'lucide-react';

export type TabType =
  | 'home'
  | 'scan'
  | 'teach'
  | 'teach_pdf'
  | 'setups'
  | 'website_builder'
  | 'results'
  | 'advanced_inspector'
  | 'advanced_rules'
  | 'advanced_patterns'
  | 'advanced_regression'
  | 'advanced_activity';

interface NavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  apiHealthy?: boolean;
}

const PRIMARY_TABS: Array<{ id: TabType; label: string; icon: React.FC<{ className?: string }> }> = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'scan', label: 'Scan Documents', icon: Scan },
  { id: 'teach', label: 'Teach From Examples', icon: Sparkles },
  { id: 'teach_pdf', label: 'Teach From PDF', icon: MousePointerClick },
  { id: 'setups', label: 'My Setups', icon: Layers },
  { id: 'website_builder', label: 'Website Builder', icon: Globe },
  { id: 'results', label: 'Results', icon: FileCheck2 },
];

const ADVANCED_TOOLS: Array<{ id: TabType; label: string; icon: React.FC<{ className?: string }> }> = [
  { id: 'advanced_inspector', label: 'OCR Inspector', icon: ScanEye },
  { id: 'advanced_rules', label: 'Advanced Rule Editor', icon: Sliders },
  { id: 'advanced_patterns', label: 'Pattern Analysis', icon: BrainCircuit },
  { id: 'advanced_regression', label: 'Test & Regression', icon: CheckCircle },
  { id: 'advanced_activity', label: 'Activity & System', icon: Activity },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
  apiHealthy = true,
}) => {
  const [showAdvancedMenu, setShowAdvancedMenu] = useState(false);
  const isAdvancedActive = activeTab.startsWith('advanced_');

  return (
    <header className="bg-[#09090b] border-b border-zinc-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onTabChange('home')}
            className="flex items-center gap-2 text-left select-none"
          >
            <div className="w-7 h-7 rounded bg-zinc-100 flex items-center justify-center text-zinc-950 font-mono font-bold text-sm">
              ts
            </div>
            <span className="font-semibold text-sm tracking-tight text-white font-sans">
              tswebui
            </span>
          </button>
        </div>

        {/* Primary Tab Navigation */}
        <nav className="flex items-center space-x-1 overflow-x-auto no-scrollbar py-1">
          {PRIMARY_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => {
                  setShowAdvancedMenu(false);
                  onTabChange(tab.id);
                }}
                className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors select-none ${
                  isActive ? 'text-white' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>

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

          {/* Advanced Tools Dropdown Trigger */}
          <div className="relative">
            <button
              onClick={() => setShowAdvancedMenu(!showAdvancedMenu)}
              className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors select-none ${
                isAdvancedActive
                  ? 'text-zinc-100 bg-zinc-800/80 border border-zinc-700'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60'
              }`}
            >
              <Wrench className="w-3.5 h-3.5" />
              <span>Advanced Tools</span>
              {showAdvancedMenu ? (
                <ChevronUp className="w-3 h-3 text-zinc-400" />
              ) : (
                <ChevronDown className="w-3 h-3 text-zinc-400" />
              )}
            </button>

            <AnimatePresence>
              {showAdvancedMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                  className="absolute right-0 mt-2 w-56 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl p-1.5 z-50 text-xs font-mono space-y-0.5"
                >
                  <div className="px-2.5 py-1 text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">
                    Technical Tools
                  </div>
                  {ADVANCED_TOOLS.map((tool) => {
                    const ToolIcon = tool.icon;
                    const isSelected = activeTab === tool.id;
                    return (
                      <button
                        key={tool.id}
                        onClick={() => {
                          setShowAdvancedMenu(false);
                          onTabChange(tool.id);
                        }}
                        className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-left transition-colors ${
                          isSelected
                            ? 'bg-zinc-800 text-white font-semibold'
                            : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
                        }`}
                      >
                        <ToolIcon className="w-3.5 h-3.5 shrink-0" />
                        <span>{tool.label}</span>
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </nav>

        {/* Backend Status indicator */}
        <div className="hidden lg:flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400 bg-zinc-900/80 px-2.5 py-1 rounded border border-zinc-800">
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                apiHealthy ? 'bg-emerald-400' : 'bg-rose-500'
              }`}
            />
            <span>OCR Engine: Online</span>
          </div>
        </div>
      </div>
    </header>
  );
};
