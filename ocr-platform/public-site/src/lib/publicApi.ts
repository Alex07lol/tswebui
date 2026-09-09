export interface PublicSiteConfig {
  name: string;
  slug: string;
  description?: string;
  site_title: string;
  tagline?: string;
  header_logo?: string;
  theme?: {
    preset?: string;
    primary_color?: string;
    accent_color?: string;
    background?: string;
    font_family?: string;
  };
  search_config?: {
    searchable_fields?: string[];
    enable_fuzzy?: boolean;
    default_sort?: string;
  };
  field_mappings?: {
    title_field?: string;
    drawing_number_field?: string;
    badge_fields?: string[];
    metadata_fields?: string[];
  };
  document_view?: {
    show_pdf_viewer?: boolean;
    allow_download?: boolean;
    show_thumbnails?: boolean;
  };
  collections?: Array<{
    name: string;
    slug: string;
    description?: string;
  }>;
}

export interface SearchHit {
  document_id: string;
  title: string;
  drawing_number?: string;
  score: number;
  rank_tier: string;
  structured_fields: Record<string, any>;
  snippet?: string;
  view_url: string;
  file_url: string;
  thumbnail_url: string;
}

export interface SearchResponse {
  query?: string;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  hits: SearchHit[];
}

export interface DocumentDetail {
  document_id: string;
  title: string;
  drawing_number?: string;
  filename: string;
  mime_type: string;
  page_count: number;
  structured_fields: Record<string, any>;
  file_url: string;
  thumbnail_url: string;
  published_at?: string;
}

export async function fetchPublicSite(slug: string): Promise<PublicSiteConfig> {
  const res = await fetch(`/api/public/sites/${encodeURIComponent(slug)}`);
  if (!res.ok) {
    throw new Error(res.status === 403 ? 'This document portal is currently offline or unpublished.' : 'Document portal not found.');
  }
  return res.json();
}

export async function searchPublicSite(
  slug: string,
  query: string = '',
  page: number = 1,
  sortBy: string = 'relevance'
): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  params.set('page', String(page));
  params.set('sort_by', sortBy);

  const res = await fetch(`/api/public/sites/${encodeURIComponent(slug)}/search?${params.toString()}`);
  if (!res.ok) {
    throw new Error('Failed to execute search query.');
  }
  return res.json();
}

export async function fetchPublicDocument(slug: string, docId: string): Promise<DocumentDetail> {
  const res = await fetch(`/api/public/sites/${encodeURIComponent(slug)}/documents/${encodeURIComponent(docId)}`);
  if (!res.ok) {
    throw new Error('Document not found or private.');
  }
  return res.json();
}
