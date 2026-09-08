import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  api,
  TestSuite,
  TestCase,
  TestRun,
  Configuration,
  DocumentItem,
} from '../lib/api';
import { BKLitGauge } from '../components/bklit/BKLitGauge';
import {
  CheckCircle,
  XCircle,
  Play,
  Plus,
  Clock,
  Layers,
  Check,
  AlertTriangle,
  FileCheck2,
} from 'lucide-react';

export const RegressionSuiteView: React.FC = () => {
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<TestSuite | null>(null);
  const [configs, setConfigs] = useState<Configuration[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');

  const [activeRun, setActiveRun] = useState<TestRun | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Modal: Create Test Suite
  const [showCreateSuiteModal, setShowCreateSuiteModal] = useState(false);
  const [newSuiteName, setNewSuiteName] = useState('');
  const [newSuiteConfigId, setNewSuiteConfigId] = useState('');

  // Modal: Create Test Case
  const [showCreateCaseModal, setShowCreateCaseModal] = useState(false);
  const [newCaseName, setNewCaseName] = useState('');
  const [newCaseDocId, setNewCaseDocId] = useState('');
  const [newCaseExpectedJson, setNewCaseExpectedJson] = useState('{\n  "invoice_number": "INV-2026-00128"\n}');
  const [newCaseValidationMode, setNewCaseValidationMode] = useState('exact');
  const [newCaseIsRegression, setNewCaseIsRegression] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [suitesData, configsData, docsData] = await Promise.all([
        api.listTestSuites(),
        api.listConfigurations(),
        api.listDocuments(0, 50),
      ]);
      setSuites(suitesData);
      if (suitesData.length > 0 && !selectedSuite) {
        setSelectedSuite(suitesData[0]);
      }
      setConfigs(configsData);
      if (configsData.length > 0 && !newSuiteConfigId) {
        setNewSuiteConfigId(configsData[0].id);
      }
      setDocuments(docsData);
      if (docsData.length > 0 && !newCaseDocId) {
        setNewCaseDocId(docsData[0].id);
      }
    } catch (err) {
      console.error('Failed to load regression test data:', err);
    }
  };

  const handleRunSuite = async () => {
    if (!selectedSuite) return;
    setIsRunning(true);
    setActiveRun(null);
    try {
      const run = await api.runTestSuite(selectedSuite.id, selectedVersionId || undefined);
      // Wait for test run
      let currentRun = run;
      let attempts = 0;
      while (currentRun.status === 'running' || currentRun.status === 'pending') {
        if (attempts++ > 20) break;
        await new Promise((r) => setTimeout(r, 600));
        currentRun = await api.getTestRun(run.id);
      }
      setActiveRun(currentRun);
    } catch (err: any) {
      alert(`Test run failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleCreateSuite = async () => {
    if (!newSuiteName || !newSuiteConfigId) return;
    try {
      const created = await api.createTestSuite({
        name: newSuiteName,
        configuration_id: newSuiteConfigId,
      });
      setShowCreateSuiteModal(false);
      setNewSuiteName('');
      await loadData();
      setSelectedSuite(created);
    } catch (err: any) {
      alert(`Create suite failed: ${err.message}`);
    }
  };

  const handleCreateCase = async () => {
    if (!selectedSuite || !newCaseName || !newCaseDocId) return;
    try {
      let parsedExpected = {};
      try {
        parsedExpected = JSON.parse(newCaseExpectedJson);
      } catch {
        alert('Invalid JSON in expected values');
        return;
      }
      await api.addTestCase(selectedSuite.id, {
        name: newCaseName,
        document_id: newCaseDocId,
        expected_values: parsedExpected,
        validation_mode: newCaseValidationMode,
        is_regression: newCaseIsRegression,
      });
      setShowCreateCaseModal(false);
      setNewCaseName('');
      await loadData();
    } catch (err: any) {
      alert(`Create case failed: ${err.message}`);
    }
  };

  // Parse results_json if present
  let runDetails: any[] = [];
  if (activeRun?.results_json) {
    try {
      runDetails = JSON.parse(activeRun.results_json);
    } catch {
      runDetails = [];
    }
  }

  const passRate = activeRun?.pass_rate ?? (activeRun?.total_cases ? activeRun.passed_cases / activeRun.total_cases : 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 font-sans">
            Automated Regression Testing Suite
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Continuous verification: Ensure new configuration changes do not break known historical documents.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateSuiteModal(true)}
            className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs font-mono text-zinc-200 transition-colors flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Suite</span>
          </button>

          <button
            onClick={handleRunSuite}
            disabled={!selectedSuite || isRunning}
            className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50 transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Executing Suite...' : 'Run Test Suite'}</span>
          </button>
        </div>
      </div>

      {/* Grid: Suites sidebar & Main results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Suites & Cases List (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3">
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              Test Suites ({suites.length})
            </h3>

            <div className="space-y-1">
              {suites.length === 0 ? (
                <div className="text-xs text-zinc-400 font-mono py-2">
                  No test suites found. Click "+ New Suite" above.
                </div>
              ) : (
                suites.map((s) => {
                  const isSelected = selectedSuite?.id === s.id;
                  return (
                    <div
                      key={s.id}
                      onClick={() => {
                        setSelectedSuite(s);
                        setActiveRun(null);
                      }}
                      className={`p-2.5 rounded cursor-pointer border text-xs transition-colors flex items-center justify-between ${
                        isSelected
                          ? 'bg-zinc-800 border-zinc-600 text-white'
                          : 'bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-zinc-200">{s.name}</div>
                        <div className="text-[10px] text-zinc-400 font-mono">
                          {s.cases?.length || 0} registered test cases
                        </div>
                      </div>
                      <FileCheck2 className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Test Cases inside selected suite */}
          {selectedSuite && (
            <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                  Test Cases ({selectedSuite.cases?.length || 0})
                </h3>
                <button
                  onClick={() => setShowCreateCaseModal(true)}
                  className="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-mono text-[11px]"
                >
                  + Add Case
                </button>
              </div>

              <div className="max-h-60 overflow-y-auto space-y-1 pr-1 font-mono">
                {(selectedSuite.cases?.length || 0) === 0 ? (
                  <div className="text-zinc-400 text-xs py-2">No cases in this suite yet.</div>
                ) : (
                  selectedSuite.cases?.map((c) => (
                    <div
                      key={c.id}
                      className="p-2 rounded bg-zinc-900/60 border border-zinc-800 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-zinc-200 truncate">{c.name}</span>
                        <span className="text-[10px] text-zinc-400 bg-zinc-800 px-1 rounded">
                          {c.validation_mode}
                        </span>
                      </div>
                      {c.is_regression && (
                        <span className="inline-block text-[10px] text-amber-400">
                          &bull; Regression Test
                        </span>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: Test Execution Outcome & Live Gauge (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {activeRun ? (
            <>
              {/* Pass Rate Gauge Card */}
              <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                    Test Run Results: {activeRun.status.toUpperCase()}
                  </h3>
                  <p className="text-xs text-zinc-400 font-mono mt-0.5">
                    Suite ID: {activeRun.suite_id.slice(0, 8)}... &middot; Total Cases: {activeRun.total_cases}
                  </p>

                  <div className="flex items-center gap-4 mt-4 text-xs font-mono">
                    <div className="flex items-center gap-1.5 text-emerald-400">
                      <CheckCircle className="w-4 h-4" />
                      <span>{activeRun.passed_cases} Passed</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-rose-400">
                      <XCircle className="w-4 h-4" />
                      <span>{activeRun.failed_cases} Failed</span>
                    </div>
                  </div>
                </div>

                <div className="py-2">
                  <BKLitGauge
                    value={passRate}
                    size={130}
                    strokeWidth={9}
                    label="Regression Pass Rate"
                    sublabel="Score"
                    color={passRate === 1 ? 'emerald' : passRate >= 0.7 ? 'amber' : 'rose'}
                  />
                </div>
              </div>

              {/* Case-by-case comparison breakdown */}
              <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 space-y-3">
                <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                  Test Case Outcomes & Value Diffs
                </h4>

                {runDetails.length === 0 ? (
                  <div className="text-xs font-mono text-zinc-400 py-4">
                    All {activeRun.total_cases} cases executed cleanly.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {runDetails.map((detail: any, idx: number) => {
                      const isPass = detail.status === 'passed';
                      return (
                        <div
                          key={idx}
                          className={`p-3 rounded border text-xs font-mono space-y-1.5 ${
                            isPass
                              ? 'bg-[#101712] border-emerald-900/60'
                              : 'bg-[#1a1013] border-rose-900/60'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-zinc-200">
                              Case: {detail.case_name || detail.case_id}
                            </span>
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                isPass ? 'text-emerald-400 bg-emerald-950/40' : 'text-rose-400 bg-rose-950/40'
                              }`}
                            >
                              {detail.status?.toUpperCase()}
                            </span>
                          </div>

                          {detail.diff && (
                            <div className="p-2 bg-black/40 rounded border border-zinc-800 text-[11px] text-zinc-300 space-y-0.5">
                              <div>Expected: <span className="text-emerald-400">{JSON.stringify(detail.diff.expected)}</span></div>
                              <div>Actual: <span className="text-rose-400">{JSON.stringify(detail.diff.actual)}</span></div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-12 text-center text-zinc-400 text-xs font-mono border-dashed">
              Select a test suite from the left and click "Run Test Suite" to execute regression verification.
            </div>
          )}
        </div>
      </div>

      {/* Modal: Create Suite */}
      <AnimatePresence>
        {showCreateSuiteModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0e0e12] border border-zinc-800 rounded-lg max-w-md w-full p-6 space-y-4 shadow-xl text-xs"
            >
              <h3 className="text-base font-semibold text-white font-sans">
                Create Regression Test Suite
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Suite Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Standard Invoices Regression"
                    value={newSuiteName}
                    onChange={(e) => setNewSuiteName(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Target Configuration</label>
                  <select
                    value={newSuiteConfigId}
                    onChange={(e) => setNewSuiteConfigId(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  >
                    {configs.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowCreateSuiteModal(false)}
                  className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateSuite}
                  disabled={!newSuiteName}
                  className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold disabled:opacity-50"
                >
                  Create Suite
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Create Test Case */}
      <AnimatePresence>
        {showCreateCaseModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0e0e12] border border-zinc-800 rounded-lg max-w-lg w-full p-6 space-y-4 shadow-xl text-xs"
            >
              <h3 className="text-base font-semibold text-white font-sans">
                Add Test Case to "{selectedSuite?.name}"
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Case Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Invoice #00128 Ground Truth"
                    value={newCaseName}
                    onChange={(e) => setNewCaseName(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>

                <div>
                  <label className="text-zinc-400 block mb-1">Target Document</label>
                  <select
                    value={newCaseDocId}
                    onChange={(e) => setNewCaseDocId(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  >
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.original_filename}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-zinc-400 block mb-1">Validation Mode</label>
                  <select
                    value={newCaseValidationMode}
                    onChange={(e) => setNewCaseValidationMode(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  >
                    <option value="exact">exact — Strict character match</option>
                    <option value="regex">regex — Match regular expression</option>
                    <option value="numeric_tolerance">numeric_tolerance — Float tolerance (&plusmn;0.01)</option>
                    <option value="date_equivalent">date_equivalent — Flexible date parser equivalence</option>
                  </select>
                </div>

                <div>
                  <label className="text-zinc-400 block mb-1">Expected Values (JSON dictionary)</label>
                  <textarea
                    rows={4}
                    value={newCaseExpectedJson}
                    onChange={(e) => setNewCaseExpectedJson(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded p-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="is-reg-case"
                    checked={newCaseIsRegression}
                    onChange={(e) => setNewCaseIsRegression(e.target.checked)}
                    className="accent-white cursor-pointer"
                  />
                  <label htmlFor="is-reg-case" className="text-zinc-300 font-medium cursor-pointer">
                    Flag as Permanent Regression Test
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowCreateCaseModal(false)}
                  className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCase}
                  disabled={!newCaseName || !newCaseDocId}
                  className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold disabled:opacity-50"
                >
                  Save Case
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
