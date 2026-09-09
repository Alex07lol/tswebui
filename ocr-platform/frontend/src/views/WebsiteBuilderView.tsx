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
  Palette,
  FileText,
  Settings,
  Play,
  Eye,
  Database,
  RefreshCw,
  Smartphone,
  Monitor,
  Tablet,
  ArrowRight,
  Code,
  Shield,
  Check,
  ListFilter,
  LayoutTemplate,
  ChevronRight,
  Save,
  Link2,
  Copy,
  AlertCircle,
  FileBox,
  Wand2,
} from 'lucide-react';
import {
  WebsiteListItem,
  WebsiteDetail,
  WebsitePageItem,
  WebsiteDocumentItem,
  DataSourceItem,
  DataFieldItem,
  listWebsites,
  getWebsite,
  createWebsite,
  updateWebsite,
  publishWebsite,
  unpublishWebsite,
  deleteWebsite,
  listDataSources,
  syncSetupToDataSource,
  listWebsiteDocuments,
  addWebsiteDocuments,
  syncWebsiteSetupDocuments,
} from '../lib/websiteApi';
import { listSetups, SetupSummary } from '../lib/setupApi';

type BuilderPanel =
  | 'pages'
  | 'data'
  | 'components'
  | 'design'
  | 'actions'
  | 'rules'
  | 'preview'
  | 'publish';

const TEMPLATES = [
  {
    id: 'engineering_drawing',
    name: 'Engineering Drawing Portal',
    desc: 'Searchable archive for CAD prints, specifications, and drawing revisions.',
    theme: { preset: 'engineering_dark', primary_color: '#2563eb', border_radius: 'md' },
    fields: ['title', 'drawing_number', 'revision', 'project', 'date'],
    mappings: {
      title_field: 'title',
      identifier_field: 'drawing_number',
      badge_fields: ['project', 'revision'],
      date_field: 'date',
    },
  },
  {
    id: 'warranty_lookup',
    name: 'Warranty Verification Portal',
    desc: 'Customer self-service portal to verify hardware warranty coverage and expiry.',
    theme: { preset: 'modern_slate', primary_color: '#10b981', border_radius: 'lg' },
    fields: ['serial_number', 'product_name', 'customer', 'purchase_date', 'expiry_date', 'status'],
    mappings: {
      title_field: 'product_name',
      identifier_field: 'serial_number',
      badge_fields: ['status'],
      date_field: 'expiry_date',
    },
  },
  {
    id: 'product_catalog',
    name: 'Product & Specification Catalog',
    desc: 'Interactive catalog for product sheets, compliance docs, and technical specs.',
    theme: { preset: 'corporate_clean', primary_color: '#6366f1', border_radius: 'md' },
    fields: ['sku', 'product_title', 'category', 'compliance_code', 'last_updated'],
    mappings: {
      title_field: 'product_title',
      identifier_field: 'sku',
      badge_fields: ['category'],
      date_field: 'last_updated',
    },
  },
  {
    id: 'certificate_verification',
    name: 'Certificate & Compliance Verification',
    desc: 'Public registry to verify certificates, inspections, and audit reports.',
    theme: { preset: 'technical_blueprint', primary_color: '#0284c7', border_radius: 'sm' },
    fields: ['cert_number', 'recipient', 'issuing_body', 'issue_date', 'valid_until', 'status'],
    mappings: {
      title_field: 'recipient',
      identifier_field: 'cert_number',
      badge_fields: ['status', 'issuing_body'],
      date_field: 'valid_until',
    },
  },
  {
    id: 'analytical_dashboard',
    name: 'Operational Dashboard',
    desc: 'Metrics-driven view with summary KPI cards and filterable structured data.',
    theme: { preset: 'modern_slate', primary_color: '#8b5cf6', border_radius: 'lg' },
    fields: ['record_id', 'department', 'metric_value', 'recorded_date', 'flag'],
    mappings: {
      title_field: 'department',
      identifier_field: 'record_id',
      badge_fields: ['flag'],
      date_field: 'recorded_date',
    },
  },
  {
    id: 'blank',
    name: 'Blank Canvas',
    desc: 'Start completely from scratch with a custom layout and data schema.',
    theme: { preset: 'engineering_dark', primary_color: '#3b82f6', border_radius: 'md' },
    fields: [],
    mappings: {},
  },
];

export const WebsiteBuilderView: React.FC = () => {
  const [websites, setWebsites] = useState<WebsiteListItem[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceItem[]>([]);
  const [setups, setSetups] = useState<SetupSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active Workspace / Editing Site
  const [editingSiteId, setEditingSiteId] = useState<string | null>(null);
  const [editingSite, setEditingSite] = useState<WebsiteDetail | null>(null);
  const [activePanel, setActivePanel] = useState<BuilderPanel>('pages');
  const [activePageIdx, setActivePageIdx] = useState<number>(0);
  const [previewDevice, setPreviewDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [savingSite, setSavingSite] = useState(false);
  const [siteDocs, setSiteDocs] = useState<WebsiteDocumentItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  // Modal State for New Site
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('engineering_drawing');
  const [siteName, setSiteName] = useState('');
  const [siteDesc, setSiteDesc] = useState('');
  const [selectedSourceId, setSelectedSourceId] = useState('');
  const [creating, setCreating] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [wList, dsList, sList] = await Promise.all([
        listWebsites(),
        listDataSources().catch(() => []),
        listSetups().catch(() => []),
      ]);
      setWebsites(wList);
      setDataSources(dsList);
      setSetups(sList);
      if (dsList.length > 0 && !selectedSourceId) {
        setSelectedSourceId(dsList[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load builder data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openEditor = async (siteId: string) => {
    setEditingSiteId(siteId);
    setLoading(true);
    try {
      const site = await getWebsite(siteId);
      setEditingSite(site);
      setActivePanel('pages');
      setActivePageIdx(0);
      loadSiteDocs(siteId);
    } catch (err: any) {
      alert(err.message || 'Failed to load website.');
      setEditingSiteId(null);
    } finally {
      setLoading(false);
    }
  };

  const loadSiteDocs = async (siteId: string) => {
    setDocsLoading(true);
    try {
      const docs = await listWebsiteDocuments(siteId);
      setSiteDocs(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setDocsLoading(false);
    }
  };

  const closeEditor = async () => {
    setEditingSiteId(null);
    setEditingSite(null);
    await loadData();
  };

  const handleCreateNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!siteName.trim()) return;
    setCreating(true);

    try {
      const tmpl = TEMPLATES.find((t) => t.id === selectedTemplate) || TEMPLATES[0];

      // Build default pages based on template
      const defaultPages: WebsitePageItem[] = [
        {
          page_type: 'home',
          title: 'Home',
          slug: 'home',
          components: [
            {
              id: 'comp-hero',
              type: 'hero',
              title: siteName.trim(),
              config: {
                tagline: siteDesc.trim() || tmpl.desc,
                show_search_bar: true,
              },
            },
            {
              id: 'comp-featured',
              type: 'record_grid',
              title: 'Featured Records',
              config: { limit: 6, layout: 'cards' },
            },
          ],
          display_order: 0,
        },
        {
          page_type: 'search',
          title: 'Search & Explore',
          slug: 'search',
          components: [
            {
              id: 'comp-search-bar',
              type: 'search_bar',
              title: 'Universal Query',
              config: { placeholder: 'Search by keyword, identifier, or label...' },
            },
            {
              id: 'comp-results-table',
              type: 'record_table',
              title: 'Search Results',
              config: { pagination: 20, enable_facets: true },
            },
          ],
          display_order: 1,
        },
        {
          page_type: 'detail',
          title: 'Record Detail',
          slug: 'documents',
          components: [
            {
              id: 'comp-doc-viewer',
              type: 'document_viewer',
              title: 'Document & OCR View',
              config: { show_ocr_overlay: true, show_metadata_drawer: true },
            },
          ],
          display_order: 2,
        },
      ];

      const res = await createWebsite({
        name: siteName.trim(),
        description: siteDesc.trim() || tmpl.desc,
        setup_id: selectedSourceId.startsWith('setup-') ? selectedSourceId.replace('setup-', '') : undefined,
        data_source_id: !selectedSourceId.startsWith('setup-') ? selectedSourceId : undefined,
        theme: tmpl.theme,
        search_config: {
          searchable_fields: tmpl.fields,
          default_sort: 'relevance',
          filter_facets: tmpl.mappings.badge_fields || [],
        },
        field_mappings: tmpl.mappings,
        document_view: {
          allow_download: true,
          show_bounding_boxes: true,
        },
        bindings: {
          primary_source_id: selectedSourceId,
        },
      });

      setIsCreateOpen(false);
      setSiteName('');
      setSiteDesc('');
      await loadData();
      await openEditor(res.id);
    } catch (err: any) {
      alert(err.message || 'Failed to create website.');
    } finally {
      setCreating(false);
    }
  };

  const handleSaveSiteChanges = async () => {
    if (!editingSite) return;
    setSavingSite(true);
    try {
      const res = await updateWebsite(editingSite.id, {
        name: editingSite.name,
        description: editingSite.description,
        setup_id: editingSite.setup_id,
        theme: editingSite.theme,
        search_config: editingSite.search_config,
        field_mappings: editingSite.field_mappings,
        document_view: editingSite.document_view,
        bindings: editingSite.bindings,
        actions: editingSite.actions,
        conditions: editingSite.conditions,
        computed_fields: editingSite.computed_fields,
        pages: editingSite.pages,
      });

      // Reload fresh site data
      const refreshed = await getWebsite(editingSite.id);
      setEditingSite(refreshed);
      alert(
        res.version_status === 'draft'
          ? `Changes saved to Draft (v${res.version_number}).`
          : 'Website draft updated successfully.'
      );
    } catch (err: any) {
      alert(err.message || 'Failed to save changes.');
    } finally {
      setSavingSite(false);
    }
  };

  const handlePublish = async (siteId: string) => {
    try {
      const res = await publishWebsite(siteId);
      alert(`Published successfully! Version ${res.published_version} is now live.`);
      if (editingSite) {
        const refreshed = await getWebsite(editingSite.id);
        setEditingSite(refreshed);
      }
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to publish website.');
    }
  };

  const handleUnpublish = async (siteId: string) => {
    try {
      await unpublishWebsite(siteId);
      if (editingSite) {
        const refreshed = await getWebsite(editingSite.id);
        setEditingSite(refreshed);
      }
      await loadData();
      alert('Website unpublished.');
    } catch (err: any) {
      alert(err.message || 'Failed to unpublish website.');
    }
  };

  const handleDelete = async (siteId: string) => {
    if (!confirm('Are you sure you want to permanently delete this website?')) return;
    try {
      await deleteWebsite(siteId);
      if (editingSiteId === siteId) {
        setEditingSiteId(null);
        setEditingSite(null);
      }
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete website.');
    }
  };

  // One-Click Auto-Generate
  const handleAutoGenerate = async () => {
    if (!editingSite) return;
    if (!confirm('Auto-generate pages, components, search facets, and layouts from connected data?')) return;

    setSavingSite(true);
    try {
      // Find connected DataSource or Setup fields
      let discoveredFields: string[] = [];
      let idField = 'id';
      let titleField = 'name';
      let badgeFields: string[] = [];
      let dateField: string | null = null;

      const currentDs = dataSources.find((ds) => ds.id === editingSite.bindings?.primary_source_id);
      if (currentDs && currentDs.schema?.fields) {
        currentDs.schema.fields.forEach((f) => {
          discoveredFields.push(f.key);
          if (f.semantic_role === 'identifier') idField = f.key;
          if (f.semantic_role === 'title') titleField = f.key;
          if (f.semantic_role === 'badge' || f.semantic_role === 'status') badgeFields.push(f.key);
          if (f.semantic_role === 'date') dateField = f.key;
        });
      }

      if (discoveredFields.length === 0) {
        discoveredFields = ['title', 'identifier', 'category', 'status', 'created_at'];
        titleField = 'title';
        idField = 'identifier';
        badgeFields = ['category', 'status'];
      }

      const generatedPages: WebsitePageItem[] = [
        {
          page_type: 'home',
          title: 'Home',
          slug: 'home',
          components: [
            {
              id: 'comp-hero-gen',
              type: 'hero',
              title: editingSite.name,
              config: {
                tagline: editingSite.description || 'Intelligent Document & Data Portal',
                show_search_bar: true,
              },
            },
            {
              id: 'comp-metrics-gen',
              type: 'metric_cards',
              title: 'Overview Metrics',
              config: { items: ['Total Documents', 'Verified Items', 'Active Records'] },
            },
            {
              id: 'comp-grid-gen',
              type: 'record_grid',
              title: 'Recent Records',
              config: { limit: 8, layout: 'cards' },
            },
          ],
          display_order: 0,
        },
        {
          page_type: 'search',
          title: 'Catalog & Search',
          slug: 'search',
          components: [
            {
              id: 'comp-search-bar-gen',
              type: 'search_bar',
              title: 'Universal Query',
              config: { placeholder: `Search across ${discoveredFields.join(', ')}...` },
            },
            {
              id: 'comp-filter-sidebar-gen',
              type: 'filter_sidebar',
              title: 'Refine Results',
              config: { facet_fields: badgeFields },
            },
            {
              id: 'comp-results-table-gen',
              type: 'record_table',
              title: 'Results Table',
              config: { pagination: 25, sort_field: dateField || idField },
            },
          ],
          display_order: 1,
        },
        {
          page_type: 'detail',
          title: 'Item Detail',
          slug: 'documents',
          components: [
            {
              id: 'comp-doc-viewer-gen',
              type: 'document_viewer',
              title: 'Document & OCR Inspector',
              config: { show_ocr_overlay: true, show_metadata_drawer: true },
            },
          ],
          display_order: 2,
        },
      ];

      const updatedSite: WebsiteDetail = {
        ...editingSite,
        pages: generatedPages,
        search_config: {
          searchable_fields: discoveredFields,
          default_sort: 'relevance',
          filter_facets: badgeFields,
        },
        field_mappings: {
          title_field: titleField,
          identifier_field: idField,
          badge_fields: badgeFields,
          date_field: dateField,
          metadata_fields: discoveredFields,
        },
      };

      await updateWebsite(editingSite.id, {
        pages: generatedPages,
        search_config: updatedSite.search_config,
        field_mappings: updatedSite.field_mappings,
      });

      setEditingSite(updatedSite);
      alert('Site automatically configured and generated from schema!');
    } catch (err: any) {
      alert(err.message || 'Auto-generate failed.');
    } finally {
      setSavingSite(false);
    }
  };

  const handleSyncAllSetupDocs = async () => {
    if (!editingSite) return;
    const targetSetupId = editingSite.setup_id || (setups[0] ? setups[0].id : null);
    if (!targetSetupId) {
      alert('Please connect an OCR Setup to sync documents from.');
      return;
    }
    try {
      const res = await syncWebsiteSetupDocuments(editingSite.id, targetSetupId);
      alert(`Synced ${res.synced_documents} documents from Setup to Website!`);
      loadSiteDocs(editingSite.id);
    } catch (err: any) {
      alert(err.message || 'Failed to sync documents.');
    }
  };

  // ==================== RENDERING ====================

  if (editingSite) {
    const activePage = editingSite.pages[activePageIdx] || editingSite.pages[0];

    return (
      <div className="space-y-4 pb-16">
        {/* Workspace Top Navigation Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 sm:p-4 bg-zinc-900/80 border border-zinc-800 rounded-2xl backdrop-blur-md">
          <div className="flex items-center space-x-3">
            <button
              onClick={closeEditor}
              className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
              title="Return to Sites"
            >
              <ChevronRight className="w-5 h-5 rotate-180" />
            </button>

            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base sm:text-lg font-bold text-white tracking-tight leading-tight">{editingSite.name}</h1>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    editingSite.status === 'published'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-zinc-800 text-zinc-400'
                  }`}
                >
                  {editingSite.status}
                </span>
                <span className="text-xs font-mono text-zinc-500">v{editingSite.version_number}</span>
              </div>
              <p className="text-xs text-zinc-400 font-mono">/{editingSite.slug}</p>
            </div>
          </div>

          <div className="flex flex-wrap sm:flex-nowrap items-center gap-1.5 sm:gap-2 shrink-0">
            <button
              onClick={handleAutoGenerate}
              disabled={savingSite}
              className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-lg text-xs font-semibold transition-colors"
              title="Automatically create pages, components, and search facets from schema"
            >
              <Wand2 className="w-3.5 h-3.5" />
              <span>Auto-Generate</span>
            </button>

            <button
              onClick={handleSaveSiteChanges}
              disabled={savingSite}
              className="flex items-center space-x-1.5 px-3 sm:px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition-colors"
            >
              {savingSite ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>Save Draft</span>
            </button>

            {editingSite.status === 'published' ? (
              <button
                onClick={() => handleUnpublish(editingSite.id)}
                className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-amber-400 rounded-lg text-xs font-medium"
              >
                Unpublish
              </button>
            ) : (
              <button
                onClick={() => handlePublish(editingSite.id)}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Publish</span>
              </button>
            )}

            <a
              href={`http://localhost:5174/${editingSite.slug}`}
              target="_blank"
              rel="noreferrer"
              className="p-1.5 sm:p-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg transition-colors"
              title="Open Live Public Site"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>

        {/* 8-Panel Navigation Tabs (Scrollable on Mobile) */}
        <div className="flex items-center space-x-1.5 border-b border-zinc-800 pb-2 overflow-x-auto no-scrollbar py-1 text-xs font-semibold scroll-smooth">
          {[
            { id: 'pages', label: '1. Pages', icon: FileText },
            { id: 'data', label: '2. Data & Schema', icon: Database },
            { id: 'components', label: '3. Components', icon: Layers },
            { id: 'design', label: '4. Design & Theme', icon: Palette },
            { id: 'actions', label: '5. Actions', icon: ArrowRight },
            { id: 'rules', label: '6. Rules & Logic', icon: Shield },
            { id: 'preview', label: '7. Live Preview', icon: Eye },
            { id: 'publish', label: '8. Publish & Gate', icon: ShieldCheck },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activePanel === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActivePanel(tab.id as BuilderPanel)}
                className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg transition-colors shrink-0 ${
                  isActive
                    ? 'bg-blue-600 text-white font-bold shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Workspace Panels */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-3.5 sm:p-6 min-h-[500px]">
          {/* Panel 1: PAGES */}
          {activePanel === 'pages' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Application Pages</h3>
                  <p className="text-xs text-zinc-400">
                    Manage the structure of your site. Each page defines a route and container components.
                  </p>
                </div>
                <button
                  onClick={() => {
                    const newPage: WebsitePageItem = {
                      page_type: 'custom',
                      title: `New Page ${editingSite.pages.length + 1}`,
                      slug: `page-${editingSite.pages.length + 1}`,
                      components: [],
                      display_order: editingSite.pages.length,
                    };
                    setEditingSite({
                      ...editingSite,
                      pages: [...editingSite.pages, newPage],
                    });
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-semibold"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Page</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {editingSite.pages.map((p, idx) => (
                  <div
                    key={idx}
                    onClick={() => setActivePageIdx(idx)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      activePageIdx === idx
                        ? 'bg-blue-950/30 border-blue-600 ring-1 ring-blue-500'
                        : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 uppercase">
                        {p.page_type}
                      </span>
                      {editingSite.pages.length > 1 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const nextPages = editingSite.pages.filter((_, i) => i !== idx);
                            setEditingSite({ ...editingSite, pages: nextPages });
                            setActivePageIdx(0);
                          }}
                          className="text-zinc-500 hover:text-red-400 p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                    <h4 className="text-sm font-bold text-zinc-100">{p.title}</h4>
                    <p className="text-xs text-zinc-500 font-mono mt-0.5">/{p.slug}</p>
                    <div className="mt-3 pt-2 border-t border-zinc-800/80 flex items-center justify-between text-[11px] text-zinc-400">
                      <span>{p.components?.length || 0} component(s)</span>
                      <span className="text-blue-400">Configure &rarr;</span>
                    </div>
                  </div>
                ))}
              </div>

              {activePage && (
                <div className="p-5 bg-zinc-950 border border-zinc-800 rounded-xl space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-300">
                    Page Settings: {activePage.title}
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                    <div>
                      <label className="block text-zinc-400 mb-1">Page Title</label>
                      <input
                        type="text"
                        value={activePage.title}
                        onChange={(e) => {
                          const updated = [...editingSite.pages];
                          updated[activePageIdx].title = e.target.value;
                          setEditingSite({ ...editingSite, pages: updated });
                        }}
                        className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 mb-1">Slug Route</label>
                      <input
                        type="text"
                        value={activePage.slug}
                        onChange={(e) => {
                          const updated = [...editingSite.pages];
                          updated[activePageIdx].slug = e.target.value;
                          setEditingSite({ ...editingSite, pages: updated });
                        }}
                        className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 mb-1">Type</label>
                      <select
                        value={activePage.page_type}
                        onChange={(e) => {
                          const updated = [...editingSite.pages];
                          updated[activePageIdx].page_type = e.target.value;
                          setEditingSite({ ...editingSite, pages: updated });
                        }}
                        className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200"
                      >
                        <option value="home">Home / Hero</option>
                        <option value="search">Search & Catalog</option>
                        <option value="detail">Document Detail</option>
                        <option value="collection">Collection View</option>
                        <option value="custom">Custom Markdown</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Panel 2: DATA & SCHEMA */}
          {activePanel === 'data' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-white">Universal Data Source & Schema Picker</h3>
                <p className="text-xs text-zinc-400">
                  Select fields from your connected data models. No comma-separated strings required.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Data Source Selector */}
                <div className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl space-y-3">
                  <span className="text-xs font-bold text-zinc-200">Connected Data Source</span>
                  <select
                    value={editingSite.bindings?.primary_source_id || ''}
                    onChange={(e) => {
                      setEditingSite({
                        ...editingSite,
                        bindings: {
                          ...editingSite.bindings,
                          primary_source_id: e.target.value,
                        },
                      });
                    }}
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-xs text-zinc-100"
                  >
                    <option value="">-- Choose Data Source --</option>
                    {dataSources.map((ds) => (
                      <option key={ds.id} value={ds.id}>
                        {ds.name} ({ds.record_count} records)
                      </option>
                    ))}
                    {setups.map((s) => (
                      <option key={`setup-${s.id}`} value={`setup-${s.id}`}>
                        OCR Setup: {s.name} ({s.field_count} fields)
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={async () => {
                      if (!editingSite.setup_id) {
                        alert('Connect an OCR Setup first.');
                        return;
                      }
                      try {
                        const res = await syncSetupToDataSource(editingSite.setup_id);
                        alert(`Synced Setup to DataSource: ${res.data_source_id}`);
                        loadData();
                      } catch (err: any) {
                        alert(err.message || 'Sync failed.');
                      }
                    }}
                    className="flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 font-medium pt-1"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Sync Setup Schema to DataSource</span>
                  </button>
                </div>

                {/* Field Role Mappings */}
                <div className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl space-y-3">
                  <span className="text-xs font-bold text-zinc-200">Key Semantic Roles</span>
                  <div className="space-y-2 text-xs">
                    <div>
                      <label className="block text-zinc-400 mb-0.5">Primary Title Field</label>
                      <input
                        type="text"
                        value={editingSite.field_mappings?.title_field || ''}
                        onChange={(e) =>
                          setEditingSite({
                            ...editingSite,
                            field_mappings: { ...editingSite.field_mappings, title_field: e.target.value },
                          })
                        }
                        placeholder="e.g. title, product_name"
                        className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 mb-0.5">Identifier / Key Field</label>
                      <input
                        type="text"
                        value={editingSite.field_mappings?.identifier_field || ''}
                        onChange={(e) =>
                          setEditingSite({
                            ...editingSite,
                            field_mappings: { ...editingSite.field_mappings, identifier_field: e.target.value },
                          })
                        }
                        placeholder="e.g. drawing_number, serial_no"
                        className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 font-mono"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Dynamic Field Checkbox Matrix */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-zinc-200">Searchable & Displayable Fields Matrix</span>
                <div className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl">
                  {(() => {
                    const currentDs = dataSources.find((ds) => ds.id === editingSite.bindings?.primary_source_id);
                    const fields =
                      currentDs?.schema?.fields ||
                      (editingSite.search_config?.searchable_fields || ['title', 'drawing_number', 'project', 'date']).map(
                        (f: string) => ({
                          id: f,
                          key: f,
                          label: f,
                          type: 'string',
                          semantic_role: 'metadata',
                        })
                      );

                    return (
                      <div className="divide-y divide-zinc-800/60">
                        {fields.map((f: any) => {
                          const isSearchable = (editingSite.search_config?.searchable_fields || []).includes(f.key);
                          const isFacet = (editingSite.search_config?.filter_facets || []).includes(f.key);

                          return (
                            <div key={f.key} className="py-2.5 flex items-center justify-between text-xs">
                              <div className="flex items-center space-x-3">
                                <span className="font-mono font-semibold text-zinc-100">{f.key}</span>
                                <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 uppercase">
                                  {f.type || 'string'}
                                </span>
                                {f.semantic_role && (
                                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                                    {f.semantic_role}
                                  </span>
                                )}
                              </div>

                              <div className="flex items-center space-x-4">
                                <label className="flex items-center space-x-1.5 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={isSearchable}
                                    onChange={(e) => {
                                      const currentList = editingSite.search_config?.searchable_fields || [];
                                      const nextList = e.target.checked
                                        ? [...currentList, f.key]
                                        : currentList.filter((k: string) => k !== f.key);
                                      setEditingSite({
                                        ...editingSite,
                                        search_config: { ...editingSite.search_config, searchable_fields: nextList },
                                      });
                                    }}
                                    className="rounded bg-zinc-900 border-zinc-700 text-blue-600 focus:ring-0"
                                  />
                                  <span className="text-zinc-400">Searchable</span>
                                </label>

                                <label className="flex items-center space-x-1.5 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={isFacet}
                                    onChange={(e) => {
                                      const currentFacets = editingSite.search_config?.filter_facets || [];
                                      const nextFacets = e.target.checked
                                        ? [...currentFacets, f.key]
                                        : currentFacets.filter((k: string) => k !== f.key);
                                      setEditingSite({
                                        ...editingSite,
                                        search_config: { ...editingSite.search_config, filter_facets: nextFacets },
                                      });
                                    }}
                                    className="rounded bg-zinc-900 border-zinc-700 text-emerald-600 focus:ring-0"
                                  />
                                  <span className="text-zinc-400">Filter Facet</span>
                                </label>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* Panel 3: COMPONENTS */}
          {activePanel === 'components' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Page Components ({activePage ? activePage.title : 'Page'})
                  </h3>
                  <p className="text-xs text-zinc-400">
                    Add, remove, and configure layout components on the selected page.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <select
                    id="new-comp-select"
                    className="px-3 py-1.5 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-200"
                  >
                    <option value="hero">Hero Header</option>
                    <option value="search_bar">Search Bar</option>
                    <option value="record_grid">Record Grid</option>
                    <option value="record_table">Data Table</option>
                    <option value="metric_cards">Metric KPI Cards</option>
                    <option value="document_viewer">Document / OCR Viewer</option>
                    <option value="markdown">Markdown / Text Section</option>
                  </select>
                  <button
                    onClick={() => {
                      const sel = (document.getElementById('new-comp-select') as HTMLSelectElement).value;
                      const updated = [...editingSite.pages];
                      const compList = updated[activePageIdx].components || [];
                      compList.push({
                        id: `comp-${Date.now()}`,
                        type: sel,
                        title: sel.replace('_', ' ').toUpperCase(),
                        config: {},
                      });
                      updated[activePageIdx].components = compList;
                      setEditingSite({ ...editingSite, pages: updated });
                    }}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold"
                  >
                    + Add Component
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {(!activePage?.components || activePage.components.length === 0) ? (
                  <div className="p-12 text-center border border-dashed border-zinc-800 rounded-2xl text-xs text-zinc-500">
                    No components added yet. Use "+ Add Component" above or click "Auto-Generate".
                  </div>
                ) : (
                  activePage.components.map((comp, cIdx) => (
                    <div
                      key={comp.id || cIdx}
                      className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="p-2 bg-zinc-900 rounded-lg text-blue-400 font-mono text-xs">
                          {cIdx + 1}
                        </span>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="text-xs font-bold text-zinc-100">{comp.title || comp.type}</h4>
                            <span className="px-2 py-0.5 bg-zinc-800 text-[10px] font-mono text-zinc-400 rounded">
                              {comp.type}
                            </span>
                          </div>
                          <span className="text-[11px] text-zinc-500">ID: {comp.id}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            const updated = [...editingSite.pages];
                            updated[activePageIdx].components = (updated[activePageIdx].components || []).filter(
                              (_, i) => i !== cIdx
                            );
                            setEditingSite({ ...editingSite, pages: updated });
                          }}
                          className="p-1.5 text-zinc-500 hover:text-red-400 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Panel 4: DESIGN & THEME */}
          {activePanel === 'design' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-white">Visual Design & Theme Presets</h3>
                <p className="text-xs text-zinc-400">
                  Custom styling, typography, and brand identity applied to the public portal runtime.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { id: 'engineering_dark', name: 'Engineering Dark', desc: 'High-contrast dark terminal aesthetic' },
                  { id: 'modern_slate', name: 'Modern Slate', desc: 'Clean, contemporary enterprise minimal theme' },
                  { id: 'corporate_clean', name: 'Corporate Clean', desc: 'Light professional theme with refined cards' },
                  { id: 'technical_blueprint', name: 'Technical Blueprint', desc: 'Architectural blueprint cyan & deep navy' },
                ].map((t) => (
                  <div
                    key={t.id}
                    onClick={() => {
                      setEditingSite({
                        ...editingSite,
                        theme: { ...editingSite.theme, preset: t.id },
                      });
                    }}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      editingSite.theme?.preset === t.id
                        ? 'bg-blue-950/40 border-blue-500 ring-1 ring-blue-500'
                        : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'
                    }`}
                  >
                    <h4 className="text-xs font-bold text-zinc-100">{t.name}</h4>
                    <p className="text-xs text-zinc-400 mt-1">{t.desc}</p>
                  </div>
                ))}
              </div>

              <div className="p-5 bg-zinc-950 border border-zinc-800 rounded-xl space-y-4">
                <h4 className="text-xs font-bold text-zinc-200">Brand Color Accent</h4>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    value={editingSite.theme?.primary_color || '#2563eb'}
                    onChange={(e) =>
                      setEditingSite({
                        ...editingSite,
                        theme: { ...editingSite.theme, primary_color: e.target.value },
                      })
                    }
                    className="w-10 h-10 rounded cursor-pointer bg-transparent border-0"
                  />
                  <input
                    type="text"
                    value={editingSite.theme?.primary_color || '#2563eb'}
                    onChange={(e) =>
                      setEditingSite({
                        ...editingSite,
                        theme: { ...editingSite.theme, primary_color: e.target.value },
                      })
                    }
                    className="px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-xs font-mono text-zinc-200 w-32"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Panel 5: ACTIONS */}
          {activePanel === 'actions' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-white">Interaction & Click Actions</h3>
                <p className="text-xs text-zinc-400">
                  Configure what happens when a user clicks records, cards, and CTA buttons.
                </p>
              </div>

              <div className="p-5 bg-zinc-950 border border-zinc-800 rounded-xl space-y-4 text-xs">
                <div>
                  <label className="block text-zinc-300 font-semibold mb-1">Card Click Action</label>
                  <select
                    value={editingSite.actions?.record_click_action || 'navigate_to_detail'}
                    onChange={(e) =>
                      setEditingSite({
                        ...editingSite,
                        actions: { ...editingSite.actions, record_click_action: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200"
                  >
                    <option value="navigate_to_detail">Navigate to Document Detail Page</option>
                    <option value="open_modal">Open Document in Modal Inspector</option>
                    <option value="download_pdf">Direct Download Original PDF</option>
                  </select>
                </div>

                <div>
                  <label className="block text-zinc-300 font-semibold mb-1">Search Submit Action</label>
                  <select
                    value={editingSite.actions?.search_submit_action || 'navigate_to_search'}
                    onChange={(e) =>
                      setEditingSite({
                        ...editingSite,
                        actions: { ...editingSite.actions, search_submit_action: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200"
                  >
                    <option value="navigate_to_search">Navigate to Search Results View</option>
                    <option value="live_dropdown">Instant Live Dropdown Results</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Panel 6: RULES & LOGIC */}
          {activePanel === 'rules' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-white">Conditional Visibility & Computed Rules</h3>
                <p className="text-xs text-zinc-400">
                  Enforce business logic, field transformations, and conditional display rules.
                </p>
              </div>

              <div className="p-5 bg-zinc-950 border border-zinc-800 rounded-xl space-y-4 text-xs">
                <div className="space-y-1">
                  <span className="font-semibold text-zinc-200">Document Security Masking</span>
                  <p className="text-zinc-500 text-[11px]">
                    Only documents with verified and published status can be retrieved publicly.
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editingSite.conditions?.require_public_flag !== false}
                      onChange={(e) =>
                        setEditingSite({
                          ...editingSite,
                          conditions: { ...editingSite.conditions, require_public_flag: e.target.checked },
                        })
                      }
                      className="rounded bg-zinc-900 border-zinc-700 text-blue-600 focus:ring-0"
                    />
                    <span className="text-zinc-300">Enforce explicit document membership gating (P0 Rule G)</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Panel 7: PREVIEW */}
          {activePanel === 'preview' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Live Portal Runtime Preview</h3>
                  <p className="text-xs text-zinc-400">
                    Interact with your site pages. Toggle viewport sizes to verify responsiveness.
                  </p>
                </div>

                <div className="flex items-center space-x-2 bg-zinc-950 p-1 rounded-lg border border-zinc-800">
                  <button
                    onClick={() => setPreviewDevice('desktop')}
                    className={`p-1.5 rounded ${previewDevice === 'desktop' ? 'bg-zinc-800 text-white' : 'text-zinc-500'}`}
                    title="Desktop (100%)"
                  >
                    <Monitor className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPreviewDevice('tablet')}
                    className={`p-1.5 rounded ${previewDevice === 'tablet' ? 'bg-zinc-800 text-white' : 'text-zinc-500'}`}
                    title="Tablet (768px)"
                  >
                    <Tablet className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPreviewDevice('mobile')}
                    className={`p-1.5 rounded ${previewDevice === 'mobile' ? 'bg-zinc-800 text-white' : 'text-zinc-500'}`}
                    title="Mobile (390px)"
                  >
                    <Smartphone className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="flex justify-center bg-zinc-950/80 p-4 rounded-2xl border border-zinc-800 overflow-hidden">
                <div
                  className="transition-all duration-300 bg-[#09090b] rounded-xl border border-zinc-800 overflow-hidden shadow-2xl"
                  style={{
                    width: previewDevice === 'mobile' ? '390px' : previewDevice === 'tablet' ? '768px' : '100%',
                    height: '620px',
                  }}
                >
                  <iframe
                    src={`http://localhost:5174/${editingSite.slug}`}
                    title="Public Site Live Preview"
                    className="w-full h-full border-0"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Panel 8: PUBLISH & GATE */}
          {activePanel === 'publish' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-white">Release Management & Document Gating</h3>
                <p className="text-xs text-zinc-400">
                  Guarantee published snapshot immutability and manage explicit public document membership.
                </p>
              </div>

              {/* Status Alert */}
              <div className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-zinc-400">Current Status:</span>
                    <span
                      className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${
                        editingSite.status === 'published'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-zinc-800 text-zinc-300'
                      }`}
                    >
                      {editingSite.status}
                    </span>
                    <span className="text-xs font-mono text-zinc-500">Draft v{editingSite.version_number}</span>
                    {editingSite.published_version && (
                      <span className="text-xs font-mono text-emerald-400">
                        (Live v{editingSite.published_version})
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-1">
                    Rule D Guarantee: Editing this site will branch a draft version, leaving the live published version immutable.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  {editingSite.status === 'published' ? (
                    <button
                      onClick={() => handleUnpublish(editingSite.id)}
                      className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-amber-400 rounded-xl text-xs font-semibold"
                    >
                      Unpublish
                    </button>
                  ) : (
                    <button
                      onClick={() => handlePublish(editingSite.id)}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-900/30 transition-colors"
                    >
                      Publish Version {editingSite.version_number}
                    </button>
                  )}
                </div>
              </div>

              {/* Document Membership Management */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <h4 className="text-xs font-bold text-zinc-200">
                      Explicit Public Document Members ({siteDocs.length} documents)
                    </h4>
                    <p className="text-[11px] text-zinc-500">
                      Only documents explicitly added here and marked public will be exposed in the search index and detail viewer.
                    </p>
                  </div>

                  <button
                    onClick={handleSyncAllSetupDocs}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Sync All Setup Docs</span>
                  </button>
                </div>

                <div className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl max-h-64 overflow-y-auto">
                  {docsLoading ? (
                    <div className="py-8 text-center text-xs text-zinc-500">Loading documents...</div>
                  ) : siteDocs.length === 0 ? (
                    <div className="py-8 text-center text-xs text-zinc-500">
                      No documents added to this website yet. Click "Sync All Setup Docs" above to add documents.
                    </div>
                  ) : (
                    <div className="divide-y divide-zinc-800/60">
                      {siteDocs.map((doc) => (
                        <div key={doc.id} className="py-2 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-3">
                            <FileText className="w-4 h-4 text-zinc-400 shrink-0" />
                            <div>
                              <span className="text-zinc-200 font-mono">{doc.original_filename || doc.filename}</span>
                              <div className="flex items-center space-x-2 text-[10px] text-zinc-500">
                                <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                                <span>Status: {doc.status}</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                doc.is_public ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'
                              }`}
                            >
                              {doc.is_public ? 'Public' : 'Hidden'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ==================== SITES LIST VIEW ====================

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-zinc-900/60 border border-zinc-800 rounded-2xl">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md mb-1 border border-blue-500/20">
            <Globe className="w-3.5 h-3.5" />
            <span>Universal Website & App Builder</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Document Websites & Portals
          </h1>
          <p className="text-xs text-zinc-400 max-w-2xl">
            Create domain-agnostic data-driven portals for drawings, warranties, certificates, and specs.
            Public runtime operates on port <code className="text-zinc-300 font-mono">:5174</code> with published snapshot immutability.
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

      {/* Main Grid of Websites */}
      {loading ? (
        <div className="py-20 text-center flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-xs text-zinc-400">Loading websites...</p>
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
              Select a starter template to launch your first public data portal in seconds.
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {websites.map((site) => (
            <div
              key={site.id}
              className="p-5 bg-zinc-900/60 border border-zinc-800 rounded-2xl flex flex-col justify-between hover:border-zinc-700 transition-colors shadow-lg"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
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

                <div>
                  <h3 className="text-base font-bold text-zinc-100">{site.name}</h3>
                  <p className="text-xs text-zinc-400 line-clamp-2 mt-1">
                    {site.description || 'Data-driven document search portal'}
                  </p>
                </div>

                <div className="text-[11px] text-zinc-500 font-mono">
                  Slug: /{site.slug}
                </div>
              </div>

              {/* Actions Footer */}
              <div className="pt-4 mt-4 border-t border-zinc-800/80 flex items-center justify-between">
                <button
                  onClick={() => openEditor(site.id)}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors"
                >
                  Configure (8-Panels)
                </button>

                <div className="flex items-center space-x-1">
                  {site.status === 'published' && (
                    <a
                      href={`http://localhost:5174/${site.slug}`}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg transition-colors"
                      title="Open Live Public Site"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}

                  <button
                    onClick={() => handleDelete(site.id)}
                    className="p-2 text-zinc-500 hover:text-red-400 rounded-lg transition-colors"
                    title="Delete Website"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Website Modal with Starter Templates */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <LayoutTemplate className="w-5 h-5 text-blue-400" />
                <span>Create New Document Website</span>
              </h2>
              <button onClick={() => setIsCreateOpen(false)} className="text-zinc-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateNew} className="space-y-4 text-xs">
              {/* Template Picker */}
              <div>
                <label className="block text-zinc-300 font-semibold mb-1.5">
                  Choose a Starter Template
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {TEMPLATES.map((tmpl) => (
                    <div
                      key={tmpl.id}
                      onClick={() => {
                        setSelectedTemplate(tmpl.id);
                        if (!siteName) setSiteName(tmpl.name);
                      }}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        selectedTemplate === tmpl.id
                          ? 'bg-blue-950/40 border-blue-500 ring-1 ring-blue-500'
                          : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'
                      }`}
                    >
                      <h4 className="font-bold text-zinc-100">{tmpl.name}</h4>
                      <p className="text-[11px] text-zinc-400 mt-0.5">{tmpl.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-zinc-300 font-semibold mb-1">
                  Website / Portal Name
                </label>
                <input
                  type="text"
                  required
                  value={siteName}
                  onChange={(e) => setSiteName(e.target.value)}
                  placeholder="e.g. Industrial Turbines Warranty Portal"
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-semibold mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={siteDesc}
                  onChange={(e) => setSiteDesc(e.target.value)}
                  placeholder="Brief description for portal visitors..."
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-semibold mb-1">
                  Connect Primary Data Source / OCR Setup
                </label>
                <select
                  value={selectedSourceId}
                  onChange={(e) => setSelectedSourceId(e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-700 rounded-lg text-xs text-zinc-100 focus:outline-none"
                >
                  <optgroup label="Universal DataSources">
                    {dataSources.map((ds) => (
                      <option key={ds.id} value={ds.id}>
                        {ds.name} ({ds.record_count} records)
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="OCR Setups">
                    {setups.map((s) => (
                      <option key={`setup-${s.id}`} value={`setup-${s.id}`}>
                        {s.name} ({s.field_count} fields)
                      </option>
                    ))}
                  </optgroup>
                </select>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create & Open Builder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
