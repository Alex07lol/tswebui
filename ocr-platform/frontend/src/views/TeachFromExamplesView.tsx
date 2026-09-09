import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Upload, Check, X, Edit, ArrowRight, Layers, FileText, CheckCircle2 } from 'lucide-react';
import { teachApi, TeachLayoutItem, TeachProposalItem } from '../lib/teachApi';
import { api, DocumentItem } from '../lib/api';
import { DropZone } from '../components/DropZone';
import { ConfidenceBadge } from '../components/ConfidenceBadge';

interface TeachFromExamplesViewProps {
  onSetupSaved: (setupId: string) => void;
}

export const TeachFromExamplesView: React.FC<TeachFromExamplesViewProps> = ({
  onSetupSaved,
}) => {
  const [step, setStep] = useState<'upload' | 'analyzing' | 'review' | 'save'>('upload');
  const [uploadedDocs, setUploadedDocs] = useState<DocumentItem[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [layouts, setLayouts] = useState<TeachLayoutItem[]>([]);
  const [proposals, setProposals] = useState<TeachProposalItem[]>([]);
  const [setupName, setSetupName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load existing sample documents if user wants to use them
  useEffect(() => {
    api.listDocuments(0, 50).then((docs) => {
      if (docs.length > 0 && uploadedDocs.length === 0) {
        // Offer quick selection of existing docs
      }
    });
  }, []);

  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelected = async (file: File) => {
    setIsUploading(true);
    setErrorMsg(null);
    try {
      const doc = await api.uploadDocument(file);
      setUploadedDocs((prev) => [...prev, doc]);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (uploadedDocs.length === 0) return;
    setStep('analyzing');
    setErrorMsg(null);
    try {
      const docIds = uploadedDocs.map((d) => d.id);
      const session = await teachApi.startTeachSession(docIds);
      setSessionId(session.session_id);

      // Fetch discovered layouts and proposals
      const fetchedLayouts = await teachApi.getLayouts(session.session_id);
      setLayouts(fetchedLayouts);

      const fetchedProposals = await teachApi.getProposals(session.session_id);
      setProposals(fetchedProposals);

      setStep('review');
    } catch (err: any) {
      setErrorMsg(err.message || 'Analysis failed');
      setStep('upload');
    }
  };

  const handleToggleProposal = (propId: string) => {
    setProposals((prev) =>
      prev.map((p) => {
        if (p.id !== propId) return p;
        const nextAction = p.action === 'use' ? 'skip' : 'use';
        return { ...p, action: nextAction };
      })
    );
  };

  const handleSaveSetup = async () => {
    if (!sessionId || !setupName.trim()) return;
    setIsSaving(true);
    try {
      const acceptedIds = proposals
        .filter((p) => p.action === 'use' || p.action === 'pending')
        .map((p) => p.id);

      const savedSetup = await teachApi.saveSetupFromTeach(
        sessionId,
        setupName.trim(),
        acceptedIds
      );
      onSetupSaved(savedSetup.id);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save setup');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8 font-sans">
      {/* Header */}
      <div className="border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-zinc-100" />
          <h1 className="text-2xl font-bold text-zinc-100">
            Teach From Examples
          </h1>
        </div>
        <p className="text-xs text-zinc-400 font-mono mt-1">
          Upload several sample documents and let the system discover repeating information automatically.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-xs font-mono">
          {errorMsg}
        </div>
      )}

      {/* Phase 1: Upload */}
      {step === 'upload' && (
        <div className="space-y-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider font-mono">
              Upload Sample Documents
            </h3>
            <p className="text-xs text-zinc-400 font-mono">
              Upload 2 or more similar files (PDF or images) so the engine can discover repeating layouts.
            </p>

            <DropZone
              onFileSelected={handleFileSelected}
              isUploading={isUploading}
            />

            {uploadedDocs.length > 0 && (
              <div className="pt-3 border-t border-zinc-800 space-y-2">
                <span className="text-xs font-mono text-zinc-400">
                  {uploadedDocs.length} documents staged for teaching:
                </span>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                  {uploadedDocs.map((d, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded bg-zinc-950 border border-zinc-800 text-xs font-mono text-zinc-300"
                    >
                      {d.original_filename}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-center">
            <button
              onClick={handleStartAnalysis}
              disabled={uploadedDocs.length === 0}
              className="px-8 py-3 rounded-xl bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-semibold flex items-center gap-2 transition-colors disabled:opacity-40"
            >
              <Sparkles className="w-4 h-4" />
              <span>Analyze {uploadedDocs.length} Documents</span>
            </button>
          </div>
        </div>
      )}

      {/* Phase 2: Analyzing */}
      {step === 'analyzing' && (
        <div className="py-24 text-center space-y-5">
          <div className="w-12 h-12 border-2 border-zinc-700 border-t-zinc-100 rounded-full animate-spin mx-auto" />
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-zinc-100">
              Analyzing your documents...
            </h3>
            <p className="text-xs text-zinc-400 font-mono">
              Identifying document layouts and discovering repeating information fields.
            </p>
          </div>
        </div>
      )}

      {/* Phase 3 & 4: Review Discovered Layouts & Proposals */}
      {step === 'review' && (
        <div className="space-y-8">
          {/* Discovered Layouts Section */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-300 font-mono">
              Document Layouts Found ({layouts.length})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {layouts.map((l) => (
                <div
                  key={l.id}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-200">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-zinc-100">{l.label}</h4>
                      <p className="text-xs text-zinc-500 font-mono">{l.document_count} documents match</p>
                    </div>
                  </div>
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2 py-0.5 rounded">
                    Consistent
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Proposals Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-300 font-mono">
                Discovered Information Candidates ({proposals.length})
              </h2>
              <span className="text-xs font-mono text-zinc-500">
                Choose which fields you would like to keep in your Setup
              </span>
            </div>

            <div className="space-y-3">
              {proposals.map((p) => {
                const isSelected = p.action !== 'skip';
                return (
                  <div
                    key={p.id}
                    className={`bg-zinc-900 border rounded-xl p-5 space-y-3 transition-colors ${
                      isSelected ? 'border-zinc-700' : 'border-zinc-800/60 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="text-base font-semibold text-zinc-100 font-sans">
                          {p.suggested_name}
                        </h4>
                        <div className="text-xs font-mono text-zinc-400 space-y-0.5 mt-1">
                          <div>
                            Example found: <strong className="text-zinc-200">{p.example_found}</strong>
                          </div>
                          <div>
                            Looks like: <span className="text-zinc-300 font-bold">{p.human_pattern}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <ConfidenceBadge
                          score={p.confidence_score}
                          label={p.confidence_label}
                          why={p.why}
                        />
                        <button
                          onClick={() => handleToggleProposal(p.id)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-colors ${
                            isSelected
                              ? 'bg-zinc-100 text-zinc-950 hover:bg-white'
                              : 'bg-zinc-800 text-zinc-400 hover:text-white'
                          }`}
                        >
                          {isSelected ? '✓ Using This' : 'Don\'t Use'}
                        </button>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-zinc-800 text-[11px] font-mono text-zinc-500">
                      Why confident: {p.why[0]}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Continue to Save Setup */}
          <div className="pt-4 border-t border-zinc-800 flex justify-end">
            <button
              onClick={() => setStep('save')}
              className="px-6 py-2.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-2"
            >
              <span>Continue to Save Setup</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Phase 5: Name and Save Setup */}
      {step === 'save' && (
        <div className="max-w-md mx-auto py-6 space-y-5">
          <div className="space-y-1 text-center">
            <h3 className="text-lg font-bold text-zinc-100">
              Save as a New Setup
            </h3>
            <p className="text-xs text-zinc-400 font-mono">
              Give your new setup a name so you can scan with it anytime.
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-mono text-zinc-400">
              Setup Name:
            </label>
            <input
              type="text"
              value={setupName}
              onChange={(e) => setSetupName(e.target.value)}
              placeholder="e.g. Supplier Invoices, Warranty Cards"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-100 outline-none focus:border-zinc-500"
              autoFocus
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => setStep('review')}
              className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:text-white text-xs font-mono"
            >
              Back to Proposals
            </button>
            <button
              onClick={handleSaveSetup}
              disabled={isSaving || !setupName.trim()}
              className="px-6 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Setup'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
