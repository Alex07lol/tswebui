import React from 'react';
import { Home, Search, Layers, Info } from 'lucide-react';
import { PublicSiteConfig } from '../lib/publicApi';

interface MobileBottomNavProps {
  site: PublicSiteConfig;
  currentTab: string;
  onNavigate: (tab: string) => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  site,
  currentTab,
  onNavigate,
}) => {
  const hasCollections = site.collections && site.collections.length > 0;

  return (
    <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#090d16]/95 backdrop-blur-xl border-t border-zinc-800/80 px-2 py-1.5 flex items-center justify-around shadow-2xl safe-area-inset-bottom">
      <button
        onClick={() => onNavigate('home')}
        className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-xl transition-all ${
          currentTab === 'home'
            ? 'text-blue-400 font-semibold scale-105'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        <Home className="w-5 h-5 mb-0.5" />
        <span className="text-[10px] tracking-tight">Home</span>
      </button>

      <button
        onClick={() => onNavigate('search')}
        className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-xl transition-all ${
          currentTab === 'search'
            ? 'text-blue-400 font-semibold scale-105'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        <Search className="w-5 h-5 mb-0.5" />
        <span className="text-[10px] tracking-tight">Search</span>
      </button>

      {hasCollections && (
        <button
          onClick={() => onNavigate('collections')}
          className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-xl transition-all ${
            currentTab === 'collections'
              ? 'text-blue-400 font-semibold scale-105'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Layers className="w-5 h-5 mb-0.5" />
          <span className="text-[10px] tracking-tight">Collections</span>
        </button>
      )}

      <button
        onClick={() => onNavigate('about')}
        className={`flex flex-col items-center justify-center flex-1 py-1.5 rounded-xl transition-all ${
          currentTab === 'about'
            ? 'text-blue-400 font-semibold scale-105'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        <Info className="w-5 h-5 mb-0.5" />
        <span className="text-[10px] tracking-tight">About</span>
      </button>
    </nav>
  );
};
