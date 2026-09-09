import React, { useState } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { CandidateItem } from '../lib/setupApi';
import { ConfidenceBadge } from './ConfidenceBadge';

interface AmbiguityPanelProps {
  fieldName: string;
  candidates: CandidateItem[];
  onSelectCandidate: (candidateValue: string) => Promise<void> | void;
}

export const AmbiguityPanel: React.FC<AmbiguityPanelProps> = ({
  fieldName,
  candidates,
  onSelectCandidate,
}) => {
  const [selectedVal, setSelectedVal] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);
  const [resolved, setResolved] = useState(false);

  const handleChoose = async (val: string) => {
    setSelectedVal(val);
    setResolving(true);
    try {
      await onSelectCandidate(val);
      setResolved(true);
    } catch (err) {
      console.error('Failed to resolve candidate:', err);
    } finally {
      setResolving(false);
    }
  };

  if (resolved && selectedVal) {
    return (
      <div className="p-3 bg-emerald-950/30 border border-emerald-800/50 rounded-lg flex items-center gap-2 text-xs font-mono text-emerald-300">
        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>Resolved: Selected <strong>{selectedVal}</strong>. Future scans will prioritize this format and location.</span>
      </div>
    );
  }

  return (
    <div className="p-4 bg-amber-950/20 border border-amber-800/40 rounded-lg space-y-3 font-mono text-xs">
      <div className="flex items-center gap-2 text-amber-300 font-semibold font-sans">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>We found {candidates.length} possible values for {fieldName}.</span>
      </div>
      <p className="text-zinc-400 text-[11px]">
        Choose the correct value to teach the system how to resolve this in future scans:
      </p>

      <div className="space-y-2">
        {candidates.map((cand, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded border transition-colors ${
              selectedVal === cand.value
                ? 'bg-zinc-800 border-zinc-500'
                : 'bg-zinc-900 border-zinc-800 hover:border-zinc-700'
            }`}
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-zinc-100 font-bold">{cand.value}</span>
                <ConfidenceBadge score={cand.confidence} />
              </div>
              <div className="text-[11px] text-zinc-500">
                {cand.context_before && (
                  <span>Near: "<span className="text-zinc-400">{cand.context_before}</span>"</span>
                )}
                {cand.anchor_found && (
                  <span className="ml-2 text-emerald-500 font-semibold">• Label: {cand.anchor_found}</span>
                )}
              </div>
            </div>

            <button
              onClick={() => handleChoose(cand.value)}
              disabled={resolving}
              className="px-3 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold shrink-0 transition-colors disabled:opacity-50"
            >
              {resolving && selectedVal === cand.value ? 'Saving...' : 'Use This'}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
