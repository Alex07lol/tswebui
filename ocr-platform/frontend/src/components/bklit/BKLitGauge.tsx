import React from 'react';
import { motion } from 'framer-motion';

interface BKLitGaugeProps {
  value: number; // 0 to 1
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  color?: 'emerald' | 'amber' | 'rose' | 'zinc';
}

export const BKLitGauge: React.FC<BKLitGaugeProps> = ({
  value,
  size = 120,
  strokeWidth = 8,
  label,
  sublabel,
  color = 'emerald',
}) => {
  const clamped = Math.max(0, Math.min(1, value));
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  // Use a 270-degree arc for speedometer / gauge feel
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - arcLength * clamped;

  const colorMap = {
    emerald: { stroke: '#10b981', text: 'text-emerald-400', glow: 'rgba(16, 185, 129, 0.15)' },
    amber: { stroke: '#f59e0b', text: 'text-amber-400', glow: 'rgba(245, 158, 11, 0.15)' },
    rose: { stroke: '#f43f5e', text: 'text-rose-400', glow: 'rgba(244, 63, 94, 0.15)' },
    zinc: { stroke: '#a1a1aa', text: 'text-zinc-300', glow: 'rgba(161, 161, 170, 0.15)' },
  };

  const selectedColor = colorMap[color];

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="transform rotate-135"
        >
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#27272a"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />
          {/* Animated Value Arc */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={selectedColor.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset }}
            transition={{ type: 'spring', stiffness: 60, damping: 15 }}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className={`font-mono text-xl font-semibold tracking-tight ${selectedColor.text}`}
          >
            {Math.round(clamped * 100)}%
          </motion.span>
          {sublabel && (
            <span className="text-[10px] text-zinc-400 font-mono tracking-wider uppercase mt-0.5">
              {sublabel}
            </span>
          )}
        </div>
      </div>

      {label && (
        <span className="mt-2 text-xs font-medium text-zinc-300 text-center">
          {label}
        </span>
      )}
    </div>
  );
};
