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
  Menu,
  X,
  MoreHorizontal,
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
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const isAdvancedActive = activeTab.startsWith('advanced_');

  const handleSelectTab = (tab: TabType) => {
    setShowAdvancedMenu(false);
    setMobileDrawerOpen(false);
    onTabChange(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      <header className="bg-[#09090b]/95 backdrop-blur-md border-b border-zinc-800 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => handleSelectTab('home')}
              className="flex items-center gap-2 text-left select-none"
            >
              <div className="w-7 h-7 rounded bg-zinc-100 flex items-center justify-center text-zinc-950 font-mono font-bold text-sm shadow-sm">
                ts
              </div>
              <span className="font-semibold text-sm tracking-tight text-white font-sans">
                tswebui
              </span>
            </button>

            {/* Mobile health dot */}
            <span
              className={`md:hidden inline-block w-2 h-2 rounded-full ${
                apiHealthy ? 'bg-emerald-400' : 'bg-rose-500'
              }`}
              title={apiHealthy ? 'API Online' : 'API Offline'}
            />
          </div>

          {/* Desktop Primary Tab Navigation */}
          <nav className="hidden md:flex items-center space-x-1 overflow-x-auto no-scrollbar py-1">
            {PRIMARY_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => handleSelectTab(tab.id)}
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
                <span>Advanced</span>
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
                          onClick={() => handleSelectTab(tool.id)}
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

          {/* Desktop Status indicator */}
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

          {/* Mobile Hamburger Menu Button */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white focus:outline-none"
              aria-label="Toggle Navigation Menu"
            >
              {mobileDrawerOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Slide-Over Drawer */}
      <AnimatePresence>
        {mobileDrawerOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 md:hidden bg-black/80 backdrop-blur-sm flex flex-col justify-end"
            onClick={() => setMobileDrawerOpen(false)}
          >
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 26, stiffness: 280 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-zinc-900 border-t border-zinc-800 rounded-t-3xl p-5 max-h-[80vh] overflow-y-auto space-y-5 shadow-2xl safe-area-inset-bottom"
            >
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 rounded bg-zinc-100 flex items-center justify-center text-zinc-950 font-mono font-bold text-xs">
                    ts
                  </div>
                  <h3 className="text-sm font-bold text-white">All Platform Navigation</h3>
                </div>
                <button
                  onClick={() => setMobileDrawerOpen(false)}
                  className="p-1.5 rounded-full bg-zinc-800 text-zinc-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Core Tools */}
              <div className="space-y-1.5">
                <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500 font-semibold px-2">
                  Core Tools
                </span>
                <div className="grid grid-cols-1 gap-1">
                  {PRIMARY_TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => handleSelectTab(tab.id)}
                        className={`flex items-center space-x-3 px-3.5 py-3 rounded-xl text-left transition-all ${
                          isActive
                            ? 'bg-blue-600 text-white font-semibold shadow-md'
                            : 'bg-zinc-950/60 text-zinc-300 hover:bg-zinc-800'
                        }`}
                      >
                        <Icon className="w-4 h-4 shrink-0" />
                        <span className="text-xs">{tab.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Advanced Tools */}
              <div className="space-y-1.5 pt-2 border-t border-zinc-800/80">
                <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500 font-semibold px-2">
                  Technical & Advanced
                </span>
                <div className="grid grid-cols-1 gap-1">
                  {ADVANCED_TOOLS.map((tool) => {
                    const ToolIcon = tool.icon;
                    const isActive = activeTab === tool.id;
                    return (
                      <button
                        key={tool.id}
                        onClick={() => handleSelectTab(tool.id)}
                        className={`flex items-center space-x-3 px-3.5 py-3 rounded-xl text-left transition-all ${
                          isActive
                            ? 'bg-zinc-800 text-white font-semibold'
                            : 'bg-zinc-950/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                        }`}
                      >
                        <ToolIcon className="w-4 h-4 shrink-0" />
                        <span className="text-xs">{tool.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Fixed Bottom Navigation Bar (Thumb Friendly) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#09090b]/95 backdrop-blur-xl border-t border-zinc-800/90 px-1 py-1 flex items-center justify-around shadow-2xl safe-area-inset-bottom">
        <button
          onClick={() => handleSelectTab('home')}
          className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-lg ${
            activeTab === 'home' ? 'text-blue-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <Home className="w-4 h-4 mb-0.5" />
          <span className="text-[10px]">Home</span>
        </button>

        <button
          onClick={() => handleSelectTab('scan')}
          className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-lg ${
            activeTab === 'scan' ? 'text-blue-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <Scan className="w-4 h-4 mb-0.5" />
          <span className="text-[10px]">Scan</span>
        </button>

        <button
          onClick={() => handleSelectTab('setups')}
          className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-lg ${
            activeTab === 'setups' ? 'text-blue-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <Layers className="w-4 h-4 mb-0.5" />
          <span className="text-[10px]">Setups</span>
        </button>

        <button
          onClick={() => handleSelectTab('website_builder')}
          className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-lg ${
            activeTab === 'website_builder' ? 'text-blue-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <Globe className="w-4 h-4 mb-0.5" />
          <span className="text-[10px]">Websites</span>
        </button>

        <button
          onClick={() => setMobileDrawerOpen(true)}
          className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-lg ${
            mobileDrawerOpen || isAdvancedActive || activeTab === 'teach' || activeTab === 'teach_pdf' || activeTab === 'results'
              ? 'text-blue-400 font-semibold'
              : 'text-zinc-400'
          }`}
        >
          <MoreHorizontal className="w-4 h-4 mb-0.5" />
          <span className="text-[10px]">More</span>
        </button>
      </nav>
    </>
  );
};
