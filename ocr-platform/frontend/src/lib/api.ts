/**
 * Typed API Client for the OCR Platform Backend
 */

export interface DocumentItem {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  file_hash: string | null;
  page_count: number | null;
  status: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OCRWord {
  text: string;
  confidence: number;
  bounding_box: BoundingBox;
  word_index: number;
  line_number: number;
  block_number: number;
}

export interface OCRPage {
  page_number: number;
  width: number;
  height: number;
  text: string;
  words: OCRWord[];
}

export interface OCRResult {
  document_id: string;
  full_text: string;
  pages: OCRPage[];
  provider: string;
  provider_version: string;
}

export interface OCRJob {
  id: string;
  document_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  provider: string;
  language: string;
  error_message?: string | null;
}

export interface ExtractionRule {
  id?: string;
  rule_name?: string;
  strategy: string; // anchored_pattern, direct_pattern, same_line, next_line, region, table
  anchor_config?: {
    value: string;
    match?: 'exact' | 'fuzzy' | 'regex';
    minimum_similarity?: number;
  };
  search_config?: {
    direction?: 'after' | 'before' | 'left' | 'right';
    scope?: 'same_line' | 'next_line' | 'multi_line' | 'region';
    max_lines?: number;
  };
  pattern_config?: {
    type?: 'regex' | 'template' | 'typed' | 'example';
    value?: string;
    examples?: string[];
    named_type?: string;
  };
  region_config?: {
    page?: number;
    x_min?: number;
    y_min?: number;
    x_max?: number;
    y_max?: number;
  };
  priority: number;
  is_enabled: boolean;
}

export interface ExtractionField {
  id?: string;
  field_id: string;
  display_name: string;
  output_variable: string;
  output_type: string; // string, integer, decimal, date, currency, boolean
  required: boolean;
  priority: number;
  rules: ExtractionRule[];
}

export interface ConfigurationVersion {
  id: string;
  configuration_id: string;
  version_number: number;
  status: string;
  schema_version: number;
  config_snapshot?: string | null;
  change_notes?: string | null;
  fields?: ExtractionField[];
}

export interface Configuration {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  versions: Array<{
    id: string;
    version_number: number;
    status: string;
  }>;
}

export interface ExtractedEvidence {
  rule_id?: string;
  anchor_text?: string;
  source_line?: string;
  ocr_confidence?: number;
  bbox_x?: number;
  bbox_y?: number;
  bbox_width?: number;
  bbox_height?: number;
  page_number?: number;
}

export interface ExtractedValue {
  id?: string;
  field_id: string;
  output_variable: string;
  raw_value: string | null;
  normalized_value: string | null;
  final_confidence: number | null;
  validation_passed: boolean | null;
  validation_message: string | null;
  evidence: ExtractedEvidence[];
}

export interface ExtractionResult {
  job_id: string;
  document_id: string;
  config_version_id: string;
  overall_confidence: number | null;
  values: ExtractedValue[];
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  document_count: number;
  status: string;
  documents?: Array<{
    document_id: string;
    filename?: string;
  }>;
}

export interface PatternProposal {
  id: string;
  cluster_id: string;
  field_name: string;
  display_name: string | null;
  anchor: string | null;
  strategy: string | null;
  pattern_json: string | null;
  confidence_anchor: number | null;
  confidence_pattern: number | null;
  confidence_position: number | null;
  confidence_overall: number | null;
  status: 'pending' | 'approved' | 'rejected' | 'edited';
}

export interface DocumentCluster {
  id: string;
  run_id: string;
  label: string;
  document_count: number;
  is_outlier: boolean;
  proposals: PatternProposal[];
}

export interface DiscoveryRun {
  id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  documents_processed: number;
  clusters_found: number;
  proposals_generated: number;
  error_message: string | null;
  clusters?: DocumentCluster[];
}

export interface TestCase {
  id: string;
  suite_id: string;
  document_id: string | null;
  name: string;
  expected_values_json: string | null;
  validation_mode: string;
  is_regression: boolean;
}

export interface TestSuite {
  id: string;
  configuration_id: string;
  name: string;
  description: string | null;
  cases?: TestCase[];
}

export interface TestRun {
  id: string;
  suite_id: string;
  config_version_id: string | null;
  status: 'pending' | 'running' | 'passed' | 'failed';
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number | null;
  results_json: string | null;
}

export interface AuditLog {
  id: string;
  event_type: string;
  actor_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  details_json: string | null;
  created_at: string;
}

const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errorText = res.statusText;
    try {
      const errJson = await res.json();
      errorText = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      // fallback to statusText
    }
    throw new Error(errorText || `Request failed with status ${res.status}`);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const api = {
  // Health
  async getHealth(): Promise<{ status: string; version: string; ocr_provider: string }> {
    return request('/health');
  },

  // Documents
  async listDocuments(skip = 0, limit = 100): Promise<DocumentItem[]> {
    return request(`/documents?skip=${skip}&limit=${limit}`);
  },

  async getDocument(id: string): Promise<DocumentItem> {
    return request(`/documents/${id}`);
  },

  async uploadDocument(file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || 'Failed to upload document');
    }
    return res.json();
  },

  async deleteDocument(id: string): Promise<void> {
    await request(`/documents/${id}`, { method: 'DELETE' });
  },

  getDocumentFileUrl(id: string): string {
    return `${BASE_URL}/documents/${id}/file`;
  },

  getDocumentPageImageUrl(id: string, pageNumber = 1): string {
    return `${BASE_URL}/documents/${id}/pages/${pageNumber}/image`;
  },

  // OCR
  async listOCRProviders(): Promise<string[]> {
    return request('/ocr/providers');
  },

  async runOCR(documentId: string, language = 'eng', psm = 6): Promise<OCRJob> {
    return request('/ocr/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, language, options: { psm } }),
    });
  },

  async getOCRJob(jobId: string): Promise<OCRJob> {
    return request(`/ocr/jobs/${jobId}`);
  },

  async getOCRResult(documentId: string): Promise<OCRResult> {
    return request(`/ocr/documents/${documentId}/result`);
  },

  // Configurations
  async listConfigurations(): Promise<Configuration[]> {
    return request('/configurations');
  },

  async createConfiguration(data: { name: string; slug: string; description?: string }): Promise<Configuration> {
    return request('/configurations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async getConfiguration(id: string): Promise<Configuration> {
    return request(`/configurations/${id}`);
  },

  async createConfigurationVersion(
    configId: string,
    data: {
      config_snapshot?: string;
      change_notes?: string;
      fields?: ExtractionField[];
    }
  ): Promise<ConfigurationVersion> {
    return request(`/configurations/${configId}/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async getConfigurationVersion(configId: string, versionId: string): Promise<ConfigurationVersion> {
    return request(`/configurations/${configId}/versions/${versionId}`);
  },

  async testConfigurationVersion(versionId: string, documentId: string): Promise<ExtractionResult> {
    return request(`/configurations/versions/${versionId}/test?document_id=${documentId}`, {
      method: 'POST',
    });
  },

  // Extraction Jobs & Results
  async runExtraction(documentId: string, configVersionId: string): Promise<{ job_id: string; status: string }> {
    return request('/extraction/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, config_version_id: configVersionId }),
    });
  },

  async getExtractionResult(documentId: string): Promise<ExtractionResult> {
    return request(`/extraction/documents/${documentId}/results`);
  },

  async getExtractionJobResult(jobId: string): Promise<ExtractionResult> {
    return request(`/results/jobs/${jobId}`);
  },

  getExportJobUrl(jobId: string, format: 'json' | 'csv'): string {
    return `${BASE_URL}/results/jobs/${jobId}/export?format=${format}`;
  },

  // Datasets & Pattern Discovery
  async listDatasets(): Promise<Dataset[]> {
    return request('/datasets');
  },

  async createDataset(data: { name: string; description?: string }): Promise<Dataset> {
    return request('/datasets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async addDocumentToDataset(datasetId: string, documentId: string): Promise<void> {
    await request(`/datasets/${datasetId}/documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId }),
    });
  },

  async startDiscoveryRun(datasetId: string): Promise<DiscoveryRun> {
    return request('/discovery/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId }),
    });
  },

  async getDiscoveryRun(runId: string): Promise<DiscoveryRun> {
    return request(`/discovery/runs/${runId}`);
  },

  async listProposals(runId: string): Promise<PatternProposal[]> {
    return request(`/discovery/runs/${runId}/proposals`);
  },

  async updateProposalStatus(
    proposalId: string,
    status: 'approved' | 'rejected' | 'edited',
    customField?: Partial<PatternProposal>
  ): Promise<PatternProposal> {
    return request(`/discovery/proposals/${proposalId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, ...customField }),
    });
  },

  async generateConfigurationFromRun(
    runId: string,
    data: { name: string; slug: string }
  ): Promise<Configuration> {
    return request(`/discovery/runs/${runId}/generate-configuration`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  // Test Suites & Regression
  async listTestSuites(): Promise<TestSuite[]> {
    return request('/tests/suites');
  },

  async createTestSuite(data: { configuration_id: string; name: string; description?: string }): Promise<TestSuite> {
    return request('/tests/suites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async addTestCase(
    suiteId: string,
    data: {
      name: string;
      document_id: string;
      expected_values: Record<string, string>;
      validation_mode?: string;
      is_regression?: boolean;
    }
  ): Promise<TestCase> {
    return request(`/tests/suites/${suiteId}/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        suite_id: suiteId,
        document_id: data.document_id,
        name: data.name,
        expected_values_json: JSON.stringify(data.expected_values),
        validation_mode: data.validation_mode || 'exact',
        is_regression: data.is_regression ?? false,
      }),
    });
  },

  async runTestSuite(suiteId: string, configVersionId?: string): Promise<TestRun> {
    return request(`/tests/suites/${suiteId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config_version_id: configVersionId }),
    });
  },

  async getTestRun(runId: string): Promise<TestRun> {
    return request(`/tests/runs/${runId}`);
  },

  // Audit Logs
  async listAuditLogs(limit = 100): Promise<AuditLog[]> {
    return request(`/audit-logs?limit=${limit}`);
  },
};
