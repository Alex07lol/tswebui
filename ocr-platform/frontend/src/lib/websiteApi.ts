/**
 * API client for Document Websites, Versions, Publications, and Visual PDF Locators.
 */

export interface WebsiteListItem {
  id: string;
  name: string;
  slug: string;
  description?: string;
  setup_id?: string;
  status: 'draft' | 'preview' | 'published' | 'unpublished' | 'archived';
  version_number: number;
  collection_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface WebsiteDetail extends WebsiteListItem {
  theme: Record<string, any>;
  search_config: Record<string, any>;
  field_mappings: Record<string, any>;
  document_view: Record<string, any>;
  collections: Array<{
    id: string;
    name: string;
    slug: string;
    description?: string;
    display_order: number;
  }>;
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

export async function listWebsites(): Promise<WebsiteListItem[]> {
  const res = await fetch('/api/admin/websites');
  if (!res.ok) throw new Error('Failed to load websites.');
  return res.json();
}

export async function getWebsite(id: string): Promise<WebsiteDetail> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error('Failed to load website details.');
  return res.json();
}

export async function createWebsite(payload: {
  name: string;
  slug?: string;
  description?: string;
  setup_id?: string;
  theme?: Record<string, any>;
  search_config?: Record<string, any>;
  field_mappings?: Record<string, any>;
  document_view?: Record<string, any>;
}): Promise<any> {
  const res = await fetch('/api/admin/websites', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create website.' }));
    throw new Error(err.detail || 'Failed to create website.');
  }
  return res.json();
}

export async function publishWebsite(id: string): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}/publish`, {
    method: 'POST',
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
  });
  if (!res.ok) throw new Error('Failed to unpublish website.');
  return res.json();
}

export async function deleteWebsite(id: string): Promise<any> {
  const res = await fetch(`/api/admin/websites/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete website.');
  return res.json();
}

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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to analyze selection.');
  return res.json();
}

export async function saveLocator(payload: {
  field_id: string;
  name?: string;
  template_label?: string;
  document_id?: string;
  page_number?: number;
  selection_analysis: SelectionAnalysis;
  pixel_bbox?: number[];
}): Promise<any> {
  const res = await fetch('/api/admin/locators', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ limit, confidence_threshold: 0.65 }),
  });
  if (!res.ok) throw new Error('Failed to run cross-document test.');
  return res.json();
}
