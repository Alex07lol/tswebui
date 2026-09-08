import React from 'react';
import { motion } from 'framer-motion';

interface ClusterItem {
  id: string;
  label: string;
  count: number;
  isOutlier?: boolean;
}

interface BKLitClusterBarProps {
  clusters: ClusterItem[];
  selectedClusterId?: string | null;
  onSelectCluster?: (id: string) => void;
}

export const BKLitClusterBar: React.FC<BKLitClusterBarProps> = ({
  clusters,
  selectedClusterId,
  onSelectCluster,
}) => {
  const totalDocs = clusters.reduce((acc, c) => acc + c.count, 0) || 1;

  return (
    <div className="space-y-2">
      {/* Visual proportional distribution bar */}
      <div className="h-3 w-full bg-zinc-900 rounded flex overflow-hidden border border-zinc-800">
        {clusters.map((c, i) => {
          const widthPercent = (c.count / totalDocs) * 100;
          const isSelected = c.id === selectedClusterId;
          const bgShade = c.isOutlier
            ? 'bg-rose-600'
            : i % 2 === 0
            ? 'bg-zinc-300'
            : 'bg-zinc-500';

          return (
            <motion.div
              key={c.id}
              initial={{ width: 0 }}
              animate={{ width: `${widthPercent}%` }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              onClick={() => onSelectCluster?.(c.id)}
              className={`h-full cursor-pointer transition-opacity ${bgShade} ${
                isSelected ? 'ring-2 ring-white z-10' : 'hover:opacity-80'
              }`}
              title={`${c.label}: ${c.count} documents (${Math.round(widthPercent)}%)`}
            />
          );
        })}
      </div>

      {/* Cluster legend list */}
      <div className="flex flex-wrap gap-2 text-xs">
        {clusters.map((c, i) => {
          const isSelected = c.id === selectedClusterId;
          const dotColor = c.isOutlier
            ? 'bg-rose-500'
            : i % 2 === 0
            ? 'bg-zinc-300'
            : 'bg-zinc-500';

          return (
            <button
              key={c.id}
              onClick={() => onSelectCluster?.(c.id)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded border transition-all ${
                isSelected
                  ? 'bg-zinc-800 border-zinc-500 text-white'
                  : 'bg-zinc-900/60 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${dotColor}`} />
              <span className="font-medium">{c.label}</span>
              <span className="font-mono text-[10px] text-zinc-400">({c.count})</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
