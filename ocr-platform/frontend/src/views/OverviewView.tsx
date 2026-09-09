import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Sliders,
  CheckCircle2,
  Cpu,
  ArrowUpRight,
  UploadCloud,
  BrainCircuit,
  FileSpreadsheet,
} from 'lucide-react';
import { api, DocumentItem, Configuration, TestRun } from '../lib/api';
import { BKLitMetricCard } from '../components/bklit/BKLitMetricCard';
import { BKLitGauge } from '../components/bklit/BKLitGauge';
import { BKLitAreaChart } from '../components/bklit/BKLitAreaChart';
import { formatBytes } from '../lib/utils';
import { TabType } from '../components/Navigation';

interface OverviewViewProps {
  onNavigate: (tab: TabType) => void;
  onSelectDocument?: (doc: DocumentItem) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onSelectDocument }) => {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [configs, setConfigs] = useState<Configuration[]>([]);
  const [latestRun, setLatestRun] = useState<TestRun | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [docsData, configsData] = await Promise.all([
          api.listDocuments(0, 10).catch(() => []),
          api.listConfigurations().catch(() => []),
        ]);
        setDocs(docsData);
        setConfigs(configsData);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalDocs = docs.length;
  const readyDocs = docs.filter((d) => d.status === 'ready').length;
  const configCount = configs.length;

  const sampleActivity = [
    { label: '09:00', value: 3 },
    { label: '10:00', value: 7 },
    { label: '11:00', value: 12 },
    { label: '12:00', value: 9 },
    { label: '13:00', value: 18 },
    { label: '14:00', value: 24 },
    { label: '15:00', value: 31 },
  ];

  return (
    <div className="space-y-6">
      {/* Top Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <BKLitMetricCard
          title="Total Documents"
          value={totalDocs}
          subvalue={`${readyDocs} ready for extraction`}
          sparklineData={[2, 5, 8, 7, 12, 16, totalDocs || 10]}
          icon={FileText}
          sparklineColor="#38bdf8"
        />

        <BKLitMetricCard
          title="Configurations"
          value={configCount}
          subvalue="Active rule versions"
          sparklineData={[1, 2, 2, 3, 3, 4, configCount || 4]}
          icon={Sliders}
          sparklineColor="#a855f7"
        />

        <BKLitMetricCard
          title="OCR Engine"
          value="Tesseract"
          subvalue="v5.x / multi-language"
          sparklineData={[10, 10, 10, 10, 10]}
          icon={Cpu}
          sparklineColor="#10b981"
        />

        <BKLitMetricCard
          title="System Health"
          value="100%"
          subvalue="All services operational"
          sparklineData={[98, 99, 99, 100, 100]}
          icon={CheckCircle2}
          sparklineColor="#10b981"
        />
      </div>

      {/* Main Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity & Extraction Volume Chart */}
        <div className="lg:col-span-2 bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                Document Extraction Activity
              </h3>
              <p className="text-xs text-zinc-400 font-mono mt-0.5">
                Processed tokens and field executions across batches
              </p>
            </div>
            <span className="font-mono text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/80 px-2 py-0.5 rounded">
              Live Feed
            </span>
          </div>

          <div className="mt-2">
            <BKLitAreaChart data={sampleActivity} height={140} color="#10b981" unit=" docs" />
          </div>

          <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400 font-mono">
            <span>Peak throughput: 31 docs/hr</span>
            <span>Median latency: 420ms</span>
          </div>
        </div>

        {/* Quality & Confidence Meter */}
        <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg p-5 flex flex-col items-center justify-between">
          <div className="w-full text-left">
            <h3 className="text-sm font-semibold text-zinc-100 font-sans">
              Model Extraction Quality
            </h3>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Weighted confidence across fields
            </p>
          </div>

          <div className="py-4">
            <BKLitGauge
              value={0.94}
              size={130}
              strokeWidth={9}
              label="Overall Accuracy"
              sublabel="Confidence"
              color="emerald"
            />
          </div>

          <div className="w-full grid grid-cols-2 gap-2 text-center text-xs font-mono pt-3 border-t border-zinc-800">
            <div className="bg-zinc-900/60 p-2 rounded border border-zinc-800">
              <div className="text-zinc-400 text-[10px]">Anchor Precision</div>
              <div className="text-zinc-100 font-semibold mt-0.5">97.8%</div>
            </div>
            <div className="bg-zinc-900/60 p-2 rounded border border-zinc-800">
              <div className="text-zinc-400 text-[10px]">Regex Validation</div>
              <div className="text-zinc-100 font-semibold mt-0.5">99.1%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Launch Action Cards */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Quick Workflows
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            whileHover={{ y: -2 }}
            onClick={() => onNavigate('advanced_inspector')}
            className="p-4 bg-[#0e0e11] border border-zinc-800 rounded-lg cursor-pointer hover:border-zinc-700 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-200">
                <UploadCloud className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
            </div>
            <h4 className="mt-3 text-sm font-semibold text-zinc-100">Upload & Inspect</h4>
            <p className="mt-1 text-xs text-zinc-400">
              Drop PDFs/images, explore tokens and run Tesseract OCR.
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -2 }}
            onClick={() => onNavigate('advanced_rules')}
            className="p-4 bg-[#0e0e11] border border-zinc-800 rounded-lg cursor-pointer hover:border-zinc-700 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-200">
                <Sliders className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
            </div>
            <h4 className="mt-3 text-sm font-semibold text-zinc-100">Rule Builder</h4>
            <p className="mt-1 text-xs text-zinc-400">
              Build extraction anchors, patterns, and test live on docs.
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -2 }}
            onClick={() => onNavigate('advanced_patterns')}
            className="p-4 bg-[#0e0e11] border border-zinc-800 rounded-lg cursor-pointer hover:border-zinc-700 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-200">
                <BrainCircuit className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
            </div>
            <h4 className="mt-3 text-sm font-semibold text-zinc-100">Pattern Trainer</h4>
            <p className="mt-1 text-xs text-zinc-400">
              Discover recurring templates and infer rules from N files.
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -2 }}
            onClick={() => onNavigate('results')}
            className="p-4 bg-[#0e0e11] border border-zinc-800 rounded-lg cursor-pointer hover:border-zinc-700 transition-colors group"
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-200">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-zinc-400 group-hover:text-white transition-colors" />
            </div>
            <h4 className="mt-3 text-sm font-semibold text-zinc-100">Extract & Export</h4>
            <p className="mt-1 text-xs text-zinc-400">
              Run structured extraction and export clean JSON / CSV.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-[#0c0c0e] border border-zinc-800 rounded-lg overflow-hidden">
        <div className="px-5 py-3.5 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-zinc-400" />
            <h3 className="text-sm font-semibold text-zinc-100 font-sans">Recent Ingested Files</h3>
          </div>
          <button
            onClick={() => onNavigate('advanced_inspector')}
            className="text-xs text-zinc-400 hover:text-white font-mono flex items-center gap-1 transition-colors"
          >
            View all ({docs.length}) &rarr;
          </button>
        </div>

        {docs.length === 0 ? (
          <div className="p-8 text-center text-zinc-400 text-xs font-mono">
            No documents uploaded yet. Switch to OCR Inspector or drop a file above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-[#0e0e12] border-b border-zinc-800 text-zinc-400 font-mono text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Filename</th>
                  <th className="px-4 py-2.5 font-medium">Type</th>
                  <th className="px-4 py-2.5 font-medium">Size</th>
                  <th className="px-4 py-2.5 font-medium">Pages</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 font-mono">
                {docs.slice(0, 5).map((d) => (
                  <tr key={d.id} className="hover:bg-zinc-900/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-zinc-200 truncate max-w-[200px]">
                      {d.original_filename}
                    </td>
                    <td className="px-4 py-3 text-zinc-400">{d.mime_type.split('/')[1] || 'bin'}</td>
                    <td className="px-4 py-3 text-zinc-400">{formatBytes(d.file_size_bytes)}</td>
                    <td className="px-4 py-3 text-zinc-300">{d.page_count || 1}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${
                          d.status === 'ready'
                            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-400'
                            : 'bg-zinc-900 border-zinc-800 text-zinc-400'
                        }`}
                      >
                        {d.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => {
                          onSelectDocument?.(d);
                          onNavigate('advanced_inspector');
                        }}
                        className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs transition-colors font-sans"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
