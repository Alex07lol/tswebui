import React from 'react';
import { ShieldCheck } from 'lucide-react';

export const SiteFooter: React.FC = () => {
  return (
    <footer className="border-t border-zinc-800 bg-[#080b12] py-8 text-center text-xs text-zinc-500">
      <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 text-zinc-400">
          <ShieldCheck className="w-4 h-4 text-blue-500" />
          <span>Verified Document Archive</span>
        </div>
        <p>© {new Date().getFullYear()} Document Portal. Secured & Powered by TSWebUI Platform.</p>
        <div className="text-zinc-600 font-mono">
          Public Consumer Interface
        </div>
      </div>
    </footer>
  );
};
