import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigation, TabType } from './components/Navigation';
import { HomeView } from './views/HomeView';
import { ScanDocumentsView } from './views/ScanDocumentsView';
import { TeachFromExamplesView } from './views/TeachFromExamplesView';
import { MySetupsView } from './views/MySetupsView';
import { CreateSetupView } from './views/CreateSetupView';
import { SetupDetailView } from './views/SetupDetailView';
import { ResultsView } from './views/ResultsView';
import { OCRPlaygroundView } from './views/OCRPlaygroundView';
import { RuleBuilderView } from './views/RuleBuilderView';
import { PatternTrainerView } from './views/PatternTrainerView';
import { RegressionSuiteView } from './views/RegressionSuiteView';
import { ActivityView } from './views/ActivityView';
import { WebsiteBuilderView } from './views/WebsiteBuilderView';
import { PDFFieldMapperView } from './views/PDFFieldMapperView';
import { api, DocumentItem } from './lib/api';
import { SetupItem } from './lib/setupApi';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType | 'create_setup' | 'setup_detail'>('home');
  const [activeSetupId, setActiveSetupId] = useState<string | null>(null);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
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

  const handleNavigate = (tab: TabType | 'create_setup') => {
    setActiveTab(tab);
  };

  const handleOpenSetupDetail = (setup: SetupItem) => {
    setActiveSetupId(setup.id);
    setActiveTab('setup_detail');
  };

  const handleScanSetup = (setup: SetupItem | string) => {
    const sId = typeof setup === 'string' ? setup : setup.id;
    setActiveSetupId(sId);
    setActiveTab('scan');
  };

  const handleViewResults = (setup: SetupItem | string, docId?: string) => {
    const sId = typeof setup === 'string' ? setup : setup.id;
    setActiveSetupId(sId);
    if (docId) setActiveDocumentId(docId);
    setActiveTab('results');
  };

  const handleSendTokenToRuleBuilder = (tokenText: string) => {
    setInitialAnchorForRuleBuilder(tokenText);
    setActiveTab('advanced_rules');
  };

  const handleOpenAdvancedRuleEditor = (configId: string, fieldId?: string) => {
    setActiveTab('advanced_rules');
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex flex-col selection:bg-zinc-800 selection:text-white">
      {/* Top Navigation */}
      <Navigation
        activeTab={activeTab === 'create_setup' || activeTab === 'setup_detail' ? 'setups' : activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        apiHealthy={apiHealthy}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-3 sm:px-6 py-4 sm:py-6 pb-24 md:pb-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="h-full"
          >
            {/* Primary Consumer Views */}
            {activeTab === 'home' && (
              <HomeView onNavigate={handleNavigate} />
            )}

            {activeTab === 'scan' && (
              <ScanDocumentsView
                initialSetupId={activeSetupId}
                onViewResults={(setupId, docId) => {
                  setActiveSetupId(setupId);
                  setActiveDocumentId(docId);
                  setActiveTab('results');
                }}
              />
            )}

            {activeTab === 'teach' && (
              <TeachFromExamplesView
                onSetupSaved={(setupId) => {
                  setActiveSetupId(setupId);
                  setActiveTab('setup_detail');
                }}
              />
            )}

            {activeTab === 'teach_pdf' && (
              <PDFFieldMapperView />
            )}

            {activeTab === 'setups' && (
              <MySetupsView
                onCreateNew={() => setActiveTab('create_setup')}
                onScanSetup={handleScanSetup}
                onEditSetup={handleOpenSetupDetail}
                onViewResults={handleViewResults}
              />
            )}

            {activeTab === 'website_builder' && (
              <WebsiteBuilderView />
            )}

            {activeTab === 'create_setup' && (
              <CreateSetupView
                onCancel={() => setActiveTab('setups')}
                onSaved={(setupId) => {
                  setActiveSetupId(setupId);
                  setActiveTab('setup_detail');
                }}
              />
            )}

            {activeTab === 'setup_detail' && activeSetupId && (
              <SetupDetailView
                setupId={activeSetupId}
                onBack={() => setActiveTab('setups')}
                onScan={(sId) => {
                  setActiveSetupId(sId);
                  setActiveTab('scan');
                }}
                onOpenAdvancedRuleEditor={handleOpenAdvancedRuleEditor}
              />
            )}

            {activeTab === 'results' && (
              <ResultsView
                initialSetupId={activeSetupId}
                initialDocumentId={activeDocumentId}
              />
            )}

            {/* Advanced Tools Views */}
            {activeTab === 'advanced_inspector' && (
              <OCRPlaygroundView
                initialDocument={selectedDocForPlayground}
                onSendToRuleBuilder={handleSendTokenToRuleBuilder}
              />
            )}

            {activeTab === 'advanced_rules' && (
              <RuleBuilderView initialAnchor={initialAnchorForRuleBuilder} />
            )}

            {activeTab === 'advanced_patterns' && (
              <PatternTrainerView />
            )}

            {activeTab === 'advanced_regression' && (
              <RegressionSuiteView />
            )}

            {activeTab === 'advanced_activity' && (
              <ActivityView onNavigateTab={(t) => setActiveTab(t)} />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Minimal Bottom Status Bar */}
      <footer className="border-t border-zinc-900 bg-[#070709] py-3 text-center text-xs font-mono text-zinc-400 select-none">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span>tswebui</span>
            <span>&middot;</span>
            <span>OCR Platform</span>
            <span>&middot;</span>
            <span className="text-zinc-500">Consumer Setups & Declarative Extraction</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-zinc-500">
            <span>motion.dev springs</span>
            <span>&middot;</span>
            <span>Solid Zinc Surfaces</span>
            <span>&middot;</span>
            <span className="text-emerald-500 font-medium">Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default App;
