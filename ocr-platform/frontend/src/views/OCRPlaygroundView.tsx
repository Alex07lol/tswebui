import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  api,
  DocumentItem,
  OCRResult,
  OCRWord,
  OCRJob,
} from '../lib/api';
import { DropZone } from '../components/DropZone';
import { BoundingBoxOverlay } from '../components/BoundingBoxOverlay';
import {
  Play,
  FileText,
  Copy,
  Check,
  Search,
  Trash2,
  RefreshCw,
  Sliders,
  Layers,
} from 'lucide-react';
import { formatBytes, getConfidenceBadge } from '../lib/utils';

interface OCRPlaygroundViewProps {
  initialDocument?: DocumentItem | null;
  onSendToRuleBuilder?: (tokenText: string) => void;
}

export const OCRPlaygroundView: React.FC<OCRPlaygroundViewProps> = ({
  initialDocument,
  onSendToRuleBuilder,
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(initialDocument || null);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [selectedWord, setSelectedWord] = useState<OCRWord | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<'visual' | 'text' | 'tokens'>('visual');
  const [textSearch, setTextSearch] = useState('');
  const [copied, setCopied] = useState(false);
  const [isOcrRunning, setIsOcrRunning] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [language, setLanguage] = useState('eng');
  const [psm, setPsm] = useState(6);
  const [ocrProvider, setOcrProvider] = useState<'tesseract' | 'mock_vision'>('tesseract');

  // Load document list
  const refreshDocuments = async () => {
    try {
      const docs = await api.listDocuments(0, 50);
      setDocuments(docs);
      if (!selectedDoc && docs.length > 0) {
        setSelectedDoc(docs[0]);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  useEffect(() => {
    refreshDocuments();
  }, []);

  // When selectedDoc changes, fetch its existing OCR result if available
  useEffect(() => {
    if (!selectedDoc) {
      setOcrResult(null);
      return;
    }
    setSelectedPageNum(1);
    setSelectedWord(null);

    api.getOCRResult(selectedDoc.id)
      .then((res) => setOcrResult(res))
      .catch(() => setOcrResult(null));
  }, [selectedDoc]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const doc = await api.uploadDocument(file);
      await refreshDocuments();
      setSelectedDoc(doc);
      // Automatically trigger OCR for immediate feedback
      await handleRunOCR(doc.id);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunOCR = async (docIdToRun?: string) => {
    const docId = docIdToRun || selectedDoc?.id;
    if (!docId) return;
    setIsOcrRunning(true);
    try {
      const job = await api.runOCR(docId, language, psm);
      // Wait for completion (inline queue completes immediately or short poll)
      let attempts = 0;
      let status = job.status;
      while (status === 'running' || status === 'pending') {
        if (attempts++ > 15) break;
        await new Promise((r) => setTimeout(r, 600));
        const updated = await api.getOCRJob(job.id);
        status = updated.status;
      }
      // Load resulting OCR data
      const result = await api.getOCRResult(docId);
      setOcrResult(result);
    } catch (err: any) {
      console.error('OCR run failed:', err);
    } finally {
      setIsOcrRunning(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedDoc) return;
    if (!confirm(`Delete ${selectedDoc.original_filename}?`)) return;
    try {
      await api.deleteDocument(selectedDoc.id);
      setSelectedDoc(null);
      setOcrResult(null);
      await refreshDocuments();
    } catch (err) {
      console.error('Failed to delete doc:', err);
    }
  };

  const handleCopyText = () => {
    if (!ocrResult?.full_text) return;
    navigator.clipboard.writeText(ocrResult.full_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currentPage = ocrResult?.pages.find((p) => p.page_number === selectedPageNum) || ocrResult?.pages[0];
  const wordsForCurrentPage = currentPage?.words || [];

  return (
    <div className="space-y-6">
      {/* Top Header & Quick Upload */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 font-sans">
            OCR Playground & Document Inspector
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Ingest documents, execute Tesseract OCR, and inspect word coordinates & confidence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {selectedDoc && (
            <button
              onClick={handleDelete}
              className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 text-rose-400 hover:bg-rose-950/30 hover:border-rose-800/80 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete</span>
            </button>
          )}

          <button
            onClick={() => handleRunOCR()}
            disabled={!selectedDoc || isOcrRunning}
            className="px-3 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 disabled:opacity-50 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${isOcrRunning ? 'animate-spin' : ''}`} />
            <span>{isOcrRunning ? 'Running OCR...' : 'Run OCR'}</span>
          </button>
        </div>
      </div>

      {/* Grid: Left Column DropZone & Doc Selector, Right Column Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Sidebar Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Animated DropZone */}
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4">
            <h3 className="text-xs font-semibold text-zinc-300 mb-2 uppercase tracking-wider">
              Upload Document
            </h3>
            <DropZone onFileSelected={handleUpload} isUploading={isUploading} />
          </div>

          {/* Document Picker */}
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                Document Library
              </h3>
              <button
                onClick={refreshDocuments}
                className="text-zinc-400 hover:text-white p-1 rounded hover:bg-zinc-800"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>

            <div className="max-h-56 overflow-y-auto space-y-1 pr-1">
              {documents.length === 0 ? (
                <div className="text-xs text-zinc-400 font-mono py-2">No documents available</div>
              ) : (
                documents.map((d) => {
                  const isSelected = selectedDoc?.id === d.id;
                  return (
                    <div
                      key={d.id}
                      onClick={() => setSelectedDoc(d)}
                      className={`p-2 rounded cursor-pointer border text-xs transition-colors flex items-center justify-between ${
                        isSelected
                          ? 'bg-zinc-800 border-zinc-600 text-white'
                          : 'bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="w-3.5 h-3.5 flex-shrink-0 text-zinc-400" />
                        <span className="font-mono truncate">{d.original_filename}</span>
                      </div>
                      <span className="text-[10px] text-zinc-400 font-mono">
                        {formatBytes(d.file_size_bytes)}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* OCR Engine Controls */}
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-4 space-y-3 text-xs">
            <div className="flex items-center gap-2 text-zinc-300 font-semibold uppercase tracking-wider text-[11px]">
              <Sliders className="w-3.5 h-3.5" />
              <span>OCR Engine Options</span>
            </div>

            <div className="space-y-2">
              {/* Provider selector */}
              <div>
                <label className="text-zinc-400 block mb-1">Provider</label>
                <select
                  value={ocrProvider}
                  onChange={(e) => setOcrProvider(e.target.value as 'tesseract' | 'mock_vision')}
                  className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono focus:border-zinc-600 outline-none"
                >
                  <option value="tesseract">Tesseract OCR</option>
                  <option value="mock_vision">Mock Vision OCR</option>
                </select>
              </div>

              {/* Mock mode warning */}
              {ocrProvider === 'mock_vision' && (
                <div className="px-3 py-2 rounded bg-amber-950/40 border border-amber-800/50 text-amber-400 font-mono text-[11px]">
                  ⚠ Mock Vision mode — synthetic output for demonstration
                </div>
              )}

              <div>
                <label className="text-zinc-400 block mb-1">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono focus:border-zinc-600 outline-none"
                >
                  <option value="eng">English (eng)</option>
                  <option value="fra">French (fra)</option>
                  <option value="deu">German (deu)</option>
                  <option value="spa">Spanish (spa)</option>
                </select>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1">Page Segmentation Mode (PSM)</label>
                <select
                  value={psm}
                  onChange={(e) => setPsm(Number(e.target.value))}
                  className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono focus:border-zinc-600 outline-none"
                >
                  <option value={3}>3 - Fully automatic page segmentation</option>
                  <option value={4}>4 - Assume a single column of text</option>
                  <option value={6}>6 - Assume a single uniform block of text (Default)</option>
                  <option value={11}>11 - Sparse text: find as much text as possible</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Right Main Viewer Panel (8 cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-3">
          {/* Sub-tabs header */}
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-2 flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setActiveSubTab('visual')}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  activeSubTab === 'visual'
                    ? 'bg-zinc-800 text-white border border-zinc-700'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Visual Bounding Boxes
              </button>
              <button
                onClick={() => setActiveSubTab('text')}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  activeSubTab === 'text'
                    ? 'bg-zinc-800 text-white border border-zinc-700'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Raw OCR Text
              </button>
              <button
                onClick={() => setActiveSubTab('tokens')}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  activeSubTab === 'tokens'
                    ? 'bg-zinc-800 text-white border border-zinc-700'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Word Tokens ({wordsForCurrentPage.length})
              </button>
            </div>

            {/* Page navigator if multi-page */}
            {selectedDoc && (selectedDoc.page_count || 1) > 1 && (
              <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-400">
                <span>Page:</span>
                {Array.from({ length: selectedDoc.page_count || 1 }).map((_, i) => (
                  <button
                    key={i + 1}
                    onClick={() => setSelectedPageNum(i + 1)}
                    className={`w-6 h-6 rounded flex items-center justify-center ${
                      selectedPageNum === i + 1
                        ? 'bg-zinc-200 text-zinc-950 font-bold'
                        : 'bg-zinc-900 text-zinc-400 hover:text-white'
                    }`}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            )}

            {/* Provider badge */}
            {ocrResult && (
              <span className="text-[10px] font-mono text-zinc-500 ml-auto">
                Processed by: <span className="text-zinc-300">{ocrResult.provider || ocrProvider}</span>
              </span>
            )}
          </div>

          {/* Content Area */}
          <div className="h-[620px]">
            {activeSubTab === 'visual' && (
              <BoundingBoxOverlay
                imageUrl={
                  selectedDoc
                    ? api.getDocumentPageImageUrl(selectedDoc.id, selectedPageNum)
                    : undefined
                }
                words={wordsForCurrentPage}
                pageWidth={currentPage?.width || 1000}
                pageHeight={currentPage?.height || 1400}
                selectedWord={selectedWord}
                onSelectWord={(w) => setSelectedWord(w)}
              />
            )}

            {activeSubTab === 'text' && (
              <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg h-full flex flex-col p-4">
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-3">
                  <div className="text-xs font-mono text-zinc-400">
                    Character count: {ocrResult?.full_text?.length || 0}
                  </div>
                  <button
                    onClick={handleCopyText}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy Text'}</span>
                  </button>
                </div>
                <textarea
                  readOnly
                  value={ocrResult?.full_text || 'No OCR text extracted yet. Run OCR to inspect text.'}
                  className="w-full flex-1 bg-[#09090b] border border-zinc-800 rounded p-3 font-mono text-xs text-zinc-200 resize-none outline-none focus:border-zinc-700"
                />
              </div>
            )}

            {activeSubTab === 'tokens' && (
              <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg h-full flex flex-col p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="relative flex-1">
                    <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-zinc-400" />
                    <input
                      type="text"
                      placeholder="Filter tokens by text..."
                      value={textSearch}
                      onChange={(e) => setTextSearch(e.target.value)}
                      className="w-full bg-[#121215] border border-zinc-800 rounded pl-8 pr-3 py-1.5 text-xs font-mono text-zinc-200 outline-none focus:border-zinc-700"
                    />
                  </div>
                </div>

                <div className="flex-1 overflow-auto border border-zinc-800 rounded">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#121215] sticky top-0 border-b border-zinc-800 text-zinc-400 text-[11px]">
                      <tr>
                        <th className="px-3 py-2">Index</th>
                        <th className="px-3 py-2">Token</th>
                        <th className="px-3 py-2">Confidence</th>
                        <th className="px-3 py-2">BBox [x, y, w, h]</th>
                        <th className="px-3 py-2">Line #</th>
                        <th className="px-3 py-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/60">
                      {wordsForCurrentPage
                        .filter((w) =>
                          textSearch ? w.text.toLowerCase().includes(textSearch.toLowerCase()) : true
                        )
                        .map((w, idx) => (
                          <tr
                            key={idx}
                            className="hover:bg-zinc-900/50 cursor-pointer"
                            onClick={() => setSelectedWord(w)}
                          >
                            <td className="px-3 py-2 text-zinc-400">{w.word_index}</td>
                            <td className="px-3 py-2 text-zinc-100 font-semibold">{w.text}</td>
                            <td className="px-3 py-2">
                              <span
                                className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold border ${getConfidenceBadge(
                                  w.confidence
                                )}`}
                              >
                                {Math.round(w.confidence * 100)}%
                              </span>
                            </td>
                            <td className="px-3 py-2 text-zinc-400">
                              [{w.bounding_box.x}, {w.bounding_box.y}, {w.bounding_box.width},{' '}
                              {w.bounding_box.height}]
                            </td>
                            <td className="px-3 py-2 text-zinc-400">{w.line_number}</td>
                            <td className="px-3 py-2 text-right">
                              {onSendToRuleBuilder && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onSendToRuleBuilder(w.text);
                                  }}
                                  className="text-[11px] font-sans text-zinc-300 hover:text-white px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700"
                                >
                                  Use as Anchor
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
