import React, { useState } from 'react';
import { Plus, ArrowLeft, Check, Save } from 'lucide-react';
import { setupApi, FieldItem } from '../lib/setupApi';
import { AddFieldModal } from '../components/setup/AddFieldModal';
import { FieldCard } from '../components/setup/FieldCard';

interface CreateSetupViewProps {
  onCancel: () => void;
  onSaved: (setupId: string) => void;
}

export const CreateSetupView: React.FC<CreateSetupViewProps> = ({
  onCancel,
  onSaved,
}) => {
  const [setupName, setSetupName] = useState('');
  const [description, setDescription] = useState('');
  const [step, setStep] = useState<1 | 2>(1);
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault();
    if (!setupName.trim()) return;
    setStep(2);
  };

  const handleFieldAdded = (newField: FieldItem) => {
    setFields((prev) => [...prev, newField]);
  };

  const handleRemoveField = (fieldId: string) => {
    setFields((prev) => prev.filter((f) => f.field_id !== fieldId));
  };

  const handleSaveSetup = async () => {
    if (!setupName.trim()) return;
    setIsSaving(true);
    setErrorMsg(null);
    try {
      // 1. Create setup
      const created = await setupApi.createSetup(setupName.trim(), description.trim());
      // 2. Add each field
      for (const f of fields) {
        await setupApi.addField(created.id, {
          display_name: f.display_name,
          human_pattern: f.human_pattern,
        });
      }
      onSaved(created.id);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save setup');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-8 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => (step === 2 ? setStep(1) : onCancel())}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
            title="Back"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-zinc-100">
              Create a Setup
            </h1>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Step {step} of 2: {step === 1 ? 'Name your document type' : 'Add what you want to extract'}
            </p>
          </div>
        </div>

        {step === 2 && (
          <button
            onClick={handleSaveSetup}
            disabled={isSaving || fields.length === 0}
            className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving...' : 'Save Setup'}</span>
          </button>
        )}
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-xs font-mono">
          {errorMsg}
        </div>
      )}

      {/* Step 1: Name */}
      {step === 1 && (
        <form onSubmit={handleNextStep} className="space-y-6 max-w-xl">
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-zinc-200">
              What kind of documents are these?
            </label>
            <input
              type="text"
              value={setupName}
              onChange={(e) => setSetupName(e.target.value)}
              placeholder="e.g. Laptop Warranty Documents, Supplier Invoices"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-zinc-500"
              autoFocus
            />
            <p className="text-xs text-zinc-500 font-mono">
              Give this setup a clear name so you can pick it whenever you scan.
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono">
              Optional description
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. For warranty slips, serial plates, and purchase receipts"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-xs text-zinc-100 placeholder-zinc-600 outline-none focus:border-zinc-500"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={!setupName.trim()}
              className="px-5 py-2.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold transition-colors disabled:opacity-50"
            >
              Continue to Step 2 →
            </button>
          </div>
        </form>
      )}

      {/* Step 2: Add Fields */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="p-4 bg-zinc-900/60 border border-zinc-800 rounded-lg flex items-center justify-between">
            <div>
              <span className="text-xs text-zinc-500 font-mono">Document Setup:</span>
              <h3 className="text-sm font-semibold text-zinc-200">{setupName}</h3>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-3.5 py-1.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Something</span>
            </button>
          </div>

          {/* Fields list */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono">
              Information to Find ({fields.length})
            </h4>

            {fields.length === 0 ? (
              <div className="text-center py-12 px-4 border border-dashed border-zinc-800 rounded-xl space-y-3">
                <p className="text-sm text-zinc-400">
                  No information fields added yet.
                </p>
                <p className="text-xs text-zinc-600 font-mono">
                  Click "+ Add Something" to define your first field (e.g. Serial Number, Date, Total).
                </p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-mono inline-flex items-center gap-2 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Something to Find</span>
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {fields.map((f) => (
                  <FieldCard
                    key={f.field_id}
                    field={f}
                    onRemove={handleRemoveField}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <AddFieldModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onFieldAdded={handleFieldAdded}
      />
    </div>
  );
};
