import React, { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Play, Trash2, RefreshCw, Layers } from 'lucide-react';
import { setupApi, SetupItem, FieldItem } from '../lib/setupApi';
import { FieldCard } from '../components/setup/FieldCard';
import { AddFieldModal } from '../components/setup/AddFieldModal';

interface SetupDetailViewProps {
  setupId: string;
  onBack: () => void;
  onScan: (setupId: string) => void;
  onOpenAdvancedRuleEditor: (configId: string, fieldId?: string) => void;
}

export const SetupDetailView: React.FC<SetupDetailViewProps> = ({
  setupId,
  onBack,
  onScan,
  onOpenAdvancedRuleEditor,
}) => {
  const [setup, setSetup] = useState<SetupItem | null>(null);
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const s = await setupApi.getSetup(setupId);
      setSetup(s);
      const f = await setupApi.listFields(setupId);
      setFields(f);
    } catch (err) {
      console.error('Failed to load setup details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [setupId]);

  const handleRemoveField = async (fieldId: string) => {
    try {
      await setupApi.deleteField(setupId, fieldId);
      setFields((prev) => prev.filter((f) => f.field_id !== fieldId));
    } catch (err) {
      console.error('Failed to delete field:', err);
    }
  };

  const handleFieldAdded = (newField: FieldItem) => {
    setFields((prev) => [...prev, newField]);
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
            title="Back to Setups"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-zinc-100">
                {setup?.name || 'Setup Details'}
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-zinc-800 text-zinc-300 border border-zinc-700">
                {setup?.status === 'ready' ? 'Ready' : 'Draft'}
              </span>
            </div>
            {setup?.description && (
              <p className="text-xs text-zinc-400 font-mono mt-0.5">
                {setup.description}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onScan(setupId)}
            className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Scan with this Setup</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-mono flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Something</span>
          </button>
        </div>
      </div>

      {/* Fields List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 font-mono">
            Information Configured to Extract ({fields.length})
          </h2>
          <button
            onClick={() => onOpenAdvancedRuleEditor(setupId)}
            className="text-xs font-mono text-zinc-400 hover:text-zinc-200 underline transition-colors"
          >
            Open in Advanced Rule Editor →
          </button>
        </div>

        {isLoading ? (
          <div className="py-16 text-center text-xs font-mono text-zinc-500">
            Loading fields...
          </div>
        ) : fields.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-zinc-800 rounded-xl space-y-3">
            <p className="text-sm text-zinc-300">No fields configured in this setup yet.</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold inline-flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add First Field</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {fields.map((field) => (
              <FieldCard
                key={field.field_id}
                field={field}
                onRemove={handleRemoveField}
                onOpenAdvanced={(fid) => onOpenAdvancedRuleEditor(setupId, fid)}
              />
            ))}
          </div>
        )}
      </div>

      <AddFieldModal
        setupId={setupId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onFieldAdded={handleFieldAdded}
      />
    </div>
  );
};
