import React, { useState, useEffect } from 'react';
import { Plus, Search, Layers, RefreshCw } from 'lucide-react';
import { setupApi, SetupItem } from '../lib/setupApi';
import { SetupCard } from '../components/setup/SetupCard';

interface MySetupsViewProps {
  onCreateNew: () => void;
  onScanSetup: (setup: SetupItem) => void;
  onEditSetup: (setup: SetupItem) => void;
  onViewResults: (setup: SetupItem) => void;
}

export const MySetupsView: React.FC<MySetupsViewProps> = ({
  onCreateNew,
  onScanSetup,
  onEditSetup,
  onViewResults,
}) => {
  const [setups, setSetups] = useState<SetupItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');

  const loadSetups = async () => {
    setIsLoading(true);
    try {
      const data = await setupApi.listSetups();
      setSetups(data);
    } catch (err) {
      console.error('Failed to load setups:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSetups();
  }, []);

  const filtered = setups.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            My Setups
          </h1>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Document extraction setups configured for your specific paperwork.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadSetups}
            className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={onCreateNew}
            className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Setup</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      {setups.length > 0 && (
        <div className="relative max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search setups..."
            className="w-full pl-9 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-200 placeholder-zinc-600 outline-none focus:border-zinc-600"
          />
        </div>
      )}

      {/* Setups Grid */}
      {isLoading ? (
        <div className="py-20 text-center text-xs font-mono text-zinc-500">
          Loading your setups...
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center border border-dashed border-zinc-800 rounded-xl space-y-4">
          <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
            <Layers className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <p className="text-base font-semibold text-zinc-200">No setups found</p>
            <p className="text-xs text-zinc-500 font-mono">
              Create a setup to tell the system what information to extract from your documents.
            </p>
          </div>
          <button
            onClick={onCreateNew}
            className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold inline-flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Create Your First Setup</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filtered.map((setup) => (
            <SetupCard
              key={setup.id}
              setup={setup}
              onScan={onScanSetup}
              onEdit={onEditSetup}
              onViewResults={onViewResults}
            />
          ))}
        </div>
      )}
    </div>
  );
};
