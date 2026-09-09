import React, { useState, useEffect } from 'react';
import { Search, Filter, FileText, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { PublicSiteConfig, SearchHit, SearchResponse, searchPublicSite } from '../lib/publicApi';

interface SearchPageProps {
  site: PublicSiteConfig;
  initialQuery?: string;
  onSelectDocument: (docId: string) => void;
}

export const SearchPage: React.FC<SearchPageProps> = ({
  site,
  initialQuery = '',
  onSelectDocument,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('relevance');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const doSearch = async (q: string, p: number, s: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await searchPublicSite(site.slug, q, p, s);
      setResponse(res);
      setActiveQuery(q);
    } catch (err: any) {
      setError(err.message || 'Failed to execute search.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    doSearch(initialQuery, 1, sortBy);
  }, [initialQuery]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    doSearch(query, 1, sortBy);
  };

  const handleSortChange = (newSort: string) => {
    setSortBy(newSort);
    setPage(1);
    doSearch(query, 1, newSort);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    doSearch(query, newPage, sortBy);
  };

  return (
    <div className="space-y-4 sm:space-y-6 py-4 sm:py-6">
      {/* Search Header */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 sm:p-6">
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5 sm:gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by keywords, titles, identifiers, or specs..."
              className="w-full pl-10 pr-4 py-2.5 sm:py-2.5 bg-zinc-950 border border-zinc-700 rounded-lg text-base sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs sm:text-sm font-semibold transition-colors shrink-0 shadow-md"
          >
            Search
          </button>
        </form>

        {/* Filters & Sorting */}
        <div className="mt-3.5 pt-3.5 border-t border-zinc-800 flex flex-wrap items-center justify-between gap-2.5 text-xs">
          <div className="text-zinc-400 text-[11px] sm:text-xs">
            {response && (
              <span>
                Found <strong className="text-zinc-100">{response.total}</strong> document{response.total === 1 ? '' : 's'}
                {activeQuery && <span> for &ldquo;<span className="text-blue-400 font-medium">{activeQuery}</span>&rdquo;</span>}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-zinc-500 text-[11px]">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              className="bg-zinc-950 border border-zinc-700 rounded px-2.5 py-1 text-zinc-300 text-xs focus:outline-none"
            >
              <option value="relevance">Relevance</option>
              <option value="title">Title (A-Z)</option>
              <option value="newest">Newest</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results List */}
      {loading ? (
        <div className="py-20 text-center flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-sm text-zinc-400">Searching archive...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-sm">
          {error}
        </div>
      ) : response && response.hits.length === 0 ? (
        <div className="py-16 text-center bg-zinc-900/30 border border-zinc-800 rounded-xl text-zinc-400 space-y-2">
          <p className="text-base font-semibold text-zinc-200">No matching drawings were found.</p>
          <p className="text-xs text-zinc-500">Try broadening your search term or checking for typos.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {response?.hits.map((hit) => (
            <div
              key={hit.document_id}
              onClick={() => onSelectDocument(hit.document_id)}
              className="cursor-pointer p-5 bg-zinc-900/50 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all group flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors">
                    {hit.title}
                  </h3>
                  {hit.drawing_number && (
                    <span className="px-2 py-0.5 rounded bg-blue-900/30 border border-blue-700/40 text-blue-300 text-xs font-mono font-medium">
                      {hit.drawing_number}
                    </span>
                  )}
                  <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">
                    [{hit.rank_tier}]
                  </span>
                </div>

                {hit.snippet && (
                  <p className="text-xs text-zinc-400 line-clamp-2">
                    {hit.snippet}
                  </p>
                )}

                {/* Structured metadata badges */}
                <div className="flex flex-wrap gap-2 pt-1">
                  {Object.entries(hit.structured_fields).map(([key, val]) => (
                    <span
                      key={key}
                      className="px-2 py-0.5 rounded bg-zinc-800/80 border border-zinc-700/60 text-zinc-300 text-xs"
                    >
                      <strong className="text-zinc-400 font-normal">{key}:</strong> {String(val)}
                    </span>
                  ))}
                </div>
              </div>

              <div className="shrink-0 flex items-center space-x-3 sm:border-l sm:border-zinc-800 sm:pl-4">
                <button className="px-4 py-2 bg-zinc-800 group-hover:bg-blue-600 text-zinc-200 group-hover:text-white rounded-lg text-xs font-medium transition-colors">
                  View Drawing →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {response && response.total_pages > 1 && (
        <div className="flex items-center justify-center space-x-3 pt-6 border-t border-zinc-800">
          <button
            onClick={() => handlePageChange(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 disabled:opacity-30"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </button>
          <span className="text-xs font-mono text-zinc-400">
            Page {page} of {response.total_pages}
          </span>
          <button
            onClick={() => handlePageChange(Math.min(response.total_pages, page + 1))}
            disabled={page >= response.total_pages}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 disabled:opacity-30"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </button>
        </div>
      )}
    </div>
  );
};
