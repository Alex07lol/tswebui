import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, Sparkles } from 'lucide-react';
import { PatternInput } from './PatternInput';
import { setupApi, FieldItem } from '../../lib/setupApi';

interface AddFieldModalProps {
  setupId?: string;
  isOpen: boolean;
  onClose: () => void;
  onFieldAdded: (field: FieldItem) => void;
}

export const AddFieldModal: React.FC<AddFieldModalProps> = ({
  setupId,
  isOpen,
  onClose,
  onFieldAdded,
}) => {
  const [displayName, setDisplayName] = useState('');
  const [pattern, setPattern] = useState('');
  const [examples, setExamples] = useState<string[]>([]);
  const [description, setDescription] = useState('');
  const [outputType, setOutputType] = useState('text');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handlePatternChange = (
    newPat: string,
    newEx?: string[],
    newDesc?: string,
    inferredType?: string
  ) => {
    setPattern(newPat);
    if (newEx) setExamples(newEx);
    if (newDesc !== undefined) setDescription(newDesc);
    if (inferredType) setOutputType(inferredType);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim()) {
      setErrorMsg('Please give this field a name');
      return;
    }

    setIsSaving(true);
    setErrorMsg(null);

    try {
      if (setupId) {
        const added = await setupApi.addField(setupId, {
          display_name: displayName.trim(),
          human_pattern: pattern.trim() || undefined,
          examples: examples.length ? examples : undefined,
          description: description.trim() || undefined,
        });
        onFieldAdded(added);
      } else {
        // Local mode before setup is saved
        const slug = displayName.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
        const mockField: FieldItem = {
          field_id: slug || 'field_1',
          display_name: displayName.trim(),
          human_pattern: pattern.trim() || '{ANY}',
          output_type: outputType,
          status: 'ready',
          confidence_label: 'Very High',
          confidence_score: 0.95,
          explanation: ['Ready to extract with automatic strategy'],
        };
        onFieldAdded(mockField);
      }

      // Reset
      setDisplayName('');
      setPattern('');
      setExamples([]);
      setDescription('');
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to add field');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.96 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          className="relative w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden font-sans"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
            <div>
              <h3 className="text-base font-semibold text-zinc-100">
                Add Something to Find
              </h3>
              <p className="text-xs text-zinc-400 font-mono mt-0.5">
                Tell us what this information is and what it usually looks like.
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {errorMsg && (
              <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded text-rose-300 text-xs font-mono">
                {errorMsg}
              </div>
            )}

            {/* Step A: What should we call this? */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-300 font-mono">
                What should we call this?
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="e.g. Serial Number, Product ID, Invoice Date"
                className="w-full bg-zinc-950 border border-zinc-800 rounded px-3.5 py-2 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-zinc-500"
                autoFocus
              />
            </div>

            {/* Step B: What does it usually look like? */}
            <div className="space-y-1.5 pt-2 border-t border-zinc-800/80">
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-300 font-mono">
                What does it usually look like?
              </label>
              <PatternInput
                value={pattern}
                onChange={handlePatternChange}
                initialExamples={examples}
                initialDescription={description}
              />
            </div>

            {/* Inferred Output Type summary */}
            <div className="flex items-center justify-between p-3 bg-zinc-950/80 border border-zinc-800/80 rounded text-xs font-mono">
              <span className="text-zinc-400">Data Type:</span>
              <select
                value={outputType}
                onChange={(e) => setOutputType(e.target.value)}
                className="bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-zinc-200 outline-none capitalize"
              >
                <option value="text">Text / Code</option>
                <option value="date">Date</option>
                <option value="currency">Currency / Money</option>
                <option value="number">Number</option>
                <option value="boolean">Yes / No (Boolean)</option>
              </select>
            </div>

            {/* Footer Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving || !displayName.trim()}
                className="px-5 py-2 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Add This Field'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
