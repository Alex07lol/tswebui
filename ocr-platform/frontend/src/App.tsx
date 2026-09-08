import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigation, TabType } from './components/Navigation';
import { OverviewView } from './views/OverviewView';
import { OCRPlaygroundView } from './views/OCRPlaygroundView';
import { RuleBuilderView } from './views/RuleBuilderView';
import { PatternTrainerView } from './views/PatternTrainerView';
import { ExtractionResultsView } from './views/ExtractionResultsView';
import { RegressionSuiteView } from './views/RegressionSuiteView';
import { AuditLogsView } from './views/AuditLogsView';
import { api, DocumentItem } from './lib/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedDocForPlayground, setSelectedDocForPlayground] = useState<DocumentItem | null>(null);
  const [initialAnchorForRuleBuilder, setInitialAnchorForRuleBuilder] = useState<string | null>(null);
  const [apiHealthy, setApiHealthy] = useState<boolean>(true);

  // Periodic health check
  useEffect(() => {
    const checkHealth = () => {
      api.getHealth()
        .then(() => setApiHealthy(true))
        .catch(() => setApiHealthy(false));
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigate = (tab: TabType) => {
    setActiveTab(tab);
  };

  const handleSelectDocumentFromOverview = (doc: DocumentItem) => {
    setSelectedDocForPlayground(doc);
    setActiveTab('playground');
  };

  const handleSendTokenToRuleBuilder = (tokenText: string) => {
    setInitialAnchorForRuleBuilder(tokenText);
    setActiveTab('rules');
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex flex-col selection:bg-zinc-800 selection:text-white">
      {/* Top Navigation */}
      <Navigation
        activeTab={activeTab}
        onTabChange={handleNavigate}
        apiHealthy={apiHealthy}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="h-full"
          >
            {activeTab === 'overview' && (
              <OverviewView
                onNavigate={handleNavigate}
                onSelectDocument={handleSelectDocumentFromOverview}
              />
            )}

            {activeTab === 'playground' && (
              <OCRPlaygroundView
                initialDocument={selectedDocForPlayground}
                onSendToRuleBuilder={handleSendTokenToRuleBuilder}
              />
            )}

            {activeTab === 'rules' && (
              <RuleBuilderView initialAnchor={initialAnchorForRuleBuilder} />
            )}

            {activeTab === 'trainer' && <PatternTrainerView />}

            {activeTab === 'results' && <ExtractionResultsView />}

            {activeTab === 'regression' && <RegressionSuiteView />}

            {activeTab === 'audit' && <AuditLogsView />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Minimal Bottom Status Bar */}
      <footer className="border-t border-zinc-900 bg-[#070709] py-3 text-center text-xs font-mono text-zinc-400 select-none">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span>tswebui</span>
            <span>&middot;</span>
            <span>Tesseract OCR Platform</span>
            <span>&middot;</span>
            <span className="text-zinc-400">Declarative Extraction & Pattern Learning</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-zinc-400">
            <span>motion.dev spring physics</span>
            <span>&middot;</span>
            <span>Zero Glassmorphism</span>
            <span>&middot;</span>
            <span className="text-emerald-500 font-medium">Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default App;
