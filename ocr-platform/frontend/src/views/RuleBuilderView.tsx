import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  api,
  Configuration,
  ConfigurationVersion,
  ExtractionField,
  ExtractionRule,
  DocumentItem,
  ExtractionResult,
} from '../lib/api';
import {
  Sliders,
  Plus,
  Trash2,
  Play,
  Save,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  ShieldAlert,
  ChevronRight,
  Eye,
} from 'lucide-react';
import { getConfidenceBadge } from '../lib/utils';

interface RuleBuilderViewProps {
  initialAnchor?: string | null;
}

export const RuleBuilderView: React.FC<RuleBuilderViewProps> = ({ initialAnchor }) => {
  const [configs, setConfigs] = useState<Configuration[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<Configuration | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<ConfigurationVersion | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [testDocumentId, setTestDocumentId] = useState<string>('');

  // Active fields inside the editor
  const [fields, setFields] = useState<ExtractionField[]>([]);
  const [activeFieldIndex, setActiveFieldIndex] = useState<number>(0);

  // Live test result
  const [testResult, setTestResult] = useState<ExtractionResult | null>(null);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  // New config modal state
  const [showNewModal, setShowNewModal] = useState(false);
  const [newConfigName, setNewConfigName] = useState('');
  const [newConfigSlug, setNewConfigSlug] = useState('');

  // Load configs and docs
  useEffect(() => {
    loadConfigurations();
    api.listDocuments(0, 50).then((docs) => {
      setDocuments(docs);
      if (docs.length > 0) {
        setTestDocumentId(docs[0].id);
      }
    });
  }, []);

  const loadConfigurations = async () => {
    try {
      const data = await api.listConfigurations();
      setConfigs(data);
      if (data.length > 0 && !selectedConfig) {
        selectConfiguration(data[0]);
      }
    } catch (err) {
      console.error('Failed to load configurations:', err);
    }
  };

  const selectConfiguration = async (cfg: Configuration) => {
    setSelectedConfig(cfg);
    setTestResult(null);
    if (cfg.versions && cfg.versions.length > 0) {
      const latestVerId = cfg.versions[cfg.versions.length - 1].id;
      try {
        const ver = await api.getConfigurationVersion(cfg.id, latestVerId);
        setSelectedVersion(ver);
        if (ver.fields && ver.fields.length > 0) {
          setFields(ver.fields);
          setActiveFieldIndex(0);
        } else {
          initDefaultFields();
        }
      } catch {
        initDefaultFields();
      }
    } else {
      initDefaultFields();
    }
  };

  const initDefaultFields = () => {
    const defaultField: ExtractionField = {
      field_id: 'invoice_number',
      display_name: 'Invoice Number',
      output_variable: 'invoice_number',
      output_type: 'string',
      required: true,
      priority: 100,
      rules: [
        {
          rule_name: 'Anchor Invoice No',
          strategy: 'same_line',
          anchor_config: {
            value: initialAnchor || 'Invoice No',
            match: 'fuzzy',
            minimum_similarity: 0.85,
          },
          search_config: {
            direction: 'after',
            scope: 'same_line',
            max_lines: 3,
          },
          pattern_config: {
            type: 'regex',
            value: 'INV-\\d{4}-\\d+',
            named_type: '',
          },
          priority: 100,
          is_enabled: true,
        },
      ],
    };
    setFields([defaultField]);
    setActiveFieldIndex(0);
  };

  const handleAddField = () => {
    const newIdx = fields.length + 1;
    const newField: ExtractionField = {
      field_id: `field_${newIdx}`,
      display_name: `New Field ${newIdx}`,
      output_variable: `field_${newIdx}`,
      output_type: 'string',
      required: false,
      priority: 100,
      rules: [
        {
          rule_name: 'Rule 1',
          strategy: 'same_line',
          anchor_config: {
            value: '',
            match: 'fuzzy',
            minimum_similarity: 0.85,
          },
          search_config: {
            direction: 'after',
            scope: 'same_line',
            max_lines: 3,
          },
          pattern_config: {
            type: 'regex',
            value: '.*',
          },
          priority: 100,
          is_enabled: true,
        },
      ],
    };
    setFields([...fields, newField]);
    setActiveFieldIndex(fields.length);
  };

  const handleDeleteField = (index: number) => {
    if (fields.length <= 1) return;
    const updated = fields.filter((_, i) => i !== index);
    setFields(updated);
    setActiveFieldIndex(Math.max(0, index - 1));
  };

  const updateActiveField = (patch: Partial<ExtractionField>) => {
    setFields((prev) => {
      const copy = [...prev];
      copy[activeFieldIndex] = { ...copy[activeFieldIndex], ...patch };
      return copy;
    });
  };

  const updateActiveRule = (patch: Partial<ExtractionRule>) => {
    setFields((prev) => {
      const copy = [...prev];
      const curField = copy[activeFieldIndex];
      if (curField.rules.length === 0) return prev;
      curField.rules[0] = { ...curField.rules[0], ...patch };
      return copy;
    });
  };

  const handleSaveVersion = async () => {
    if (!selectedConfig) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const snapshot = JSON.stringify({
        schema_version: 1,
        fields,
      });
      const ver = await api.createConfigurationVersion(selectedConfig.id, {
        config_snapshot: snapshot,
        change_notes: `Updated ${fields.length} extraction fields`,
        fields,
      });
      setSelectedVersion(ver);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      await loadConfigurations();
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateConfiguration = async () => {
    if (!newConfigName || !newConfigSlug) return;
    try {
      const created = await api.createConfiguration({
        name: newConfigName,
        slug: newConfigSlug,
        description: 'Created via Visual Rule Builder',
      });
      setShowNewModal(false);
      setNewConfigName('');
      setNewConfigSlug('');
      await loadConfigurations();
      selectConfiguration(created);
    } catch (err: any) {
      alert(`Create failed: ${err.message}`);
    }
  };

  const handleLiveTest = async () => {
    if (!testDocumentId) {
      alert('Please select a document to test against');
      return;
    }
    setIsTesting(true);
    setTestResult(null);
    try {
      // First save draft version to ensure backend tests with latest edits
      if (selectedConfig) {
        const snapshot = JSON.stringify({ schema_version: 1, fields });
        const ver = await api.createConfigurationVersion(selectedConfig.id, {
          config_snapshot: snapshot,
          change_notes: 'Draft for live test',
          fields,
        });
        setSelectedVersion(ver);
        const result = await api.testConfigurationVersion(ver.id, testDocumentId);
        setTestResult(result);
      }
    } catch (err: any) {
      alert(`Test failed: ${err.message}`);
    } finally {
      setIsTesting(false);
    }
  };

  const activeField = fields[activeFieldIndex];
  const activeRule = activeField?.rules[0];

  // Regex safety preview check
  // AI Suggest panel state
  const [showAISuggest, setShowAISuggest] = useState(false);
  const [aiOCRText, setAiOCRText] = useState('');
  const [aiSuggestions, setAiSuggestions] = useState<Array<{
    field_name: string;
    confidence: number;
    matched_alias: string;
    pattern: string | null;
    example: string;
    strategy: string;
  }>>([]);
  const [aiLoading, setAiLoading] = useState(false);

  const handleAIAnalyze = async () => {
    if (!aiOCRText.trim()) return;
    setAiLoading(true);
    try {
      const res = await fetch('/api/intelligence/suggest-rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ocr_text: aiOCRText, top_k: 10 }),
      });
      const data = await res.json();
      setAiSuggestions(data.suggestions || []);
    } catch (e) {
      console.error('AI suggest failed:', e);
    } finally {
      setAiLoading(false);
    }
  };

  const applyAISuggestion = (s: { field_name: string; pattern: string | null }) => {
    const activeField = fields[activeFieldIndex];
    if (!activeField) return;
    const updated = fields.map((f, i) =>
      i === activeFieldIndex
        ? {
            ...f,
            name: s.field_name,
            output_variable: s.field_name,
            rules: f.rules.map((r, ri) =>
              ri === 0 && s.pattern ? { ...r, pattern: s.pattern } : r
            ),
          }
        : f
    );
    setFields(updated);
    setShowAISuggest(false);
  };

  const isRegexSafe = (regexStr?: string): boolean => {
    if (!regexStr) return true;
    if (regexStr.includes('(.*).*') || regexStr.includes('(.+)+')) return false;
    return true;
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 font-sans">
            Visual Extraction Rule Builder
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Configure declarative anchor labels, search geometries, patterns, and run live verification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Config selector */}
          <div className="flex items-center gap-2">
            <select
              value={selectedConfig?.id || ''}
              onChange={(e) => {
                const found = configs.find((c) => c.id === e.target.value);
                if (found) selectConfiguration(found);
              }}
              className="bg-[#121215] border border-zinc-800 rounded px-3 py-1.5 text-xs font-mono text-zinc-200 outline-none focus:border-zinc-600"
            >
              {configs.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.slug})
                </option>
              ))}
            </select>

            <button
              onClick={() => setShowNewModal(true)}
              className="px-2.5 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs text-zinc-200 font-mono"
            >
              + New
            </button>
          </div>

          <button
            onClick={() => setShowAISuggest(true)}
            className="px-3.5 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs text-zinc-200 font-mono flex items-center gap-1.5 transition-colors"
            title="AI-assisted rule suggestions"
          >
            <span>✦</span>
            <span>AI Suggest</span>
          </button>

          <button
            onClick={handleSaveVersion}
            disabled={isSaving}
            className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            {saveSuccess ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            <span>{isSaving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Version'}</span>
          </button>
        </div>
      </div>

      {/* Editor Main Grid: 3-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Field List (3 cols) */}
        <div className="lg:col-span-3 space-y-3">
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-3">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800 mb-2">
              <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                Extraction Fields ({fields.length})
              </span>
              <button
                onClick={handleAddField}
                className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800 transition-colors"
                title="Add Field"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-1">
              {fields.map((f, idx) => {
                const isActive = idx === activeFieldIndex;
                return (
                  <div
                    key={idx}
                    onClick={() => setActiveFieldIndex(idx)}
                    className={`p-2.5 rounded cursor-pointer border text-xs transition-colors flex items-center justify-between ${
                      isActive
                        ? 'bg-zinc-800 border-zinc-600 text-white'
                        : 'bg-zinc-900/40 border-zinc-800/80 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                    }`}
                  >
                    <div className="truncate">
                      <div className="font-semibold text-zinc-200 truncate">{f.display_name}</div>
                      <div className="font-mono text-[10px] text-zinc-400 truncate">
                        {f.field_id} &middot; {f.output_type}
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      {f.required && (
                        <span className="text-[10px] text-amber-400 font-mono">*req</span>
                      )}
                      {fields.length > 1 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteField(idx);
                          }}
                          className="text-zinc-500 hover:text-rose-400 p-1"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Middle Column: Field & Rule Inspector (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {activeField && (
            <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 space-y-5 text-xs">
              {/* Field Identity */}
              <div className="space-y-3 pb-4 border-b border-zinc-800">
                <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                  Field Definition
                </h3>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-zinc-400 block mb-1">Display Name</label>
                    <input
                      type="text"
                      value={activeField.display_name}
                      onChange={(e) => updateActiveField({ display_name: e.target.value })}
                      className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                    />
                  </div>
                  <div>
                    <label className="text-zinc-400 block mb-1">Field ID</label>
                    <input
                      type="text"
                      value={activeField.field_id}
                      onChange={(e) => updateActiveField({ field_id: e.target.value })}
                      className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-zinc-400 block mb-1">Output Type</label>
                    <select
                      value={activeField.output_type}
                      onChange={(e) => updateActiveField({ output_type: e.target.value })}
                      className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                    >
                      <option value="string">String</option>
                      <option value="integer">Integer</option>
                      <option value="decimal">Decimal</option>
                      <option value="date">Date</option>
                      <option value="currency">Currency</option>
                      <option value="boolean">Boolean</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2 pt-5">
                    <input
                      type="checkbox"
                      id="field-required"
                      checked={activeField.required}
                      onChange={(e) => updateActiveField({ required: e.target.checked })}
                      className="accent-white rounded cursor-pointer"
                    />
                    <label htmlFor="field-required" className="text-zinc-300 font-medium cursor-pointer">
                      Required Field
                    </label>
                  </div>
                </div>
              </div>

              {/* Extraction Rule Settings */}
              {activeRule && (
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                    Extraction Strategy & Geometry
                  </h3>

                  {/* Strategy */}
                  <div>
                    <label className="text-zinc-400 block mb-1">Strategy</label>
                    <select
                      value={activeRule.strategy}
                      onChange={(e) => updateActiveRule({ strategy: e.target.value })}
                      className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                    >
                      <option value="same_line">same_line — Look immediately after anchor on same line</option>
                      <option value="next_line">next_line — Look on line directly beneath anchor</option>
                      <option value="anchored_pattern">anchored_pattern — Pattern in proximity to anchor</option>
                      <option value="direct_pattern">direct_pattern — Global regex search (no anchor)</option>
                      <option value="region">region — Fixed bounding box coordinates</option>
                      <option value="table">table — Line-item tabular data extractor</option>
                    </select>
                  </div>

                  {/* Anchor configuration (if not direct_pattern) */}
                  {activeRule.strategy !== 'direct_pattern' && activeRule.strategy !== 'region' && (
                    <div className="p-3 bg-[#101014] border border-zinc-800 rounded-md space-y-3">
                      <div className="font-semibold text-zinc-300 text-[11px] uppercase tracking-wider">
                        Anchor Label Config
                      </div>

                      <div>
                        <label className="text-zinc-400 block mb-1">Anchor Label Text</label>
                        <input
                          type="text"
                          placeholder="e.g. Invoice No, Total Due, Date"
                          value={activeRule.anchor_config?.value || ''}
                          onChange={(e) =>
                            updateActiveRule({
                              anchor_config: {
                                ...activeRule.anchor_config,
                                value: e.target.value,
                                match: activeRule.anchor_config?.match || 'fuzzy',
                                minimum_similarity: activeRule.anchor_config?.minimum_similarity ?? 0.85,
                              },
                            })
                          }
                          className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-zinc-400 block mb-1">Matching Mode</label>
                          <select
                            value={activeRule.anchor_config?.match || 'fuzzy'}
                            onChange={(e: any) =>
                              updateActiveRule({
                                anchor_config: {
                                  ...activeRule.anchor_config!,
                                  match: e.target.value,
                                },
                              })
                            }
                            className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                          >
                            <option value="fuzzy">Fuzzy Match</option>
                            <option value="exact">Exact Match</option>
                            <option value="regex">Regex Match</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-zinc-400 block mb-1">
                            Min Similarity ({Math.round((activeRule.anchor_config?.minimum_similarity ?? 0.85) * 100)}%)
                          </label>
                          <input
                            type="range"
                            min="0.5"
                            max="1.0"
                            step="0.05"
                            value={activeRule.anchor_config?.minimum_similarity ?? 0.85}
                            onChange={(e) =>
                              updateActiveRule({
                                anchor_config: {
                                  ...activeRule.anchor_config!,
                                  minimum_similarity: parseFloat(e.target.value),
                                },
                              })
                            }
                            className="w-full accent-zinc-200"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Pattern Configuration */}
                  <div className="p-3 bg-[#101014] border border-zinc-800 rounded-md space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-zinc-300 text-[11px] uppercase tracking-wider">
                        Value Pattern (Regex / Template)
                      </span>
                      {isRegexSafe(activeRule.pattern_config?.value) ? (
                        <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                          <ShieldCheck className="w-3 h-3" />
                          ReDoS Safe
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[10px] text-rose-400 font-mono">
                          <ShieldAlert className="w-3 h-3" />
                          Dangerous Pattern
                        </span>
                      )}
                    </div>

                    <div>
                      <label className="text-zinc-400 block mb-1">Pattern Value</label>
                      <input
                        type="text"
                        placeholder="e.g. INV-\d{4}-\d+ or \d{2}/\d{2}/\d{4}"
                        value={activeRule.pattern_config?.value || ''}
                        onChange={(e) =>
                          updateActiveRule({
                            pattern_config: {
                              ...activeRule.pattern_config,
                              type: 'regex',
                              value: e.target.value,
                            },
                          })
                        }
                        className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Live Test & Evidence Panel (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                Live Rule Verification
              </h3>
              <button
                onClick={handleLiveTest}
                disabled={isTesting || !testDocumentId}
                className="px-3 py-1.5 rounded bg-zinc-200 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50 transition-colors"
              >
                <Play className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
                <span>{isTesting ? 'Testing...' : 'Run Test'}</span>
              </button>
            </div>

            <div>
              <label className="text-xs text-zinc-400 block mb-1 font-mono">
                Target Test Document
              </label>
              <select
                value={testDocumentId}
                onChange={(e) => setTestDocumentId(e.target.value)}
                className="w-full bg-[#121215] border border-zinc-800 rounded px-2.5 py-1.5 text-xs font-mono text-zinc-200 outline-none focus:border-zinc-600"
              >
                {documents.length === 0 ? (
                  <option value="">No documents uploaded</option>
                ) : (
                  documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Test Results Output */}
            <div>
              <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2 font-mono">
                Extracted Values & Evidence
              </span>

              {testResult ? (
                <div className="space-y-2">
                  <div className="p-2.5 bg-zinc-900/60 border border-zinc-800 rounded text-xs font-mono flex items-center justify-between">
                    <span className="text-zinc-400">Overall Confidence:</span>
                    <span className="font-bold text-emerald-400">
                      {Math.round((testResult.overall_confidence || 0) * 100)}%
                    </span>
                  </div>

                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {testResult.values.map((v, i) => (
                      <div
                        key={i}
                        className="p-3 bg-[#111115] border border-zinc-800 rounded space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-zinc-200 font-mono text-xs">
                            {v.output_variable}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getConfidenceBadge(
                              v.final_confidence
                            )}`}
                          >
                            {Math.round((v.final_confidence || 0) * 100)}%
                          </span>
                        </div>

                        <div className="text-zinc-100 font-mono text-xs font-medium bg-zinc-900 px-2 py-1 rounded border border-zinc-800">
                          {v.normalized_value || <span className="text-zinc-500">Not found</span>}
                        </div>

                        {v.evidence && v.evidence.length > 0 && (
                          <div className="text-[10px] text-zinc-400 font-mono pt-1">
                            <div>Matched Line: "{v.evidence[0].source_line}"</div>
                            {v.evidence[0].bbox_x !== undefined && (
                              <div>
                                Box: [{v.evidence[0].bbox_x}, {v.evidence[0].bbox_y},{' '}
                                {v.evidence[0].bbox_width}, {v.evidence[0].bbox_height}]
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-6 border border-dashed border-zinc-800 rounded text-center text-xs font-mono text-zinc-400">
                  Select a document and click "Run Test" to verify rules against real OCR output.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* New Configuration Modal */}
      <AnimatePresence>
        {showNewModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0e0e12] border border-zinc-800 rounded-lg max-w-md w-full p-6 space-y-4 shadow-xl"
            >
              <h3 className="text-base font-semibold text-white font-sans">
                Create Extraction Configuration
              </h3>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-zinc-400 block mb-1">Configuration Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Supplier Invoice Parser"
                    value={newConfigName}
                    onChange={(e) => {
                      setNewConfigName(e.target.value);
                      if (!newConfigSlug) {
                        setNewConfigSlug(
                          e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
                        );
                      }
                    }}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Slug Identifier</label>
                  <input
                    type="text"
                    placeholder="e.g. supplier_invoice"
                    value={newConfigSlug}
                    onChange={(e) => setNewConfigSlug(e.target.value)}
                    className="w-full bg-[#141418] border border-zinc-800 rounded px-2.5 py-2 text-zinc-200 font-mono outline-none focus:border-zinc-600"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowNewModal(false)}
                  className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white text-xs"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateConfiguration}
                  disabled={!newConfigName || !newConfigSlug}
                  className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold disabled:opacity-50"
                >
                  Create
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ✦ AI Suggest slide-in panel */}
      <AnimatePresence>
        {showAISuggest && (
          <div className="fixed inset-0 z-50 flex justify-end">
            {/* backdrop */}
            <motion.div
              className="absolute inset-0 bg-zinc-950/70"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAISuggest(false)}
            />
            {/* panel */}
            <motion.div
              className="relative w-full max-w-md bg-zinc-900 border-l border-zinc-800 flex flex-col h-full overflow-y-auto"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            >
              {/* Panel header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
                <div>
                  <p className="text-sm font-semibold text-white font-sans">✦ AI Rule Suggestions</p>
                  <p className="text-xs text-zinc-500 font-mono mt-0.5">Paste OCR text — get field candidates instantly</p>
                </div>
                <button
                  onClick={() => setShowAISuggest(false)}
                  className="text-zinc-500 hover:text-white transition-colors text-lg leading-none"
                >
                  ×
                </button>
              </div>

              {/* OCR text input */}
              <div className="px-5 py-4 space-y-3 border-b border-zinc-800">
                <textarea
                  value={aiOCRText}
                  onChange={(e) => setAiOCRText(e.target.value)}
                  placeholder="Paste raw OCR text here…"
                  rows={6}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs font-mono text-zinc-200 outline-none focus:border-zinc-600 resize-none"
                />
                <button
                  onClick={handleAIAnalyze}
                  disabled={aiLoading || !aiOCRText.trim()}
                  className="w-full px-4 py-2 rounded bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-950 text-xs font-semibold transition-colors"
                >
                  {aiLoading ? 'Analyzing…' : 'Analyze'}
                </button>
              </div>

              {/* Suggestion cards */}
              <div className="flex-1 px-5 py-4 space-y-3">
                {aiSuggestions.length === 0 && !aiLoading && (
                  <p className="text-xs text-zinc-600 font-mono text-center pt-8">
                    No suggestions yet — paste OCR text above and click Analyze.
                  </p>
                )}
                {aiSuggestions.map((s, i) => (
                  <motion.button
                    key={s.field_name}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04, type: 'spring', stiffness: 400, damping: 30 }}
                    onClick={() => applyAISuggestion(s)}
                    className="w-full text-left bg-zinc-950 border border-zinc-800 hover:border-zinc-600 rounded-lg px-4 py-3 space-y-2 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white font-mono">{s.field_name}</span>
                      <span className="text-xs text-zinc-500 font-mono">{Math.round(s.confidence * 100)}%</span>
                    </div>
                    {/* confidence bar */}
                    <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden" role="progressbar" aria-valuenow={Math.round(s.confidence * 100)} aria-valuemin={0} aria-valuemax={100}>
                      <div className="h-1 bg-zinc-300 rounded-full" style={{ width: `${Math.round(s.confidence * 100)}%` }} />
                    </div>
                    {s.matched_alias && (
                      <p className="text-xs text-zinc-500 font-mono">alias: <span className="text-zinc-300">{s.matched_alias}</span></p>
                    )}
                    {s.pattern && (
                      <p className="text-xs text-zinc-600 font-mono truncate">pattern: <span className="text-emerald-400">{s.pattern}</span></p>
                    )}
                    <p className="text-xs text-zinc-600 font-mono">e.g. <span className="text-zinc-400">{s.example}</span> · {s.strategy}</p>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
