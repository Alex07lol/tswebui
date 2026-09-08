import React from 'react';
import { motion } from 'framer-motion';
import { BKLitSparkline } from './BKLitSparkline';
import { LucideIcon } from 'lucide-react';

interface BKLitMetricCardProps {
  title: string;
  value: string | number;
  subvalue?: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  sparklineData?: number[];
  icon?: LucideIcon;
  sparklineColor?: string;
}

export const BKLitMetricCard: React.FC<BKLitMetricCardProps> = ({
  title,
  value,
  subvalue,
  change,
  trend = 'neutral',
  sparklineData,
  icon: Icon,
  sparklineColor = '#10b981',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 20 }}
      whileHover={{ y: -2 }}
      className="bg-[#0e0e11] border border-zinc-800 rounded-lg p-4 transition-colors duration-150 hover:border-zinc-700"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">{title}</span>
        {Icon && <Icon className="w-4 h-4 text-zinc-400" />}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div>
          <div className="text-2xl font-bold font-mono text-zinc-100 tracking-tight">{value}</div>
          {subvalue && <div className="text-xs text-zinc-400 mt-0.5">{subvalue}</div>}
        </div>

        {sparklineData && sparklineData.length > 1 && (
          <div className="ml-4">
            <BKLitSparkline data={sparklineData} width={80} height={28} color={sparklineColor} />
          </div>
        )}
      </div>

      {change && (
        <div className="mt-3 pt-2.5 border-t border-zinc-800/80 flex items-center text-xs">
          <span
            className={`font-mono font-medium ${
              trend === 'up'
                ? 'text-emerald-400'
                : trend === 'down'
                ? 'text-rose-400'
                : 'text-zinc-400'
            }`}
          >
            {change}
          </span>
          <span className="text-zinc-400 ml-1.5 font-sans">vs previous period</span>
        </div>
      )}
    </motion.div>
  );
};
