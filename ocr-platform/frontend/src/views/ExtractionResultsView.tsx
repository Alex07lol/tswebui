import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  api,
  DocumentItem,
  Configuration,
  ExtractionResult,
  ExtractedValue,
} from '../lib/api';
import {
  FileSpreadsheet,
  Download,
  Play,
  CheckCircle2,
  AlertCircle,
  FileJson,
  Layers,
  Search,
  ExternalLink,
} from 'lucide-react';
import { getConfidenceBadge } from '../lib/utils';

export const ExtractionResultsView: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [configs, setConfigs] = useState<Configuration[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [selectedConfigId, setSelectedConfigId] = useState<string>('');
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');

  const [isExtracting, setIsExtracting] = useState(false);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [filterText, setFilterText] = useState('');
  const [lastJobId, setLastJobId] = useState<string | null>(null);

  // Correction state
  const [editingFields, setEditingFields] = useState<Record<string, { value: string }>>({});
  const [correctionSuccess, setCorrectionSuccess] = useState<string | null>(null);
  const [confidenceBoosts, setConfidenceBoosts] = useState<Record<string, string>>({});

  useEffect(() => {
    loadInitData();
  }, []);

  const loadInitData = async () => {
    try {
      const [docsData, configsData] = await Promise.all([
        api.listDocuments(0, 50),
        api.listConfigurations(),
      ]);
      setDocuments(docsData);
      if (docsData.length > 0) setSelectedDocId(docsData[0].id);

      setConfigs(configsData);
      if (configsData.length > 0) {
        setSelectedConfigId(configsData[0].id);
        if (configsData[0].versions && configsData[0].versions.length > 0) {
          setSelectedVersionId(configsData[0].versions[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const handleConfigChange = (configId: string) => {
    setSelectedConfigId(configId);
    const found = configs.find((c) => c.id === configId);
    if (found && found.versions && found.versions.length > 0) {
      setSelectedVersionId(found.versions[found.versions.length - 1].id);
    } else {
      setSelectedVersionId('');
    }
  };

  const startEditing = (val: ExtractedValue) => {
    setEditingFields({
      ...editingFields,
      [val.field_id]: { value: val.normalized_value || val.raw_value || '' }
    });
  };

  const cancelEditing = (fieldId: string) => {
    const newFields = { ...editingFields };
    delete newFields[fieldId];
    setEditingFields(newFields);
  };

  const saveCorrection = async (val: ExtractedValue) => {
    if (!result) return;
    const newVal = editingFields[val.field_id]?.value;
    if (newVal === undefined) return;

    try {
      const res = await fetch('/api/corrections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: result.document_id,
          field_name: val.field_id,
          original_value: val.normalized_value || val.raw_value || '',
          corrected_value: newVal,
          ocr_tokens: []
        })
      });
      const data = await res.json();
      
      // Update local result to show the new value immediately
      const newResult = { ...result };
      const valIndex = newResult.values.findIndex(v => v.field_id === val.field_id);
      if (valIndex !== -1) {
        newResult.values[valIndex].normalized_value = newVal;
      }
      setResult(newResult);
      
      cancelEditing(val.field_id);
      setCorrectionSuccess(val.field_id);
      if (data.confidence_delta) {
        setConfidenceBoosts({ ...confidenceBoosts, [val.field_id]: data.confidence_delta });
      }
      
      setTimeout(() => {
        setCorrectionSuccess(null);
      }, 3000);
    } catch (err) {
      console.error('Correction failed:', err);
      alert('Failed to save correction.');
    }
  };

  const handleRunExtraction = async () => {
    if (!selectedDocId || !selectedVersionId) {
      alert('Please select both a document and a configuration version');
      return;
    }
    setIsExtracting(true);
    setResult(null);
    try {
      const job = await api.runExtraction(selectedDocId, selectedVersionId);
      setLastJobId(job.job_id);

      // Load extraction result
      const res = await api.getExtractionJobResult(job.job_id);
      setResult(res);
    } catch (err: any) {
      alert(`Extraction failed: ${err.message}`);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleDownloadJSON = () => {
    if (!result) return;
    const payload = {
      document_id: result.document_id,
      overall_confidence: result.overall_confidence,
      extracted_values: result.values.map((v) => ({
        field: v.field_id,
        variable: v.output_variable,
        raw_value: v.raw_value,
        normalized_value: v.normalized_value,
        confidence: v.final_confidence,
        validation_passed: v.validation_passed,
        evidence: v.evidence,
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extraction_${result.document_id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadCSV = () => {
    if (!result) return;
    const headers = ['field_id', 'output_variable', 'raw_value', 'normalized_value', 'confidence', 'validation_passed', 'source_line'];
    const rows = result.values.map((v) => {
      const line = v.evidence && v.evidence.length > 0 ? (v.evidence[0].source_line || '').replace(/"/g, '""') : '';
      return [
        `"${v.field_id}"`,
        `"${v.output_variable}"`,
        `"${(v.raw_value || '').replace(/"/g, '""')}"`,
        `"${(v.normalized_value || '').replace(/"/g, '""')}"`,
        v.final_confidence ?? '',
        v.validation_passed ?? '',
        `"${line}"`,
      ].join(',');
    });
    const csvContent = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extraction_${result.document_id.slice(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredValues = result
    ? result.values.filter(
        (v) =>
          v.field_id.toLowerCase().includes(filterText.toLowerCase()) ||
          v.output_variable.toLowerCase().includes(filterText.toLowerCase()) ||
          (v.normalized_value || '').toLowerCase().includes(filterText.toLowerCase())
      )
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 font-sans">
            Structured Extraction Results & Evidence
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Full audit provenance: Inspect extracted values, normalization passes, OCR evidence boxes, and export.
          </p>
        </div>

        {result && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadJSON}
              className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs font-mono text-zinc-200 flex items-center gap-1.5 transition-colors"
            >
              <FileJson className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={handleDownloadCSV}
              className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs font-mono text-zinc-200 flex items-center gap-1.5 transition-colors"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          </div>
        )}
      </div>

      {/* Target Selector Toolbar */}
      <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 flex flex-col md:flex-row items-stretch md:items-center gap-4 text-xs">
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-zinc-400 block mb-1 font-mono">Select Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-zinc-400 block mb-1 font-mono">Configuration</label>
            <select
              value={selectedConfigId}
              onChange={(e) => handleConfigChange(e.target.value)}
              className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
            >
              {configs.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-zinc-400 block mb-1 font-mono">Version</label>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
            >
              {configs
                .find((c) => c.id === selectedConfigId)
                ?.versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    v{v.version_number} ({v.status})
                  </option>
                ))}
            </select>
          </div>
        </div>

        <div className="flex items-end">
          <button
            onClick={handleRunExtraction}
            disabled={isExtracting || !selectedDocId || !selectedVersionId}
            className="w-full md:w-auto px-4 py-2 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold text-xs flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${isExtracting ? 'animate-spin' : ''}`} />
            <span>{isExtracting ? 'Extracting...' : 'Run Extraction'}</span>
          </button>
        </div>
      </div>

      {/* Main Results Table & Evidence Cards */}
      <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-semibold text-zinc-100 font-sans">
              Extracted Output & Provenance
            </h3>
            {result && (
              <span className="font-mono text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/80 px-2 py-0.5 rounded">
                Overall Confidence: {Math.round((result.overall_confidence || 0) * 100)}%
              </span>
            )}
          </div>

          {result && (
            <div className="relative w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-zinc-400" />
              <input
                type="text"
                placeholder="Filter extracted fields..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="w-full bg-[#121215] border border-zinc-800 rounded pl-8 pr-3 py-1.5 text-xs font-mono text-zinc-200 outline-none focus:border-zinc-700"
              />
            </div>
          )}
        </div>

        {!result ? (
          <div className="p-12 text-center text-zinc-400 text-xs font-mono border border-dashed border-zinc-800 rounded">
            Select a document and configuration version above, then click "Run Extraction" to produce structured fields.
          </div>
        ) : filteredValues.length === 0 ? (
          <div className="p-8 text-center text-zinc-400 text-xs font-mono">
            No fields matched the search criteria.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredValues.map((val, idx) => {
              const ev = val.evidence && val.evidence.length > 0 ? val.evidence[0] : null;

              return (
                <div
                  key={idx}
                  className="p-4 bg-[#0e0e12] border border-zinc-800 rounded-lg text-xs font-mono space-y-2.5"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-zinc-100 text-sm">
                        {val.output_variable}
                      </span>
                      <span className="text-[10px] text-zinc-400 px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">
                        {val.field_id}
                      </span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getConfidenceBadge(
                          val.final_confidence
                        )}`}
                      >
                        {Math.round((val.final_confidence || 0) * 100)}%
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {val.validation_passed === true && (
                        <span className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-950/30 border border-emerald-900/60 px-2 py-0.5 rounded">
                          <CheckCircle2 className="w-3 h-3" />
                          Validated
                        </span>
                      )}
                      {val.validation_passed === false && (
                        <span className="flex items-center gap-1 text-[10px] text-rose-400 bg-rose-950/30 border border-rose-900/60 px-2 py-0.5 rounded">
                          <AlertCircle className="w-3 h-3" />
                          Validation Failed
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Values grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-800 flex flex-col relative group">
                      <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-0.5 flex items-center justify-between">
                        <span>Clean Normalized Value</span>
                        {!editingFields[val.field_id] && (
                          <button
                            onClick={() => startEditing(val)}
                            className="text-zinc-600 hover:text-zinc-300 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                            Edit
                          </button>
                        )}
                      </div>
                      <div className="text-zinc-100 font-semibold text-xs truncate">
                        {editingFields[val.field_id] ? (
                          <div className="flex items-center gap-2 mt-1">
                            <input
                              type="text"
                              value={editingFields[val.field_id].value}
                              onChange={(e) => setEditingFields({ ...editingFields, [val.field_id]: { ...editingFields[val.field_id], value: e.target.value } })}
                              className="w-full bg-[#121215] border border-zinc-700 rounded px-2 py-1 text-zinc-200 outline-none focus:border-zinc-500"
                              autoFocus
                            />
                            <button
                              onClick={() => saveCorrection(val)}
                              className="px-2 py-1 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold flex items-center gap-1 shrink-0"
                            >
                              ✓ Save
                            </button>
                            <button
                              onClick={() => cancelEditing(val.field_id)}
                              className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 flex items-center gap-1 shrink-0"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          val.normalized_value || <span className="text-zinc-600">null</span>
                        )}
                      </div>
                      
                      {/* Success Toast */}
                      {correctionSuccess === val.field_id && (
                        <motion.div
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          className="absolute -top-8 right-0 bg-zinc-900 border border-emerald-900 text-emerald-400 text-[10px] px-2 py-1 rounded shadow-lg flex items-center gap-1 z-10"
                        >
                          Correction saved — AI learning updated
                          {confidenceBoosts[val.field_id] && (
                            <span className="bg-emerald-950 px-1 py-0.5 rounded border border-emerald-800 ml-1">
                              +{confidenceBoosts[val.field_id]}% confidence boost
                            </span>
                          )}
                        </motion.div>
                      )}
                    </div>

                    <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-800">
                      <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-0.5">
                        Raw OCR Output
                      </div>
                      <div className="text-zinc-400 text-xs truncate">
                        {val.raw_value || <span className="text-zinc-600">null</span>}
                      </div>
                    </div>
                  </div>

                  {/* Evidence Trace Provenance */}
                  {ev && (
                    <div className="pt-2 border-t border-zinc-800/80 text-[11px] text-zinc-400 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-zinc-400">Anchor matched:</span>
                        <span className="text-zinc-200 font-medium">"{ev.anchor_text || 'direct'}"</span>
                        <span className="text-zinc-400">in line:</span>
                        <span className="text-zinc-200 italic">"{ev.source_line}"</span>
                      </div>

                      {ev.bbox_x !== undefined && (
                        <div className="flex items-center gap-2 text-[10px] text-zinc-400">
                          <span>
                            Bounding Box: [{ev.bbox_x}, {ev.bbox_y}, {ev.bbox_width}, {ev.bbox_height}]
                          </span>
                          <span>&middot;</span>
                          <span>Page {ev.page_number || 1}</span>
                          <span>&middot;</span>
                          <span>OCR Conf: {Math.round((ev.ocr_confidence || 0) * 100)}%</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
