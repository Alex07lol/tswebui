import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  api,
  Dataset,
  DiscoveryRun,
  DocumentCluster,
  PatternProposal,
  DocumentItem,
} from '../lib/api';
import { BKLitClusterBar } from '../components/bklit/BKLitClusterBar';
import {
  BrainCircuit,
  Plus,
  Play,
  CheckCircle2,
  XCircle,
  Sparkles,
  FileText,
  RefreshCw,
  Sliders,
  Layers,
  Check,
} from 'lucide-react';
import { getConfidenceBadge } from '../lib/utils';

export const PatternTrainerView: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [runs, setRuns] = useState<DiscoveryRun[]>([]);
  const [activeRun, setActiveRun] = useState<DiscoveryRun | null>(null);
  const [proposals, setProposals] = useState<PatternProposal[]>([]);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  const [isRunning, setIsRunning] = useState(false);
  const [isGeneratingConfig, setIsGeneratingConfig] = useState(false);
  const [generatedConfigSuccess, setGeneratedConfigSuccess] = useState<string | null>(null);

  // Modal to create dataset
  const [showCreateDatasetModal, setShowCreateDatasetModal] = useState(false);
  const [newDatasetName, setNewDatasetName] = useState('');
  const [newDatasetDesc, setNewDatasetDesc] = useState('');

  useEffect(() => {
    loadDatasets();
    api.listDocuments(0, 50).then(setDocuments);
  }, []);

  const loadDatasets = async () => {
    try {
      const data = await api.listDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        handleSelectDataset(data[0]);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
    }
  };

  const handleSelectDataset = async (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setActiveRun(null);
    setProposals([]);
    setSelectedClusterId(null);
    setGeneratedConfigSuccess(null);
  };

  const handleCreateDataset = async () => {
    if (!newDatasetName) return;
    try {
      const created = await api.createDataset({
        name: newDatasetName,
        description: newDatasetDesc,
      });
      setShowCreateDatasetModal(false);
      setNewDatasetName('');
      setNewDatasetDesc('');
      await loadDatasets();
      handleSelectDataset(created);
    } catch (err: any) {
      alert(`Create dataset failed: ${err.message}`);
    }
  };

  const handleAddDocumentToDataset = async (docId: string) => {
    if (!selectedDataset) return;
    try {
      await api.addDocumentToDataset(selectedDataset.id, docId);
      await loadDatasets();
    } catch (err: any) {
      alert(`Add document failed: ${err.message}`);
    }
  };

  const handleStartDiscovery = async () => {
    if (!selectedDataset) return;
    setIsRunning(true);
    setGeneratedConfigSuccess(null);
    try {
      const run = await api.startDiscoveryRun(selectedDataset.id);
      setActiveRun(run);

      // Poll until completed
      let attempts = 0;
      let currentRun = run;
      while (currentRun.status === 'running' || currentRun.status === 'pending') {
        if (attempts++ > 20) break;
        await new Promise((r) => setTimeout(r, 600));
        currentRun = await api.getDiscoveryRun(run.id);
      }
      setActiveRun(currentRun);

      // Fetch proposals
      const propData = await api.listProposals(currentRun.id);
      setProposals(propData);
    } catch (err: any) {
      alert(`Discovery failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleProposalAction = async (
    proposalId: string,
    status: 'approved' | 'rejected'
  ) => {
    try {
      await api.updateProposalStatus(proposalId, status);
      setProposals((prev) =>
        prev.map((p) => (p.id === proposalId ? { ...p, status } : p))
      );
    } catch (err: any) {
      alert(`Update proposal failed: ${err.message}`);
    }
  };

  const handleGenerateConfiguration = async () => {
    if (!activeRun) return;
    setIsGeneratingConfig(true);
    try {
      const slug = `learned_${selectedDataset?.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')}_${Date.now().toString().slice(-4)}`;
      const cfg = await api.generateConfigurationFromRun(activeRun.id, {
        name: `${selectedDataset?.name} (Learned)`,
        slug,
      });
      setGeneratedConfigSuccess(`Created configuration: ${cfg.name} (${cfg.slug})`);
    } catch (err: any) {
      alert(`Generate configuration failed: ${err.message}`);
    } finally {
      setIsGeneratingConfig(false);
    }
  };

  // Convert clusters for BKLitClusterBar
  const clustersData = activeRun?.clusters
    ? activeRun.clusters.map((c) => ({
        id: c.id,
        label: c.label,
        count: c.document_count,
        isOutlier: c.is_outlier,
      }))
    : [];

  const filteredProposals = selectedClusterId
    ? proposals.filter((p) => p.cluster_id === selectedClusterId)
    : proposals;

  const approvedCount = proposals.filter((p) => p.status === 'approved').length;

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 font-sans">
            Pattern Discovery & Example-Based Trainer
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Mode B: Analyze N document examples, detect recurring templates, infer stable labels, and generate rules.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreateDatasetModal(true)}
            className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs font-mono text-zinc-200 transition-colors flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Dataset</span>
          </button>

          <button
            onClick={handleStartDiscovery}
            disabled={!selectedDataset || isRunning}
            className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50 transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Discovering Patterns...' : 'Run Discovery'}</span>
          </button>
        </div>
      </div>

      {/* Dataset Picker and Training Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Dataset Selector & Documents (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3">
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              Select Training Dataset
            </h3>

            <div className="space-y-1">
              {datasets.length === 0 ? (
                <div className="text-xs text-zinc-400 font-mono py-2">
                  No datasets created yet. Click "+ New Dataset" above.
                </div>
              ) : (
                datasets.map((d) => {
                  const isSelected = selectedDataset?.id === d.id;
                  return (
                    <div
                      key={d.id}
                      onClick={() => handleSelectDataset(d)}
                      className={`p-2.5 rounded cursor-pointer border text-xs transition-colors flex items-center justify-between ${
                        isSelected
                          ? 'bg-zinc-800 border-zinc-600 text-white'
                          : 'bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-zinc-200">{d.name}</div>
                        <div className="text-[10px] text-zinc-400 font-mono">
                          {d.document_count} documents in training set
                        </div>
                      </div>
                      <Layers className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Add Documents to Dataset */}
          {selectedDataset && (
            <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3 text-xs">
              <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                Add Samples to "{selectedDataset.name}"
              </h3>
              <p className="text-zinc-400 text-[11px] font-mono">
                Click any ingested document to include it as a training example.
              </p>

              <div className="max-h-52 overflow-y-auto space-y-1 pr-1 font-mono">
                {documents.map((d) => (
                  <div
                    key={d.id}
                    className="p-2 rounded bg-zinc-900/60 border border-zinc-800 flex items-center justify-between"
                  >
                    <span className="truncate max-w-[170px] text-zinc-300">{d.original_filename}</span>
                    <button
                      onClick={() => handleAddDocumentToDataset(d.id)}
                      className="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-white text-[10px]"
                    >
                      + Add
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Clusters and Proposals Panel (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {/* Cluster Distribution Bar */}
          {clustersData.length > 0 && (
            <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                  Discovered Document Clusters & Templates ({clustersData.length})
                </h4>
                {selectedClusterId && (
                  <button
                    onClick={() => setSelectedClusterId(null)}
                    className="text-xs font-mono text-zinc-400 hover:text-white"
                  >
                    Clear Filter
                  </button>
                )}
              </div>

              <BKLitClusterBar
                clusters={clustersData}
                selectedClusterId={selectedClusterId}
                onSelectCluster={(id) => setSelectedClusterId(id === selectedClusterId ? null : id)}
              />
            </div>
          )}

          {/* Proposals List */}
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div>
                <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                  Proposed Extraction Rules ({filteredProposals.length})
                </h3>
                <p className="text-xs text-zinc-400 font-mono mt-0.5">
                  Review conservative patterns inferred from recurring document structures.
                </p>
              </div>

              {proposals.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-zinc-400">
                    {approvedCount}/{proposals.length} approved
                  </span>
                  <button
                    onClick={handleGenerateConfiguration}
                    disabled={isGeneratingConfig || approvedCount === 0}
                    className="px-3 py-1.5 rounded bg-zinc-200 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-40 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Generate Config</span>
                  </button>
                </div>
              )}
            </div>

            {generatedConfigSuccess && (
              <div className="p-3 bg-emerald-950/30 border border-emerald-800 rounded text-xs font-mono text-emerald-300 flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-400" />
                <span>{generatedConfigSuccess}</span>
              </div>
            )}

            {filteredProposals.length === 0 ? (
              <div className="p-8 text-center text-zinc-400 text-xs font-mono border border-dashed border-zinc-800 rounded">
                No proposals yet. Select a dataset with documents and click "Run Discovery".
              </div>
            ) : (
              <div className="space-y-3">
                {filteredProposals.map((prop) => {
                  const isApproved = prop.status === 'approved';
                  const isRejected = prop.status === 'rejected';

                  return (
                    <motion.div
                      key={prop.id}
                      layout
                      className={`p-4 rounded-lg border text-xs transition-colors ${
                        isApproved
                          ? 'bg-[#101915] border-emerald-800/80'
                          : isRejected
                          ? 'bg-[#191012] border-rose-900/60 opacity-60'
                          : 'bg-[#0f0f13] border-zinc-800'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-zinc-100 text-sm font-mono">
                              {prop.field_name}
                            </span>
                            <span className="text-[10px] text-zinc-400 font-mono px-1.5 py-0.5 rounded bg-zinc-800">
                              {prop.strategy || 'same_line'}
                            </span>
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getConfidenceBadge(
                                prop.confidence_overall
                              )}`}
                            >
                              Overall: {Math.round((prop.confidence_overall || 0) * 100)}%
                            </span>
                          </div>

                          <div className="font-mono text-zinc-400 text-[11px] pt-1 space-y-0.5">
                            <div>
                              <span className="text-zinc-400">Anchor:</span>{' '}
                              <span className="text-zinc-200">"{prop.anchor}"</span>
                            </div>
                            {prop.pattern_json && (
                              <div>
                                <span className="text-zinc-400">Inferred Pattern:</span>{' '}
                                <code className="text-zinc-200 bg-zinc-900 px-1 py-0.5 rounded">
                                  {prop.pattern_json}
                                </code>
                              </div>
                            )}
                          </div>

                          {/* Confidence breakdown pills */}
                          <div className="flex items-center gap-3 pt-2 text-[10px] font-mono text-zinc-400">
                            <span>
                              Anchor Conf: {Math.round((prop.confidence_anchor || 0) * 100)}%
                            </span>
                            <span>
                              Pattern Conf: {Math.round((prop.confidence_pattern || 0) * 100)}%
                            </span>
                            <span>
                              Position Conf: {Math.round((prop.confidence_position || 0) * 100)}%
                            </span>
                          </div>
                        </div>

                        {/* Approve / Reject Actions */}
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleProposalAction(prop.id, 'approved')}
                            className={`p-1.5 rounded transition-colors ${
                              isApproved
                                ? 'bg-emerald-600 text-white'
                                : 'bg-zinc-800 text-zinc-400 hover:text-emerald-400 hover:bg-zinc-700'
                            }`}
                            title="Approve Proposal"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleProposalAction(prop.id, 'rejected')}
                            className={`p-1.5 rounded transition-colors ${
                              isRejected
                                ? 'bg-rose-600 text-white'
                                : 'bg-zinc-800 text-zinc-400 hover:text-rose-400 hover:bg-zinc-700'
                            }`}
                            title="Reject Proposal"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Create Dataset */}
      <AnimatePresence>
        {showCreateDatasetModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0e0e12] border border-zinc-800 rounded-lg max-w-md w-full p-6 space-y-4 shadow-xl"
            >
              <h3 className="text-base font-semibold text-white font-sans">
                Create Training Dataset
              </h3>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-zinc-400 block mb-1">Dataset Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Acme Corp Invoices"
                    value={newDatasetName}
                    onChange={(e) => setNewDatasetName(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Description</label>
                  <input
                    type="text"
                    placeholder="e.g. Set of 10 sample PDF invoices"
                    value={newDatasetDesc}
                    onChange={(e) => setNewDatasetDesc(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowCreateDatasetModal(false)}
                  className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white text-xs"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateDataset}
                  disabled={!newDatasetName}
                  className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold disabled:opacity-50"
                >
                  Create Dataset
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
