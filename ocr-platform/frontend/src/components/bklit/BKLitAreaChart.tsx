import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface DataPoint {
  label: string;
  value: number;
}

interface BKLitAreaChartProps {
  data: DataPoint[];
  height?: number;
  color?: string;
  unit?: string;
}

export const BKLitAreaChart: React.FC<BKLitAreaChartProps> = ({
  data,
  height = 140,
  color = '#10b981',
  unit = '',
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-xs text-zinc-400">No chart data</div>;
  }

  const values = data.map((d) => d.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 10);
  const range = max - min || 1;

  const width = 100; // viewBox coordinate percentage
  const paddingX = 4;
  const paddingY = 16;
  const usableW = width - paddingX * 2;
  const usableH = height - paddingY * 2;

  const points = data.map((d, i) => {
    const x = paddingX + (i / (data.length - 1 || 1)) * usableW;
    const y = height - paddingY - ((d.value - min) / range) * usableH;
    return { x, y, label: d.label, value: d.value };
  });

  const pathD = `M ${points.map((p) => `${p.x},${p.y}`).join(' L ')}`;
  const areaD = `M ${points[0].x},${points[0].y} L ${points.map((p) => `${p.x},${p.y}`).join(' L ')} L ${points[points.length - 1].x},${height} L ${points[0].x},${height} Z`;

  return (
    <div className="w-full relative select-none">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="w-full overflow-visible"
        style={{ height }}
      >
        <defs>
          <linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.12} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* Horizontal subtle guide lines */}
        {[0.25, 0.5, 0.75].map((factor) => {
          const y = height - paddingY - factor * usableH;
          return (
            <line
              key={factor}
              x1={paddingX}
              y1={y}
              x2={width - paddingX}
              y2={y}
              stroke="#27272a"
              strokeDasharray="2 2"
              strokeWidth={0.5}
            />
          );
        })}

        {/* Filled Area */}
        <motion.path
          d={areaD}
          fill="url(#area-gradient)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        />

        {/* Main Line */}
        <motion.path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />

        {/* Hover Points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={hoveredIdx === i ? 3.5 : 1.5}
            className="cursor-pointer transition-all duration-150"
            fill={color}
            stroke="#09090b"
            strokeWidth={1}
            onMouseEnter={() => setHoveredIdx(i)}
            onMouseLeave={() => setHoveredIdx(null)}
          />
        ))}
      </svg>

      {/* Tooltip */}
      {hoveredIdx !== null && points[hoveredIdx] && (
        <div
          className="absolute -top-3 -translate-y-full transform -translate-x-1/2 bg-[#121215] border border-zinc-700 px-2 py-1 rounded text-[11px] font-mono shadow-sm pointer-events-none z-10 whitespace-nowrap"
          style={{ left: `${(points[hoveredIdx].x / width) * 100}%` }}
        >
          <span className="text-zinc-400 mr-1.5">{points[hoveredIdx].label}:</span>
          <span className="font-semibold text-white">
            {points[hoveredIdx].value}
            {unit}
          </span>
        </div>
      )}

      {/* X-axis labels */}
      <div className="flex justify-between mt-1 text-[10px] font-mono text-zinc-400 px-1">
        <span>{data[0]?.label}</span>
        {data.length > 2 && <span>{data[Math.floor(data.length / 2)]?.label}</span>}
        <span>{data[data.length - 1]?.label}</span>
      </div>
    </div>
  );
};
