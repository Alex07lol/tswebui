import React, { useEffect, useState } from 'react';
import {
  Globe,
  Plus,
  Layers,
  ExternalLink,
  Sparkles,
  CheckCircle2,
  XCircle,
  Loader2,
  Search,
  Trash2,
  Sliders,
  ShieldCheck,
} from 'lucide-react';
import {
  WebsiteListItem,
  WebsiteDetail,
  listWebsites,
  getWebsite,
  createWebsite,
  publishWebsite,
  unpublishWebsite,
  deleteWebsite,
} from '../lib/websiteApi';
import { listSetups, SetupSummary } from '../lib/setupApi';

export const WebsiteBuilderView: React.FC = () => {
  const [websites, setWebsites] = useState<WebsiteListItem[]>([]);
  const [setups, setSetups] = useState<SetupSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [siteName, setSiteName] = useState('');
  const [siteDesc, setSiteDesc] = useState('');
  const [selectedSetupId, setSelectedSetupId] = useState('');
  const [themePreset, setThemePreset] = useState('engineering_dark');
  const [searchableFields, setSearchableFields] = useState<string>('title, drawing_number, project, date');
  const [saving, setSaving] = useState(false);

  // Selected site for inspection
  const [selectedSite, setSelectedSite] = useState<WebsiteDetail | null>(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [wList, sList] = await Promise.all([listWebsites(), listSetups()]);
      setWebsites(wList);
      setSetups(sList);
      if (sList.length > 0) setSelectedSetupId(sList[0].id);
    } catch (err: any) {
      setError(err.message || 'Failed to load websites.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!siteName.trim()) return;
    setSaving(true);
    try {
      const fields = searchableFields
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await createWebsite({
        name: siteName.trim(),
        description: siteDesc.trim() || undefined,
        setup_id: selectedSetupId || undefined,
        theme: { preset: themePreset, primary_color: '#2563eb' },
        search_config: { searchable_fields: fields, default_sort: 'relevance' },
        field_mappings: {
          title_field: 'title',
          drawing_number_field: 'drawing_number',
          badge_fields: ['project', 'revision'],
          metadata_fields: fields,
        },
      });
      setIsCreateOpen(false);
      setSiteName('');
      setSiteDesc('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create website.');
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async (siteId: string) => {
    try {
      const res = await publishWebsite(siteId);
      alert(`Website published successfully! Version ${res.published_version} is now live.`);
      await loadData();
      if (selectedSite && selectedSite.id === siteId) {
        handleInspect(siteId);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to publish website.');
    }
  };

  const handleUnpublish = async (siteId: string) => {
    try {
      await unpublishWebsite(siteId);
      await loadData();
      if (selectedSite && selectedSite.id === siteId) {
        handleInspect(siteId);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to unpublish website.');
    }
  };

  const handleDelete = async (siteId: string) => {
    if (!confirm('Are you sure you want to delete this document website?')) return;
    try {
      await deleteWebsite(siteId);
      if (selectedSite && selectedSite.id === siteId) setSelectedSite(null);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete website.');
    }
  };

  const handleInspect = async (siteId: string) => {
    setInspectLoading(true);
    try {
      const detail = await getWebsite(siteId);
      setSelectedSite(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to load details.');
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-zinc-900/60 border border-zinc-800 rounded-2xl">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md mb-1 border border-blue-500/20">
            <Globe className="w-3.5 h-3.5" />
            <span>Consumer Portal Generator</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Document Website Builder
          </h1>
          <p className="text-xs text-zinc-400 max-w-2xl">
            Publish search portals for engineering drawings, specifications, and archives.
            Websites run on port <code className="text-zinc-300 font-mono">:5174</code> and query already-extracted OCR data.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-md transition-colors shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Website</span>
        </button>
      </div>

      {/* Main Grid */}
      {loading ? (
        <div className="py-20 text-center flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-xs text-zinc-400">Loading document websites...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-xs">
          {error}
        </div>
      ) : websites.length === 0 ? (
        <div className="p-12 text-center bg-zinc-900/30 border border-zinc-800/60 rounded-2xl space-y-4">
          <div className="w-12 h-12 rounded-full bg-blue-900/20 border border-blue-700/30 flex items-center justify-center text-blue-400 mx-auto">
            <Globe className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-zinc-100">No Document Websites Created</h3>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              Create your first website by choosing an OCR Setup and selecting searchable fields.
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium"
          >
            <Plus className="w-4 h-4" />
            <span>Create Website</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sites List (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            {websites.map((site) => (
              <div
                key={site.id}
                className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-zinc-700 transition-colors"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-semibold text-zinc-100">{site.name}</h3>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        site.status === 'published'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-zinc-800 text-zinc-400'
                      }`}
                    >
                      {site.status}
                    </span>
                    <span className="text-xs font-mono text-zinc-500">v{site.version_number}</span>
                  </div>

                  {site.description && (
                    <p className="text-xs text-zinc-400 line-clamp-1">{site.description}</p>
                  )}

                  <div className="flex items-center space-x-4 text-[11px] text-zinc-500 font-mono pt-1">
                    <span>Slug: /{site.slug}</span>
                    <span>Collections: {site.collection_count}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => handleInspect(site.id)}
                    className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg text-xs font-medium transition-colors"
                  >
                    Configure
                  </button>

                  {site.status === 'published' ? (
                    <>
                      <a
                        href={`http://localhost:5174/${site.slug}`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>View Portal</span>
                      </a>
                      <button
                        onClick={() => handleUnpublish(site.id)}
                        className="px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-amber-400 rounded-lg text-xs font-medium"
                        title="Unpublish"
                      >
                        Unpublish
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handlePublish(site.id)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors"
                    >
                      Publish
                    </button>
                  )}

                  <button
                    onClick={() => handleDelete(site.id)}
                    className="p-1.5 text-zinc-500 hover:text-red-400 rounded transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Details / Config Drawer (1 col) */}
          <div className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-xl space-y-4">
            {inspectLoading ? (
              <div className="py-12 text-center text-zinc-500 text-xs">Loading details...</div>
            ) : selectedSite ? (
              <div className="space-y-4">
                <div className="border-b border-zinc-800 pb-3">
                  <h3 className="text-base font-bold text-zinc-100">{selectedSite.name}</h3>
                  <p className="text-xs text-zinc-400 mt-0.5">{selectedSite.description || 'No description'}</p>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="text-zinc-500 uppercase tracking-wider font-semibold text-[10px]">
                    Public URL
                  </div>
                  <a
                    href={`http://localhost:5174/${selectedSite.slug}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 hover:underline font-mono text-xs break-all flex items-center gap-1"
                  >
                    <span>http://localhost:5174/{selectedSite.slug}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="text-zinc-500 uppercase tracking-wider font-semibold text-[10px]">
                    Searchable Fields
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {(selectedSite.search_config?.searchable_fields || []).map((f: string) => (
                      <span key={f} className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[11px]">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="text-zinc-500 uppercase tracking-wider font-semibold text-[10px]">
                    Theme Preset
                  </div>
                  <span className="px-2 py-0.5 rounded bg-zinc-800 text-blue-300 font-mono text-[11px]">
                    {selectedSite.theme?.preset || 'engineering_dark'}
                  </span>
                </div>

                <div className="pt-3 border-t border-zinc-800 flex items-center justify-between">
                  <span className="text-xs text-zinc-500">
                    Status: <strong className="text-zinc-200 capitalize">{selectedSite.status}</strong>
                  </span>
                  {selectedSite.status === 'published' ? (
                    <button
                      onClick={() => handleUnpublish(selectedSite.id)}
                      className="px-3 py-1 bg-amber-900/30 border border-amber-700 text-amber-300 rounded text-xs"
                    >
                      Unpublish
                    </button>
                  ) : (
                    <button
                      onClick={() => handlePublish(selectedSite.id)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold"
                    >
                      Publish Version {selectedSite.version_number}
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-zinc-500 text-xs">
                Select a website to view configuration, collections, and search mappings.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Website Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Globe className="w-5 h-5 text-blue-400" />
                <span>Create Document Website</span>
              </h2>
              <button onClick={() => setIsCreateOpen(false)} className="text-zinc-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Website / Portal Name
                </label>
                <input
                  type="text"
                  required
                  value={siteName}
                  onChange={(e) => setSiteName(e.target.value)}
                  placeholder="e.g. Engineering Drawing Library"
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={siteDesc}
                  onChange={(e) => setSiteDesc(e.target.value)}
                  placeholder="Brief description for visitors..."
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Connect to Extraction Setup
                </label>
                <select
                  value={selectedSetupId}
                  onChange={(e) => setSelectedSetupId(e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none"
                >
                  {setups.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.field_count} fields)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Searchable Fields (comma separated)
                </label>
                <input
                  type="text"
                  value={searchableFields}
                  onChange={(e) => setSearchableFields(e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-xs font-mono text-zinc-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Theme Preset
                </label>
                <select
                  value={themePreset}
                  onChange={(e) => setThemePreset(e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none"
                >
                  <option value="engineering_dark">Engineering Dark (High Contrast)</option>
                  <option value="modern_slate">Modern Slate (Clean Minimal)</option>
                  <option value="archival_blueprint">Technical Blueprint</option>
                </select>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  {saving ? 'Creating...' : 'Create Website'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
