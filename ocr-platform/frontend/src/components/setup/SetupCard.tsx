import React from 'react';
import { Play, Edit, FileText, ArrowRight } from 'lucide-react';
import { SetupItem } from '../../lib/setupApi';

interface SetupCardProps {
  setup: SetupItem;
  onScan: (setup: SetupItem) => void;
  onEdit: (setup: SetupItem) => void;
  onViewResults: (setup: SetupItem) => void;
}

export const SetupCard: React.FC<SetupCardProps> = ({
  setup,
  onScan,
  onEdit,
  onViewResults,
}) => {
  return (
    <div className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl p-5 space-y-4 transition-all">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-zinc-100 font-sans">
            {setup.name}
          </h3>
          <p className="text-xs text-zinc-400 font-mono mt-1">
            {setup.field_count} {setup.field_count === 1 ? 'field' : 'fields'} configured
          </p>
        </div>

        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          {setup.status === 'ready' ? 'Ready to scan' : 'Draft'}
        </span>
      </div>

      {setup.description && (
        <p className="text-xs text-zinc-400 line-clamp-2">
          {setup.description}
        </p>
      )}

      <div className="pt-2 border-t border-zinc-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => onScan(setup)}
            className="px-3.5 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Scan</span>
          </button>

          <button
            onClick={() => onEdit(setup)}
            className="px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-mono flex items-center gap-1.5 transition-colors"
          >
            <Edit className="w-3.5 h-3.5" />
            <span>Edit</span>
          </button>
        </div>

        <button
          onClick={() => onViewResults(setup)}
          className="text-xs font-mono text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition-colors"
        >
          <span>Results</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
