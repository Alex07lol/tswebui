import React, { useState, useEffect } from 'react';
import { Play, ArrowRight, Upload, CheckCircle2, AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { setupApi, SetupItem, ScanSetupResult } from '../lib/setupApi';
import { api, DocumentItem } from '../lib/api';
import { DropZone } from '../components/DropZone';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { AmbiguityPanel } from '../components/AmbiguityPanel';

interface ScanDocumentsViewProps {
  initialSetupId?: string | null;
  onViewResults?: (setupId: string, docId: string) => void;
}

export const ScanDocumentsView: React.FC<ScanDocumentsViewProps> = ({
  initialSetupId,
  onViewResults,
}) => {
  const [setups, setSetups] = useState<SetupItem[]>([]);
  const [selectedSetupId, setSelectedSetupId] = useState<string>(initialSetupId || '');
  const [uploadedDoc, setUploadedDoc] = useState<DocumentItem | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanSetupResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setupApi.listSetups().then((data) => {
      setSetups(data);
      if (!selectedSetupId && data.length > 0) {
        setSelectedSetupId(data[0].id);
      }
    });
  }, []);

  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelected = async (file: File) => {
    setIsUploading(true);
    setErrorMsg(null);
    try {
      const doc = await api.uploadDocument(file);
      setUploadedDoc(doc);
      setScanResult(null);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunScan = async () => {
    if (!selectedSetupId || !uploadedDoc) return;
    setIsScanning(true);
    setErrorMsg(null);
    try {
      const res = await setupApi.scanWithSetup(selectedSetupId, uploadedDoc.id);
      setScanResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  const handleAmbiguityResolved = async (fieldId: string, chosenVal: string) => {
    if (!selectedSetupId || !uploadedDoc) return;
    await setupApi.resolveCandidate(selectedSetupId, fieldId, uploadedDoc.id, chosenVal);
    // Refresh scan
    handleRunScan();
  };

  const selectedSetup = setups.find((s) => s.id === selectedSetupId);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8 font-sans">
      {/* Header */}
      <div className="border-b border-zinc-800 pb-4">
        <h1 className="text-2xl font-bold text-zinc-100">
          Scan Documents
        </h1>
        <p className="text-xs text-zinc-400 font-mono mt-0.5">
          Pick a saved setup, upload your paperwork, and extract values automatically.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-xs font-mono">
          {errorMsg}
        </div>
      )}

      {/* Grid: 2 Steps (Setup selection + Upload) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Step 1: Pick Setup */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono">
              Step 1: Choose a Setup
            </span>
            {selectedSetup && (
              <span className="text-[11px] font-mono text-zinc-500">
                {selectedSetup.field_count} fields
              </span>
            )}
          </div>

          {setups.length === 0 ? (
            <p className="text-xs text-zinc-500 font-mono">
              No setups found. Please create a setup first.
            </p>
          ) : (
            <select
              value={selectedSetupId}
              onChange={(e) => setSelectedSetupId(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3.5 py-2.5 text-xs font-mono text-zinc-200 outline-none focus:border-zinc-600"
            >
              {setups.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.field_count} fields)
                </option>
              ))}
            </select>
          )}

          {selectedSetup && (
            <div className="p-3 bg-zinc-950/80 rounded border border-zinc-800/80 text-xs font-mono text-zinc-400 space-y-1">
              <div className="text-zinc-200 font-semibold">{selectedSetup.name}</div>
              <div className="text-[11px] text-zinc-500">Status: {selectedSetup.status}</div>
            </div>
          )}
        </div>

        {/* Step 2: Upload Document */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono">
              Step 2: Upload Document
            </span>
            {uploadedDoc && (
              <span className="text-[11px] font-mono text-emerald-400">
                ✓ Uploaded
              </span>
            )}
          </div>

          <DropZone
            onFileSelected={handleFileSelected}
            isUploading={isUploading}
          />

          {uploadedDoc && (
            <div className="p-2.5 bg-zinc-950 rounded border border-zinc-800 flex items-center justify-between text-xs font-mono">
              <span className="text-zinc-300 truncate max-w-xs">{uploadedDoc.original_filename}</span>
              <span className="text-zinc-500 text-[11px]">{uploadedDoc.mime_type}</span>
            </div>
          )}
        </div>
      </div>

      {/* Step 3: Scan Button */}
      <div className="flex justify-center">
        <button
          onClick={handleRunScan}
          disabled={!selectedSetupId || !uploadedDoc || isScanning}
          className="px-8 py-3 rounded-xl bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-semibold flex items-center gap-2.5 transition-all shadow-md disabled:opacity-40 disabled:hover:bg-zinc-100"
        >
          <Play className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
          <span>{isScanning ? 'Scanning document...' : 'Extract Information'}</span>
        </button>
      </div>

      {/* Results Section */}
      <AnimatePresence>
        {scanResult && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-4">
              <div>
                <h3 className="text-base font-semibold text-zinc-100">
                  Extracted Information
                </h3>
                <p className="text-xs text-zinc-400 font-mono mt-0.5">
                  Setup: {scanResult.setup_name}
                </p>
              </div>

              <ConfidenceBadge
                score={scanResult.overall_confidence}
                label={scanResult.overall_confidence_label}
                why={['Overall extraction confidence across all fields']}
              />
            </div>

            {/* Extracted Values Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {scanResult.extracted_values.map((v) => (
                <div
                  key={v.field_id}
                  className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-zinc-400">{v.display_name}</span>
                    <ConfidenceBadge score={v.confidence_score} label={v.confidence_label} why={v.why} />
                  </div>

                  <div className="text-base font-mono font-bold text-zinc-100">
                    {v.value || <span className="text-zinc-600 font-normal">Not found</span>}
                  </div>
                </div>
              ))}
            </div>

            {/* View full results footer */}
            {onViewResults && (
              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => onViewResults(scanResult.setup_id, scanResult.document_id)}
                  className="text-xs font-mono text-zinc-400 hover:text-white flex items-center gap-1.5 transition-colors underline"
                >
                  <span>Open Full Results & Export</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
