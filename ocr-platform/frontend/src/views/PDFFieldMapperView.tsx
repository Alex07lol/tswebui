import React, { useEffect, useState, useRef } from 'react';
import {
  MousePointerClick,
  Layers,
  CheckCircle2,
  XCircle,
  FileText,
  Loader2,
  Sparkles,
  Search,
  Check,
  Play,
  RotateCcw,
} from 'lucide-react';
import {
  SelectionAnalysis,
  analyzeSelection,
  saveLocator,
  testLocatorCrossDocuments,
} from '../lib/websiteApi';
import { listSetups, SetupSummary, getSetup, SetupDetail } from '../lib/setupApi';

interface OCRDocItem {
  id: string;
  filename: string;
  page_count: number;
}

export const PDFFieldMapperView: React.FC = () => {
  const [documents, setDocuments] = useState<OCRDocItem[]>([]);
  const [setups, setSetups] = useState<SetupSummary[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [selectedSetupId, setSelectedSetupId] = useState<string>('');
  const [activeSetup, setActiveSetup] = useState<SetupDetail | null>(null);

  const [loading, setLoading] = useState(true);
  const [docLoading, setDocLoading] = useState(false);

  // Document page data
  const [pageWords, setPageWords] = useState<any[]>([]);
  const [pageWidth, setPageWidth] = useState(800);
  const [pageHeight, setPageHeight] = useState(1050);
  const [pageImageUrl, setPageImageUrl] = useState<string | null>(null);

  // Selection state
  const [selectedWordIndices, setSelectedWordIndices] = useState<number[]>([]);
  const [analysis, setAnalysis] = useState<SelectionAnalysis | null>(null);
  const [selectedFieldId, setSelectedFieldId] = useState<string>('');
  const [customFieldName, setCustomFieldName] = useState<string>('');
  const [savingLocator, setSavingLocator] = useState(false);
  const [savedLocatorId, setSavedLocatorId] = useState<string | null>(null);

  // Test state
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState<any | null>(null);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [docsRes, setupsRes] = await Promise.all([
          fetch('/api/documents').then((r) => r.json()).catch(() => []),
          listSetups(),
        ]);
        setDocuments(docsRes || []);
        setSetups(setupsRes || []);

        if (docsRes && docsRes.length > 0) {
          setSelectedDocId(docsRes[0].id);
        }
        if (setupsRes && setupsRes.length > 0) {
          setSelectedSetupId(setupsRes[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  useEffect(() => {
    if (!selectedSetupId) return;
    getSetup(selectedSetupId).then(setActiveSetup).catch(console.error);
  }, [selectedSetupId]);

  useEffect(() => {
    if (!selectedDocId) return;
    loadDocumentDetails(selectedDocId);
  }, [selectedDocId]);

  const loadDocumentDetails = async (docId: string) => {
    setDocLoading(true);
    setSelectedWordIndices([]);
    setAnalysis(null);
    setSavedLocatorId(null);
    setTestResults(null);

    try {
      // 1. Fetch OCR Result
      const ocrRes = await fetch(`/api/ocr/${docId}`).then((r) => r.json()).catch(() => null);
      if (ocrRes && ocrRes.pages && ocrRes.pages.length > 0) {
        const p1 = ocrRes.pages[0];
        setPageWords(p1.words || []);
        setPageWidth(p1.width || 800);
        setPageHeight(p1.height || 1050);
      } else {
        setPageWords([]);
      }

      setPageImageUrl(`/api/documents/${docId}/file`);
    } catch (err) {
      console.error(err);
    } finally {
      setDocLoading(false);
    }
  };

  const handleWordClick = (idx: number) => {
    let nextIndices: number[];
    if (selectedWordIndices.includes(idx)) {
      nextIndices = selectedWordIndices.filter((i) => i !== idx);
    } else {
      nextIndices = [...selectedWordIndices, idx];
    }
    nextIndices.sort((a, b) => a - b);
    setSelectedWordIndices(nextIndices);

    if (nextIndices.length === 0) {
      setAnalysis(null);
      return;
    }

    // Build bounding box and text
    const selectedWords = nextIndices.map((i) => pageWords[i]);
    const bx = Math.min(...selectedWords.map((w) => w.bbox_x || 0));
    const by = Math.min(...selectedWords.map((w) => w.bbox_y || 0));
    const max_x = Math.max(...selectedWords.map((w) => (w.bbox_x || 0) + (w.bbox_width || 20)));
    const max_y = Math.max(...selectedWords.map((w) => (w.bbox_y || 0) + (w.bbox_height || 15)));
    const bw = max_x - bx;
    const bh = max_y - by;
    const text = selectedWords.map((w) => w.text).join(' ');

    analyzeSelection({
      page_width: pageWidth,
      page_height: pageHeight,
      bbox_x: bx,
      bbox_y: by,
      bbox_width: bw,
      bbox_height: bh,
      selected_text: text,
      page_words: pageWords,
    })
      .then(setAnalysis)
      .catch(console.error);
  };

  const handleSaveLocator = async () => {
    if (!analysis) return;
    const targetField = selectedFieldId || customFieldName;
    if (!targetField) {
      alert('Please select or specify a target field name.');
      return;
    }

    setSavingLocator(true);
    try {
      const selectedWords = selectedWordIndices.map((i) => pageWords[i]);
      const bx = Math.min(...selectedWords.map((w) => w.bbox_x || 0));
      const by = Math.min(...selectedWords.map((w) => w.bbox_y || 0));
      const max_x = Math.max(...selectedWords.map((w) => (w.bbox_x || 0) + (w.bbox_width || 20)));
      const max_y = Math.max(...selectedWords.map((w) => (w.bbox_y || 0) + (w.bbox_height || 15)));

      const res = await saveLocator({
        field_id: targetField,
        name: `Visual Locator for ${targetField}`,
        template_label: 'Drawing Title Block',
        document_id: selectedDocId,
        page_number: 1,
        selection_analysis: analysis,
        pixel_bbox: [bx, by, max_x - bx, max_y - by, pageWidth, pageHeight],
      });

      setSavedLocatorId(res.id);
      alert('Visual locator saved and linked to Setup!');
    } catch (err: any) {
      alert(err.message || 'Failed to save locator.');
    } finally {
      setSavingLocator(false);
    }
  };

  const handleRunCrossTest = async () => {
    if (!savedLocatorId) return;
    setTesting(true);
    try {
      const res = await testLocatorCrossDocuments(savedLocatorId, 8);
      setTestResults(res);
    } catch (err: any) {
      alert(err.message || 'Test run failed.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-zinc-900/60 border border-zinc-800 rounded-2xl">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md mb-1 border border-emerald-500/20">
            <MousePointerClick className="w-3.5 h-3.5" />
            <span>Interactive Visual Teaching</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Teach From PDF (Field Mapper)
          </h1>
          <p className="text-xs text-zinc-400 max-w-2xl">
            Click words or titles directly on the document. The system captures relative coordinates,
            nearby anchors, and structure to learn generalizable locators across documents.
          </p>
        </div>

        {/* Pickers */}
        <div className="flex items-center space-x-3 shrink-0">
          <div>
            <label className="block text-[10px] uppercase font-mono text-zinc-400 mb-1">Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="px-3 py-1.5 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-200 focus:outline-none"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] uppercase font-mono text-zinc-400 mb-1">Target Setup</label>
            <select
              value={selectedSetupId}
              onChange={(e) => setSelectedSetupId(e.target.value)}
              className="px-3 py-1.5 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-200 focus:outline-none"
            >
              {setups.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Document Canvas (2 cols) */}
        <div className="lg:col-span-2 bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
          <div className="p-3 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
            <span>
              Click tokens to select phrase ({selectedWordIndices.length} token{selectedWordIndices.length === 1 ? '' : 's'} selected)
            </span>
            {selectedWordIndices.length > 0 && (
              <button
                onClick={() => { setSelectedWordIndices([]); setAnalysis(null); }}
                className="text-zinc-400 hover:text-white flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Selection</span>
              </button>
            )}
          </div>

          <div className="relative overflow-auto p-4 flex items-center justify-center min-h-[600px] bg-zinc-900/40">
            {docLoading ? (
              <div className="py-20 flex flex-col items-center space-y-2 text-zinc-400">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                <span className="text-xs">Loading document tokens...</span>
              </div>
            ) : pageWords.length === 0 ? (
              <div className="p-8 text-center text-xs text-zinc-500">
                No OCR tokens found for this document. Run OCR in Scan Documents first.
              </div>
            ) : (
              <div
                className="relative bg-white shadow-2xl rounded"
                style={{ width: `${pageWidth}px`, height: `${pageHeight}px` }}
              >
                {/* Background Image if available */}
                {pageImageUrl && (
                  <img
                    src={pageImageUrl}
                    alt="Document page"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none opacity-90"
                  />
                )}

                {/* Overlay OCR Word Tokens */}
                {pageWords.map((word, idx) => {
                  const isSelected = selectedWordIndices.includes(idx);
                  return (
                    <div
                      key={idx}
                      onClick={() => handleWordClick(idx)}
                      title={`${word.text} (${Math.round((word.confidence || 0.9) * 100)}% conf)`}
                      className={`absolute cursor-pointer border transition-colors select-none text-transparent hover:text-zinc-900 text-[10px] font-mono leading-none ${
                        isSelected
                          ? 'bg-blue-500/40 border-blue-600 ring-2 ring-blue-500 z-20'
                          : 'bg-transparent hover:bg-amber-400/20 border-zinc-400/30 hover:border-amber-500'
                      }`}
                      style={{
                        left: `${word.bbox_x}px`,
                        top: `${word.bbox_y}px`,
                        width: `${word.bbox_width}px`,
                        height: `${word.bbox_height}px`,
                      }}
                    />
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Inspector & Tester (1 col) */}
        <div className="space-y-6">
          {/* Selection Analysis Card */}
          <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-2xl space-y-4 shadow-md">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span>Selection Inspector</span>
            </h3>

            {analysis ? (
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-zinc-500 uppercase tracking-wider text-[10px] block font-semibold">
                    Selected Phrase
                  </span>
                  <div className="mt-1 p-2.5 bg-zinc-950 border border-zinc-800 rounded-lg font-mono font-bold text-blue-300 text-sm">
                    {analysis.selected_text}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 bg-zinc-950 border border-zinc-800 rounded">
                    <span className="text-zinc-500 text-[10px] block">Relative Box (X, Y)</span>
                    <span className="font-mono text-zinc-300">
                      {analysis.rel_x}, {analysis.rel_y}
                    </span>
                  </div>
                  <div className="p-2 bg-zinc-950 border border-zinc-800 rounded">
                    <span className="text-zinc-500 text-[10px] block">Inferred Type</span>
                    <span className="font-mono text-emerald-400 capitalize">
                      {analysis.inferred_type}
                    </span>
                  </div>
                </div>

                {analysis.anchor_candidates.length > 0 && (
                  <div>
                    <span className="text-zinc-500 uppercase tracking-wider text-[10px] block font-semibold mb-1">
                      Discovered Anchors / Labels
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {analysis.anchor_candidates.map((a, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-200 font-mono text-[11px]">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Setup Field Assignment */}
                <div className="pt-2 border-t border-zinc-800 space-y-2">
                  <span className="text-zinc-400 font-semibold block text-[11px]">
                    Assign to Field:
                  </span>

                  {activeSetup && activeSetup.fields && activeSetup.fields.length > 0 ? (
                    <select
                      value={selectedFieldId}
                      onChange={(e) => setSelectedFieldId(e.target.value)}
                      className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100"
                    >
                      <option value="">-- Choose Field --</option>
                      {activeSetup.fields.map((f: any) => (
                        <option key={f.id || f.field_id} value={f.id || f.field_id}>
                          {f.display_name} ({f.output_variable || f.field_id})
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={customFieldName}
                      onChange={(e) => setCustomFieldName(e.target.value)}
                      placeholder="e.g. Title, Drawing Number"
                      className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100"
                    />
                  )}

                  <button
                    onClick={handleSaveLocator}
                    disabled={savingLocator}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition-colors flex items-center justify-center space-x-1"
                  >
                    {savingLocator ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Check className="w-3.5 h-3.5 mr-1" />
                    )}
                    <span>Save Extraction Locator</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-zinc-500">
                Click one or more OCR tokens on the document canvas to analyze position and nearby anchors.
              </div>
            )}
          </div>

          {/* Cross-Document Test Panel */}
          {savedLocatorId && (
            <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-2xl space-y-4 shadow-md">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Play className="w-4 h-4 text-emerald-400" />
                  <span>Cross-Document Testing</span>
                </h3>
                <button
                  onClick={handleRunCrossTest}
                  disabled={testing}
                  className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold"
                >
                  {testing ? 'Testing...' : 'Run Test'}
                </button>
              </div>

              {testResults ? (
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between p-3 bg-zinc-950 border border-zinc-800 rounded-xl">
                    <span className="text-zinc-400">Match Score:</span>
                    <span className="text-sm font-bold font-mono text-emerald-400">
                      {Math.round(testResults.match_rate * 100)}% ({testResults.matched_count}/{testResults.total_tested})
                    </span>
                  </div>

                  <div className="space-y-1.5 max-h-60 overflow-auto">
                    {testResults.results.map((r: any) => (
                      <div
                        key={r.document_id}
                        className="p-2.5 bg-zinc-950 border border-zinc-800/80 rounded-lg flex items-center justify-between"
                      >
                        <div className="truncate mr-2">
                          <span className="font-semibold text-zinc-300 block truncate">
                            {r.filename}
                          </span>
                          {r.extracted_value && (
                            <span className="text-[10px] text-blue-400 font-mono">
                              &ldquo;{r.extracted_value}&rdquo;
                            </span>
                          )}
                        </div>
                        {r.matched ? (
                          <span className="flex items-center text-emerald-400 text-xs font-medium shrink-0">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                            {Math.round(r.confidence * 100)}%
                          </span>
                        ) : (
                          <span className="flex items-center text-red-400 text-xs font-medium shrink-0">
                            <XCircle className="w-3.5 h-3.5 mr-1" />
                            Miss
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-zinc-500">
                  Click &ldquo;Run Test&rdquo; to test this locator across other documents in the archive.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
