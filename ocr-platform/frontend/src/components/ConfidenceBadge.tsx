import React, { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ConfidenceBadgeProps {
  score?: number | null;
  label?: string | null;
  why?: string[];
  advancedScore?: {
    pattern?: number;
    anchor?: number;
    layout?: number;
  };
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  score,
  label,
  why = [],
  advancedScore,
}) => {
  const [showWhy, setShowWhy] = useState(false);

  // Derive label if not provided
  let displayLabel = label;
  if (!displayLabel && score !== undefined && score !== null) {
    if (score >= 0.90) displayLabel = 'Very High';
    else if (score >= 0.70) displayLabel = 'High';
    else if (score >= 0.45) displayLabel = 'Medium';
    else displayLabel = 'Low';
  }
  displayLabel = displayLabel || 'Ready';

  // Determine styles
  let badgeColor = 'text-zinc-400 bg-zinc-800/60 border-zinc-700';
  let dotColor = 'bg-zinc-400';
  if (displayLabel === 'Very High') {
    badgeColor = 'text-emerald-300 bg-emerald-950/40 border-emerald-800/60';
    dotColor = 'bg-emerald-400';
  } else if (displayLabel === 'High') {
    badgeColor = 'text-green-300 bg-green-950/40 border-green-800/60';
    dotColor = 'bg-green-400';
  } else if (displayLabel === 'Medium') {
    badgeColor = 'text-amber-300 bg-amber-950/40 border-amber-800/60';
    dotColor = 'bg-amber-400';
  } else if (displayLabel === 'Low') {
    badgeColor = 'text-rose-300 bg-rose-950/40 border-rose-800/60';
    dotColor = 'bg-rose-400';
  }

  return (
    <div className="inline-flex flex-col text-xs font-mono">
      <div className="flex items-center gap-1.5">
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[11px] font-medium ${badgeColor}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
          {displayLabel}
        </span>

        {why && why.length > 0 && (
          <button
            onClick={() => setShowWhy(!showWhy)}
            className="text-zinc-500 hover:text-zinc-300 transition-colors flex items-center gap-0.5 text-[11px] underline"
            title="Explanation of confidence rating"
          >
            <span>Why?</span>
            {showWhy ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        )}
      </div>

      <AnimatePresence>
        {showWhy && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden mt-2 p-2.5 bg-zinc-900 border border-zinc-800 rounded text-[11px] text-zinc-300 space-y-1.5 max-w-sm"
          >
            <p className="font-semibold text-zinc-200">Why we are confident:</p>
            <ul className="list-disc list-inside space-y-0.5 text-zinc-400">
              {why.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>

            {advancedScore && (
              <div className="pt-1.5 mt-1.5 border-t border-zinc-800 text-[10px] text-zinc-500 flex items-center justify-between">
                <span>Score: {score !== undefined && score !== null ? Math.round(score * 100) : '--'}%</span>
                {advancedScore.anchor !== undefined && (
                  <span>Label match: {Math.round(advancedScore.anchor * 100)}%</span>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
