/**
 * API client for Universal DataSources, Document Websites, Versions,
 * Page Layouts, Publications, Document Memberships, and Visual PDF Locators.
 */

export function getAuthHeaders(): Record<string, string> {
  const token =
    localStorage.getItem('token') ||
    localStorage.getItem('access_token') ||
    sessionStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export interface DataFieldItem {
  id: string;
  key: string;
  label: string;
  type: string;
  required: boolean;
  searchable: boolean;
  sortable: boolean;
  filterable: boolean;
  displayable: boolean;
  public_readable: boolean;
  semantic_role?: string;
}

export interface DataSourceItem {
  id: string;
  name: string;
  description?: string;
  source_type: string;
  source_id?: string;
  record_count: number;
  schema?: {
    id: string;
    version: number;
    fields: DataFieldItem[];
  };
  created_at?: string;
  updated_at?: string;
}

export interface WebsitePageItem {
  id?: string;
  page_type: string; // home | search | detail | collection | custom | form
  title: string;
  slug: string;
  layout_config?: Record<string, any>;
  components?: Array<{
    id: string;
    type: string; // hero | search_bar | record_grid | record_table | metric_cards | document_viewer | markdown | filter_sidebar
    title?: string;
    data_source_id?: string;
    config?: Record<string, any>;
  }>;
  display_order?: number;
}

export interface WebsiteListItem {
  id: string;
  name: string;
  slug: string;
  description?: string;
  setup_id?: string;
  status: 'draft' | 'preview' | 'published' | 'unpublished' | 'archived';
  version_number: number;
  published_version?: number | null;
  collection_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface WebsiteDetail extends WebsiteListItem {
  theme: Record<string, any>;
  search_config: Record<string, any>;
  field_mappings: Record<string, any>;
  document_view: Record<string, any>;
  bindings: Record<string, any>;
  actions: Record<string, any>;
  conditions: Record<string, any>;
  computed_fields: Record<string, any>;
  pages: WebsitePageItem[];
  collections: Array<{
    id: string;
    name: string;
    slug: string;
    description?: string;
    filter_query?: Record<string, any>;
    display_order: number;
  }>;
}

export interface WebsiteDocumentItem {
  id: string;
  document_id: string;
  is_included: boolean;
  is_public: boolean;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  page_count: number;
  created_at?: string;
}

export interface SelectionAnalysis {
  selected_text: string;
  rel_x: number;
  rel_y: number;
  rel_width: number;
  rel_height: number;
  anchor_candidates: string[];
  structure_config: Record<string, any>;
  inferred_type: string;
  same_line_context: string;
  line_above_context: string;
}

/* ==================== Universal DataSources API ==================== */

export async function listDataSources(): Promise<DataSourceItem[]> {
  const res = await fetch('/api/admin/data-sources', {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load data sources.');
  return res.json();
}

export async function getDataSource(id: string): Promise<DataSourceItem & { fields: DataFieldItem[]; records: any[] }> {
  const res = await fetch(`/api/admin/data-sources/${encodeURIComponent(id)}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load data source details.');
  return res.json();
}

export async function createDataSource(payload: {
  name: string;
  description?: string;
  source_type?: string;
  fields?: Array<{
    key: string;
    label: string;
    type?: string;
    semantic_role?: string;
    required?: boolean;
    searchable?: boolean;
    sortable?: boolean;
    filterable?: boolean;
  }>;
}): Promise<DataSourceItem> {
  const res = await fetch('/api/admin/data-sources', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create data source.' }));
    throw new Error(err.detail || 'Failed to create data source.');
  }
  return res.json();
}

export async function syncSetupToDataSource(setupId: string): Promise<any> {
  const res = await fetch(`/api/admin/data-sources/sync-setup/${encodeURIComponent(setupId)}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to sync setup to data source.' }));
    throw new Error(err.detail || 'Failed to sync setup to data source.');
  }
  return res.json();
}

/* ==================== Websites API ==================== */

export async function listWebsites(): Promise<WebsiteListItem[]> {
  const res = await fetch('/api/admin/websites', {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load websites.');
  return res.json();
}

export async function getWebsite(id: string): Promise<WebsiteDetail> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load website details.');
  return res.json();
}

export async function createWebsite(payload: {
  name: string;
  slug?: string;
  description?: string;
  setup_id?: string;
  data_source_id?: string;
  theme?: Record<string, any>;
  search_config?: Record<string, any>;
  field_mappings?: Record<string, any>;
  document_view?: Record<string, any>;
  bindings?: Record<string, any>;
  actions?: Record<string, any>;
  conditions?: Record<string, any>;
  computed_fields?: Record<string, any>;
}): Promise<any> {
  const res = await fetch('/api/admin/websites', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create website.' }));
    throw new Error(err.detail || 'Failed to create website.');
  }
  return res.json();
}

export async function updateWebsite(id: string, payload: {
  name?: string;
  description?: string;
  setup_id?: string;
  data_source_id?: string;
  theme?: Record<string, any>;
  search_config?: Record<string, any>;
  field_mappings?: Record<string, any>;
  document_view?: Record<string, any>;
  bindings?: Record<string, any>;
  actions?: Record<string, any>;
  conditions?: Record<string, any>;
  computed_fields?: Record<string, any>;
  pages?: WebsitePageItem[];
}): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update website.' }));
    throw new Error(err.detail || 'Failed to update website.');
  }
  return res.json();
}

export async function publishWebsite(id: string): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}/publish`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to publish website.' }));
    throw new Error(err.detail || 'Failed to publish website.');
  }
  return res.json();
}

export async function unpublishWebsite(id: string): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}/unpublish`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to unpublish website.');
  return res.json();
}

export async function deleteWebsite(id: string): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete website.');
  return res.json();
}

/* ==================== Website Documents Membership API ==================== */

export async function listWebsiteDocuments(siteId: string): Promise<WebsiteDocumentItem[]> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(siteId)}/documents`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load website documents.');
  return res.json();
}

export async function addWebsiteDocuments(siteId: string, payload: {
  document_ids: string[];
  is_included?: boolean;
  is_public?: boolean;
}): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(siteId)}/documents`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to add documents to website.' }));
    throw new Error(err.detail || 'Failed to add documents to website.');
  }
  return res.json();
}

export async function syncWebsiteSetupDocuments(siteId: string, setupId: string): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(siteId)}/documents/sync-setup/${encodeURIComponent(setupId)}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to sync documents.' }));
    throw new Error(err.detail || 'Failed to sync documents.');
  }
  return res.json();
}

/* ==================== Visual PDF Locators API ==================== */

export async function analyzeSelection(payload: {
  page_width: number;
  page_height: number;
  bbox_x: number;
  bbox_y: number;
  bbox_width: number;
  bbox_height: number;
  selected_text: string;
  page_words: any[];
}): Promise<SelectionAnalysis> {
  const res = await fetch('/api/admin/locators/analyze', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to analyze selection.');
  return res.json();
}

export async function saveLocator(payload: {
  field_id?: string;
  new_field_name?: string;
  new_field_type?: string;
  setup_id?: string;
  name?: string;
  template_label?: string;
  document_id?: string;
  page_number?: number;
  selection_analysis: SelectionAnalysis;
  pixel_bbox?: number[];
}): Promise<any> {
  const res = await fetch('/api/admin/locators', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to save locator.' }));
    throw new Error(err.detail || 'Failed to save locator.');
  }
  return res.json();
}

export async function testLocatorCrossDocuments(locatorId: string, limit: number = 10): Promise<any> {
  const res = await fetch(`/api/admin/locators/${encodeURIComponent(locatorId)}/test`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ limit, confidence_threshold: 0.65 }),
  });
  if (!res.ok) throw new Error('Failed to run cross-document test.');
  return res.json();
}
