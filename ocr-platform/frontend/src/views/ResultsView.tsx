import React, { useState, useEffect } from 'react';
import { Download, Check, Edit3, ChevronRight, FileSpreadsheet, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { setupApi, SetupItem } from '../lib/setupApi';
import { api, DocumentItem, ExtractionResult } from '../lib/api';
import { ConfidenceBadge } from '../components/ConfidenceBadge';

interface ResultsViewProps {
  initialSetupId?: string | null;
  initialDocumentId?: string | null;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  initialSetupId,
  initialDocumentId,
}) => {
  const [setups, setSetups] = useState<SetupItem[]>([]);
  const [selectedSetupId, setSelectedSetupId] = useState<string>(initialSetupId || '');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>(initialDocumentId || '');
  const [extractedResult, setExtractedResult] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Correction loop state
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [correctedValue, setCorrectedValue] = useState('');
  const [learnCorrection, setLearnCorrection] = useState(true);
  const [correctionSuccess, setCorrectionSuccess] = useState<string | null>(null);

  useEffect(() => {
    setupApi.listSetups().then((s) => {
      setSetups(s);
      if (!selectedSetupId && s.length > 0) setSelectedSetupId(s[0].id);
    });
    api.listDocuments(0, 50).then((docs) => {
      setDocuments(docs);
      if (!selectedDocId && docs.length > 0) setSelectedDocId(docs[0].id);
    });
  }, []);

  const loadExtraction = async () => {
    if (!selectedSetupId || !selectedDocId) return;
    setIsLoading(true);
    try {
      const res = await setupApi.scanWithSetup(selectedSetupId, selectedDocId);
      setExtractedResult(res);
    } catch (err) {
      console.error('Failed to load extraction:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedSetupId && selectedDocId) {
      loadExtraction();
    }
  }, [selectedSetupId, selectedDocId]);

  const handleStartCorrect = (fieldId: string, currentVal: string) => {
    setEditingFieldId(fieldId);
    setCorrectedValue(currentVal || '');
  };

  const handleSaveCorrection = async (fieldId: string, origVal: string) => {
    if (!correctedValue.trim()) return;

    if (learnCorrection) {
      const confirmed = window.confirm(
        `Apply this correction to improve future extractions for this setup?\n\nThis will train the system on your correction.`
      );
      if (confirmed) {
        try {
          await fetch('/api/corrections', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              document_id: selectedDocId,
              field_name: fieldId,
              original_value: origVal,
              corrected_value: correctedValue.trim(),
              ocr_tokens: [],
            }),
          });
        } catch (e) {
          console.error('Failed to record learning correction:', e);
        }
      }
    }

    // Update locally
    if (extractedResult) {
      const updated = {
        ...extractedResult,
        extracted_values: extractedResult.extracted_values.map((v: any) =>
          v.field_id === fieldId ? { ...v, value: correctedValue.trim() } : v
        ),
      };
      setExtractedResult(updated);
    }

    setEditingFieldId(null);
    setCorrectionSuccess(fieldId);
    setTimeout(() => setCorrectionSuccess(null), 3000);
  };

  const handleExportJSON = () => {
    if (!extractedResult) return;
    const blob = new Blob([JSON.stringify(extractedResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `results_${selectedDocId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = () => {
    if (!extractedResult) return;
    const headers = ['Field', 'Value', 'Confidence', 'Validation'];
    const rows = extractedResult.extracted_values.map((v: any) => [
      `"${v.display_name}"`,
      `"${(v.value || '').replace(/"/g, '""')}"`,
      v.confidence_label,
      v.validation_passed ? 'Pass' : 'Unchecked',
    ]);
    const csvContent = [headers.join(','), ...rows.map((r: any) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `results_${selectedDocId.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-8 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            Extraction Results
          </h1>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Review, verify, correct, and export structured information from your documents.
          </p>
        </div>

        {extractedResult && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>CSV</span>
            </button>
            <button
              onClick={handleExportJSON}
              className="px-3.5 py-1.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>JSON</span>
            </button>
          </div>
        )}
      </div>

      {/* Selectors Filter Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
        <div>
          <label className="block text-xs font-mono text-zinc-400 mb-1">Select Setup:</label>
          <select
            value={selectedSetupId}
            onChange={(e) => setSelectedSetupId(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs font-mono text-zinc-200 outline-none"
          >
            {setups.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-mono text-zinc-400 mb-1">Select Document:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs font-mono text-zinc-200 outline-none"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results List */}
      {isLoading ? (
        <div className="py-20 text-center text-xs font-mono text-zinc-500">
          Extracting data...
        </div>
      ) : !extractedResult ? (
        <div className="py-16 text-center border border-dashed border-zinc-800 rounded-xl space-y-2">
          <p className="text-sm text-zinc-400">Select a setup and document to view extraction results.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-mono text-zinc-400">
              Extracted {extractedResult.extracted_values.length} fields from{' '}
              <strong className="text-zinc-200">{documents.find(d => d.id === selectedDocId)?.original_filename}</strong>
            </span>
            <ConfidenceBadge
              score={extractedResult.overall_confidence}
              label={extractedResult.overall_confidence_label}
            />
          </div>

          <div className="space-y-3">
            {extractedResult.extracted_values.map((item: any) => {
              const isEditing = editingFieldId === item.field_id;
              const wasSuccess = correctionSuccess === item.field_id;

              return (
                <div
                  key={item.field_id}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-3 transition-colors hover:border-zinc-700"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
                        {item.display_name}
                      </h4>
                      {!isEditing ? (
                        <div className="text-lg font-mono font-bold text-zinc-100 mt-1">
                          {item.value || <span className="text-zinc-600 font-normal">Not detected</span>}
                        </div>
                      ) : (
                        <div className="mt-2 space-y-2 max-w-md">
                          <input
                            type="text"
                            value={correctedValue}
                            onChange={(e) => setCorrectedValue(e.target.value)}
                            className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-1.5 text-sm font-mono text-zinc-100 outline-none focus:border-zinc-500"
                            autoFocus
                          />
                          <label className="flex items-center gap-2 text-xs font-mono text-zinc-400 select-none cursor-pointer">
                            <input
                              type="checkbox"
                              checked={learnCorrection}
                              onChange={(e) => setLearnCorrection(e.target.checked)}
                              className="rounded bg-zinc-950 border-zinc-800"
                            />
                            <span>Use this correction to improve future scans</span>
                          </label>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <ConfidenceBadge
                        score={item.confidence_score}
                        label={item.confidence_label}
                        why={item.why}
                      />
                    </div>
                  </div>

                  {wasSuccess && (
                    <div className="p-2 bg-emerald-950/40 border border-emerald-800/60 rounded text-emerald-300 text-xs font-mono flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5" />
                      <span>Correction saved successfully!</span>
                    </div>
                  )}

                  <div className="pt-2 border-t border-zinc-800/80 flex items-center justify-between">
                    <span className="text-[11px] font-mono text-zinc-500">
                      Raw OCR: {item.raw_value || 'None'}
                    </span>

                    {!isEditing ? (
                      <button
                        onClick={() => handleStartCorrect(item.field_id, item.value || '')}
                        className="text-xs font-mono text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Correct this value</span>
                      </button>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingFieldId(null)}
                          className="px-2.5 py-1 rounded bg-zinc-800 text-zinc-400 hover:text-white text-xs font-mono"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleSaveCorrection(item.field_id, item.value || '')}
                          className="px-3 py-1 rounded bg-zinc-100 text-zinc-950 hover:bg-white text-xs font-semibold"
                        >
                          Save Correction
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
