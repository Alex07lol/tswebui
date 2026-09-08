import React from 'react';
import { motion } from 'framer-motion';

interface BKLitSparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  fillOpacity?: number;
}

export const BKLitSparkline: React.FC<BKLitSparklineProps> = ({
  data,
  width = 120,
  height = 36,
  color = '#10b981',
  fillOpacity = 0.08,
}) => {
  if (!data || data.length < 2) {
    return <div style={{ width, height }} className="bg-zinc-900/30 rounded" />;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const padding = 4;
  const usableWidth = width - padding * 2;
  const usableHeight = height - padding * 2;

  const points = data.map((val, idx) => {
    const x = padding + (idx / (data.length - 1)) * usableWidth;
    const y = height - padding - ((val - min) / range) * usableHeight;
    return `${x},${y}`;
  });

  const linePath = `M ${points.join(' L ')}`;
  const areaPath = `M ${points[0]} L ${points.join(' L ')} L ${width - padding},${height} L ${padding},${height} Z`;

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={fillOpacity} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>

      {/* Area Fill */}
      <motion.path
        d={areaPath}
        fill={`url(#gradient-${color})`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      />

      {/* Crisp Stroke Line */}
      <motion.path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      />

      {/* End marker dot */}
      {points.length > 0 && (
        <motion.circle
          cx={points[points.length - 1].split(',')[0]}
          cy={points[points.length - 1].split(',')[1]}
          r={2.5}
          fill={color}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.7, type: 'spring', stiffness: 400, damping: 15 }}
        />
      )}
    </svg>
  );
};
