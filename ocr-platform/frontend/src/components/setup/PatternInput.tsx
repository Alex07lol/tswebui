import React, { useState } from 'react';
import { Sparkles, FileText, List, MessageSquare } from 'lucide-react';
import { PATTERN_TOKENS, patternParserApi } from '../../lib/patternParser';

interface PatternInputProps {
  value: string;
  onChange: (humanPattern: string, examples?: string[], description?: string, inferredType?: string) => void;
  initialExamples?: string[];
  initialDescription?: string;
}

export const PatternInput: React.FC<PatternInputProps> = ({
  value,
  onChange,
  initialExamples = [],
  initialDescription = '',
}) => {
  const [tab, setTab] = useState<'format' | 'examples' | 'select' | 'plain'>('format');
  const [examplesText, setExamplesText] = useState(initialExamples.join('\n'));
  const [descriptionText, setDescriptionText] = useState(initialDescription);
  const [sampleDocText, setSampleDocText] = useState('');
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [isInferring, setIsInferring] = useState(false);
  const [previewExample, setPreviewExample] = useState<string>('');

  const insertToken = (token: string) => {
    const nextVal = value ? `${value}-${token}` : token;
    onChange(nextVal);
  };

  const handleExamplesInfer = async () => {
    const lines = examplesText.split('\n').map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return;
    setIsInferring(true);
    try {
      const res = await patternParserApi.fromExamples(lines);
      onChange(res.inferred_human_pattern, lines, undefined, res.inferred_type);
      setPreviewExample(res.example_match);
    } catch (e) {
      console.error('Inference failed:', e);
    } finally {
      setIsInferring(false);
    }
  };

  const handleDescriptionInfer = async () => {
    if (!descriptionText.trim()) return;
    setIsInferring(true);
    try {
      const res = await patternParserApi.fromDescription(descriptionText);
      onChange(res.inferred_human_pattern, undefined, descriptionText, res.inferred_type);
      setPreviewExample(res.example_match);
    } catch (e) {
      console.error('Inference failed:', e);
    } finally {
      setIsInferring(false);
    }
  };

  const handleSelectSnippet = (word: string) => {
    setSelectedWord(word);
    const lines = [word];
    patternParserApi.fromExamples(lines).then((res) => {
      onChange(res.inferred_human_pattern, lines, undefined, res.inferred_type);
      setPreviewExample(res.example_match);
    });
  };

  return (
    <div className="space-y-4">
      {/* 4 Tabs */}
      <div className="flex border-b border-zinc-800 text-xs font-mono">
        <button
          type="button"
          onClick={() => setTab('format')}
          className={`px-3 py-2 border-b-2 font-semibold transition-colors ${
            tab === 'format'
              ? 'border-zinc-100 text-white'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          1. Describe Format
        </button>
        <button
          type="button"
          onClick={() => setTab('examples')}
          className={`px-3 py-2 border-b-2 font-semibold transition-colors ${
            tab === 'examples'
              ? 'border-zinc-100 text-white'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          2. Give Examples
        </button>
        <button
          type="button"
          onClick={() => setTab('select')}
          className={`px-3 py-2 border-b-2 font-semibold transition-colors ${
            tab === 'select'
              ? 'border-zinc-100 text-white'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          3. Select From Document
        </button>
        <button
          type="button"
          onClick={() => setTab('plain')}
          className={`px-3 py-2 border-b-2 font-semibold transition-colors ${
            tab === 'plain'
              ? 'border-zinc-100 text-white'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          4. Plain Language
        </button>
      </div>

      {/* Tab 1: Describe Format */}
      {tab === 'format' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-1">
              Pattern template:
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder="e.g. SN-{YYYY}-{NNNNNN} or INV-{NNNNN}"
              className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs font-mono text-zinc-100 outline-none focus:border-zinc-600"
            />
          </div>

          <div>
            <p className="text-[11px] font-mono text-zinc-500 mb-1.5">
              Click a building block to insert:
            </p>
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1 bg-zinc-950/60 rounded border border-zinc-900">
              {PATTERN_TOKENS.map((t) => (
                <button
                  key={t.token}
                  type="button"
                  onClick={() => insertToken(t.token)}
                  className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[11px] font-mono text-zinc-300 hover:text-white transition-colors"
                  title={`${t.label} (e.g. ${t.example})`}
                >
                  <span className="text-zinc-100 font-semibold">{t.token}</span>{' '}
                  <span className="text-zinc-500 text-[10px]">({t.label})</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Give Examples */}
      {tab === 'examples' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-1">
              Paste 2 or 3 examples (one per line):
            </label>
            <textarea
              rows={4}
              value={examplesText}
              onChange={(e) => setExamplesText(e.target.value)}
              placeholder="SN-2026-001234&#10;SN-2026-001235&#10;SN-2026-001236"
              className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs font-mono text-zinc-100 outline-none focus:border-zinc-600"
            />
          </div>
          <button
            type="button"
            onClick={handleExamplesInfer}
            disabled={isInferring || !examplesText.trim()}
            className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isInferring ? 'Detecting pattern...' : 'Learn pattern from examples'}</span>
          </button>
        </div>
      )}

      {/* Tab 3: Select from document */}
      {tab === 'select' && (
        <div className="space-y-3 text-xs font-mono">
          <div>
            <label className="block text-zinc-400 mb-1">
              Paste a snippet from your document:
            </label>
            <textarea
              rows={3}
              value={sampleDocText}
              onChange={(e) => setSampleDocText(e.target.value)}
              placeholder="e.g. Serial Number: SN-2026-004821 Model: XPS-15"
              className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs font-mono text-zinc-100 outline-none focus:border-zinc-600"
            />
          </div>

          {sampleDocText && (
            <div className="space-y-2">
              <p className="text-zinc-400 text-[11px]">Click on the value to select it:</p>
              <div className="flex flex-wrap gap-1.5 p-2 bg-zinc-950 rounded border border-zinc-800">
                {sampleDocText.split(/\s+/).map((word, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectSnippet(word)}
                    className={`px-2 py-0.5 rounded text-xs transition-colors ${
                      selectedWord === word
                        ? 'bg-emerald-950 border border-emerald-600 text-emerald-300 font-bold'
                        : 'bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white'
                    }`}
                  >
                    {word}
                  </button>
                ))}
              </div>

              {selectedWord && (
                <div className="p-2 bg-zinc-900/60 border border-zinc-800 rounded text-zinc-300 text-[11px]">
                  Looking for values similar to: <strong className="text-emerald-400">{selectedWord}</strong>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Plain Language */}
      {tab === 'plain' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-1">
              Describe the format in simple words:
            </label>
            <textarea
              rows={3}
              value={descriptionText}
              onChange={(e) => setDescriptionText(e.target.value)}
              placeholder="e.g. Starts with SN, followed by the year, then six numbers."
              className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs font-mono text-zinc-100 outline-none focus:border-zinc-600"
            />
          </div>
          <button
            type="button"
            onClick={handleDescriptionInfer}
            disabled={isInferring || !descriptionText.trim()}
            className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isInferring ? 'Interpreting...' : 'Convert to Pattern'}</span>
          </button>
        </div>
      )}

      {/* Live interpreted pattern banner */}
      {value && (
        <div className="p-2.5 bg-zinc-950 border border-zinc-800 rounded text-xs font-mono flex items-center justify-between">
          <div>
            <span className="text-zinc-500">Current Pattern: </span>
            <span className="text-zinc-100 font-bold">{value}</span>
          </div>
          {previewExample && (
            <span className="text-zinc-500 text-[11px]">
              Matches: <strong className="text-zinc-300">{previewExample}</strong>
            </span>
          )}
        </div>
      )}
    </div>
  );
};
