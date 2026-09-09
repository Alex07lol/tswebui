import React from 'react';
import { ShieldCheck, Database, Search, FileText } from 'lucide-react';
import { PublicSiteConfig } from '../lib/publicApi';

interface AboutPageProps {
  site: PublicSiteConfig;
}

export const AboutPage: React.FC<AboutPageProps> = ({ site }) => {
  return (
    <div className="max-w-4xl mx-auto py-10 space-y-8">
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-extrabold text-white">About {site.site_title || site.name}</h1>
        {site.description && (
          <p className="text-base text-zinc-400 max-w-2xl mx-auto">
            {site.description}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-xl space-y-2">
          <div className="w-8 h-8 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center">
            <Search className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-zinc-100">Ranked Search</h3>
          <p className="text-xs text-zinc-400">
            5-tier ranking hierarchy prioritizing exact title matches and drawing numbers over raw OCR text.
          </p>
        </div>

        <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-xl space-y-2">
          <div className="w-8 h-8 rounded bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-zinc-100">Verified Visibility</h3>
          <p className="text-xs text-zinc-400">
            Only explicitly published records are visible. All files are securely streamed with authorization gates.
          </p>
        </div>

        <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-xl space-y-2">
          <div className="w-8 h-8 rounded bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Database className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-zinc-100">Precomputed Intelligence</h3>
          <p className="text-xs text-zinc-400">
            High-speed responses powered by pre-extracted OCR tokens and structured metadata indexers.
          </p>
        </div>
      </div>
    </div>
  );
};
