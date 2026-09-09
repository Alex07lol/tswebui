import React from 'react';
import { motion } from 'framer-motion';
import { Scan, Sparkles, PlusCircle, FileCheck2, ArrowRight, Wrench } from 'lucide-react';
import { TabType } from '../components/Navigation';

interface HomeViewProps {
  onNavigate: (tab: TabType | 'create_setup') => void;
}

export const HomeView: React.FC<HomeViewProps> = ({ onNavigate }) => {
  const actions = [
    {
      id: 'scan',
      title: 'Scan Documents',
      desc: 'Upload documents and extract information using one of your saved setups.',
      icon: Scan,
      buttonText: 'Start Scanning',
      badge: 'Extract Data',
      onClick: () => onNavigate('scan'),
    },
    {
      id: 'teach',
      title: 'Teach From Examples',
      desc: 'Upload several similar documents and let the system discover repeating information automatically.',
      icon: Sparkles,
      buttonText: 'Teach System',
      badge: 'Automatic Discovery',
      onClick: () => onNavigate('teach'),
    },
    {
      id: 'create_setup',
      title: 'Create a Setup',
      desc: 'Tell the system what information you want to find in your documents.',
      icon: PlusCircle,
      buttonText: 'New Setup',
      badge: 'Define Fields',
      onClick: () => onNavigate('create_setup'),
    },
    {
      id: 'results',
      title: 'View Results',
      desc: 'Review, verify, and export information from previously processed documents.',
      icon: FileCheck2,
      buttonText: 'Browse Results',
      badge: 'Export & Audit',
      onClick: () => onNavigate('results'),
    },
  ];

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-10">
      {/* Title / Intro */}
      <div className="text-center space-y-2 max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100 font-sans">
          What would you like to do?
        </h1>
        <p className="text-sm text-zinc-400 font-mono">
          Extract structured data from your scanned documents or teach the platform what to look for.
        </p>
      </div>

      {/* 4 Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {actions.map((act, index) => {
          const Icon = act.icon;
          return (
            <motion.div
              key={act.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08, type: 'spring', stiffness: 400, damping: 30 }}
              className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl p-6 flex flex-col justify-between space-y-6 transition-all group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-100 group-hover:bg-zinc-100 group-hover:text-zinc-950 transition-colors">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800">
                    {act.badge}
                  </span>
                </div>

                <h3 className="text-xl font-semibold text-zinc-100 font-sans">
                  {act.title}
                </h3>
                <p className="text-sm text-zinc-400 font-sans leading-relaxed">
                  {act.desc}
                </p>
              </div>

              <div>
                <button
                  onClick={act.onClick}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold font-sans flex items-center justify-center gap-2 transition-colors shadow-sm"
                >
                  <span>{act.buttonText}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Subtle Advanced Tools hint footer */}
      <div className="pt-6 border-t border-zinc-800/80 flex items-center justify-between text-xs font-mono text-zinc-500">
        <div className="flex items-center gap-2">
          <Wrench className="w-3.5 h-3.5" />
          <span>Need full OCR engine control?</span>
        </div>
        <button
          onClick={() => onNavigate('advanced_rules')}
          className="text-zinc-400 hover:text-zinc-200 underline transition-colors"
        >
          Open Advanced Rule Editor →
        </button>
      </div>
    </div>
  );
};
