import React, { useState } from 'react';
import { Search, Layers, FileText, ArrowRight, Sparkles } from 'lucide-react';
import { PublicSiteConfig, SearchHit } from '../lib/publicApi';

interface HomePageProps {
  site: PublicSiteConfig;
  recentHits: SearchHit[];
  onSearch: (query: string) => void;
  onSelectDocument: (docId: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({
  site,
  recentHits,
  onSearch,
  onSelectDocument,
}) => {
  const [searchInput, setSearchInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchInput);
  };

  return (
    <div className="space-y-12 py-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-zinc-900 via-zinc-900/60 to-transparent border border-zinc-800 p-8 sm:p-12 text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Structured Document Archive</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight max-w-3xl mx-auto">
          {site.site_title || site.name}
        </h1>

        {site.tagline && (
          <p className="mt-4 text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto">
            {site.tagline}
          </p>
        )}

        {/* Search Bar */}
        <form onSubmit={handleSubmit} className="mt-8 max-w-2xl mx-auto">
          <div className="relative flex items-center">
            <Search className="absolute left-4 w-5 h-5 text-zinc-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search drawings, titles, document numbers, or equipment..."
              className="w-full pl-12 pr-28 py-3.5 bg-zinc-950/80 border border-zinc-700 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-xl text-sm"
            />
            <button
              type="submit"
              className="absolute right-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors"
            >
              Search
            </button>
          </div>
        </form>

        {/* Search Suggestion Pills */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-zinc-400">
          <span>Searchable fields:</span>
          {(site.search_config?.searchable_fields || ['Title', 'Drawing Number', 'Project']).map((f) => (
            <button
              key={f}
              onClick={() => { setSearchInput(f); onSearch(f); }}
              className="px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-mono transition-colors"
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Featured Collections */}
      {site.collections && site.collections.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
              <Layers className="w-5 h-5 text-blue-400" />
              <span>Browse Collections</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {site.collections.map((c) => (
              <div
                key={c.slug}
                onClick={() => onSearch(c.name)}
                className="cursor-pointer p-5 bg-zinc-900/60 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all group"
              >
                <h3 className="text-base font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors">
                  {c.name}
                </h3>
                {c.description && (
                  <p className="mt-1 text-xs text-zinc-400 line-clamp-2">
                    {c.description}
                  </p>
                )}
                <div className="mt-4 flex items-center text-xs font-medium text-blue-400 group-hover:translate-x-1 transition-transform">
                  <span>Explore items</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Documents Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            <span>Indexed Documents</span>
          </h2>
          <button
            onClick={() => onSearch('')}
            className="text-xs text-blue-400 hover:underline flex items-center space-x-1"
          >
            <span>View all archive records</span>
            <ArrowRight className="w-3 h-3 ml-1" />
          </button>
        </div>

        {recentHits.length === 0 ? (
          <div className="p-8 text-center bg-zinc-900/30 border border-zinc-800/60 rounded-xl text-zinc-400 text-sm">
            No published documents indexed yet. Index documents via the TSWebUI Admin control plane.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentHits.map((h) => (
              <div
                key={h.document_id}
                onClick={() => onSelectDocument(h.document_id)}
                className="cursor-pointer p-5 bg-zinc-900/60 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-sm font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors line-clamp-1">
                      {h.title}
                    </h3>
                    {h.drawing_number && (
                      <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 text-[11px] font-mono shrink-0">
                        {h.drawing_number}
                      </span>
                    )}
                  </div>

                  {h.snippet && (
                    <p className="text-xs text-zinc-400 line-clamp-2 mt-1">
                      {h.snippet}
                    </p>
                  )}

                  {/* Badges */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {Object.entries(h.structured_fields).slice(0, 3).map(([k, v]) => (
                      <span
                        key={k}
                        className="px-2 py-0.5 rounded bg-zinc-800/70 border border-zinc-700/50 text-zinc-400 text-[10px]"
                      >
                        <strong className="text-zinc-300 font-medium">{k}:</strong> {String(v)}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-zinc-800/60 flex items-center justify-between text-xs text-zinc-400">
                  <span className="text-[11px] font-mono text-zinc-500">
                    ID: {h.document_id.slice(0, 8)}
                  </span>
                  <span className="text-blue-400 font-medium group-hover:translate-x-1 transition-transform">
                    View Document →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
