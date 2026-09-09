import React, { useState } from 'react';
import { Trash2, Edit2, Play, Settings, ChevronRight } from 'lucide-react';
import { FieldItem } from '../../lib/setupApi';
import { ConfidenceBadge } from '../ConfidenceBadge';

interface FieldCardProps {
  field: FieldItem;
  onEdit?: (field: FieldItem) => void;
  onTest?: (field: FieldItem) => void;
  onRemove?: (fieldId: string) => void;
  onOpenAdvanced?: (fieldId: string) => void;
}

export const FieldCard: React.FC<FieldCardProps> = ({
  field,
  onEdit,
  onTest,
  onRemove,
  onOpenAdvanced,
}) => {
  const [showConfirmRemove, setShowConfirmRemove] = useState(false);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3 transition-colors hover:border-zinc-700">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="text-sm font-semibold text-zinc-100 font-sans">
            {field.display_name}
          </h4>
          {field.human_pattern && (
            <p className="text-xs font-mono text-zinc-400 mt-1">
              Looks like: <span className="text-zinc-200 font-bold">{field.human_pattern}</span>
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <ConfidenceBadge
            score={field.confidence_score}
            label={field.confidence_label}
            why={field.explanation}
          />
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs font-mono text-zinc-500 pt-1 border-t border-zinc-800/60">
        <div>
          Type: <span className="text-zinc-300 capitalize">{field.output_type || 'Text'}</span>
        </div>
        <div>
          Status: <span className="text-emerald-400">● {field.status || 'Ready'}</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-zinc-800">
        <div className="flex items-center gap-2">
          {onEdit && (
            <button
              onClick={() => onEdit(field)}
              className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 flex items-center gap-1 transition-colors"
            >
              <Edit2 className="w-3 h-3" />
              <span>Edit</span>
            </button>
          )}

          {onTest && (
            <button
              onClick={() => onTest(field)}
              className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 flex items-center gap-1 transition-colors"
            >
              <Play className="w-3 h-3" />
              <span>Test</span>
            </button>
          )}

          {onRemove && (
            showConfirmRemove ? (
              <div className="flex items-center gap-1.5 text-xs font-mono">
                <span className="text-rose-400">Remove?</span>
                <button
                  onClick={() => onRemove(field.field_id)}
                  className="px-2 py-0.5 rounded bg-rose-950 border border-rose-800 text-rose-300 hover:bg-rose-900"
                >
                  Yes
                </button>
                <button
                  onClick={() => setShowConfirmRemove(false)}
                  className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 hover:text-white"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowConfirmRemove(true)}
                className="px-2.5 py-1 rounded hover:bg-zinc-800 text-xs font-mono text-zinc-500 hover:text-rose-400 flex items-center gap-1 transition-colors"
                title="Remove field"
              >
                <Trash2 className="w-3 h-3" />
                <span>Remove</span>
              </button>
            )
          )}
        </div>

        {onOpenAdvanced && (
          <button
            onClick={() => onOpenAdvanced(field.field_id)}
            className="text-xs font-mono text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition-colors"
            title="Open full technical rules editor"
          >
            <span>···Advanced</span>
          </button>
        )}
      </div>
    </div>
  );
};
