import React from 'react';
import { FileText, Search, Layers, Info } from 'lucide-react';
import { PublicSiteConfig } from '../lib/publicApi';

interface SiteHeaderProps {
  site: PublicSiteConfig;
  currentTab: string;
  onNavigate: (tab: string) => void;
}

export const SiteHeader: React.FC<SiteHeaderProps> = ({ site, currentTab, onNavigate }) => {
  return (
    <header className="sticky top-0 z-30 border-b border-zinc-800 bg-[#0b0f19]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={() => onNavigate('home')}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:bg-blue-600/30 transition-colors">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-zinc-100 tracking-tight leading-none group-hover:text-blue-400 transition-colors">
              {site.site_title || site.name}
            </h1>
            {site.tagline && (
              <p className="text-xs text-zinc-400 mt-0.5 line-clamp-1">
                {site.tagline}
              </p>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex items-center space-x-1">
          <button
            onClick={() => onNavigate('home')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              currentTab === 'home'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            Home
          </button>
          <button
            onClick={() => onNavigate('search')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              currentTab === 'search'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Search</span>
          </button>
          {site.collections && site.collections.length > 0 && (
            <button
              onClick={() => onNavigate('collections')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                currentTab === 'collections'
                  ? 'bg-zinc-800 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Collections ({site.collections.length})</span>
            </button>
          )}
          <button
            onClick={() => onNavigate('about')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              currentTab === 'about'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <Info className="w-3.5 h-3.5" />
            <span>About</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
