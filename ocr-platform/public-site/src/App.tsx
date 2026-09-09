import React, { useEffect, useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import {
  PublicSiteConfig,
  SearchHit,
  fetchPublicSite,
  searchPublicSite,
} from './lib/publicApi';
import { SiteHeader } from './components/SiteHeader';
import { SiteFooter } from './components/SiteFooter';
import { HomePage } from './pages/HomePage';
import { SearchPage } from './pages/SearchPage';
import { DocumentDetailPage } from './pages/DocumentDetailPage';
import { AboutPage } from './pages/AboutPage';

export function App() {
  const [slug, setSlug] = useState<string>('');
  const [site, setSite] = useState<PublicSiteConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [currentTab, setCurrentTab] = useState<string>('home');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [recentHits, setRecentHits] = useState<SearchHit[]>([]);

  useEffect(() => {
    // 1. Resolve slug from path e.g. /engineering_drawings or ?site=slug
    const urlParams = new URLSearchParams(window.location.search);
    let targetSlug = urlParams.get('site') || window.location.pathname.replace(/^\/+/, '').split('/')[0];

    const init = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!targetSlug) {
          // Discover first published site
          const listRes = await fetch('/api/admin/websites');
          if (listRes.ok) {
            const list = await listRes.json();
            const published = list.find((s: any) => s.status === 'published') || list[0];
            if (published) {
              targetSlug = published.slug;
            }
          }
        }

        if (!targetSlug) {
          targetSlug = 'engineering-drawings';
        }

        setSlug(targetSlug);
        const config = await fetchPublicSite(targetSlug);
        setSite(config);

        // Load initial recent documents
        try {
          const sRes = await searchPublicSite(targetSlug, '', 1, 'newest');
          setRecentHits(sRes.hits || []);
        } catch {
          // ignore initial search failure
        }
      } catch (err: any) {
        setError(err.message || 'Failed to connect to document portal.');
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  const handleNavigate = (tab: string) => {
    setCurrentTab(tab);
    setSelectedDocId(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleHeroSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentTab('search');
    setSelectedDocId(null);
  };

  const handleSelectDocument = (docId: string) => {
    setSelectedDocId(docId);
    setCurrentTab('document');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center space-y-4 text-zinc-400">
        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        <p className="text-sm font-medium">Connecting to Document Portal...</p>
      </div>
    );
  }

  if (error || !site) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md p-8 bg-zinc-900 border border-zinc-800 rounded-2xl space-y-4 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-red-950/80 border border-red-800/80 flex items-center justify-center text-red-400 mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-zinc-100">Document Portal Unavailable</h2>
          <p className="text-xs text-zinc-400">
            {error || 'The requested document portal is not published or does not exist.'}
          </p>
          <div className="pt-2">
            <a
              href="http://localhost:5173"
              className="inline-flex items-center px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold rounded-lg transition-colors"
            >
              Open Admin Control Plane (:5173)
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0f19] flex flex-col text-zinc-100">
      <SiteHeader site={site} currentTab={currentTab} onNavigate={handleNavigate} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8">
        {currentTab === 'home' && (
          <HomePage
            site={site}
            recentHits={recentHits}
            onSearch={handleHeroSearch}
            onSelectDocument={handleSelectDocument}
          />
        )}

        {currentTab === 'search' && (
          <SearchPage
            site={site}
            initialQuery={searchQuery}
            onSelectDocument={handleSelectDocument}
          />
        )}

        {currentTab === 'collections' && (
          <HomePage
            site={site}
            recentHits={recentHits}
            onSearch={handleHeroSearch}
            onSelectDocument={handleSelectDocument}
          />
        )}

        {currentTab === 'document' && selectedDocId && (
          <DocumentDetailPage
            site={site}
            documentId={selectedDocId}
            onBack={() => setCurrentTab('search')}
          />
        )}

        {currentTab === 'about' && <AboutPage site={site} />}
      </main>

      <SiteFooter />
    </div>
  );
}
export default App;
