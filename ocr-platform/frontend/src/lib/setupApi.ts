/**
 * Setup and Field API client adapters.
 */
import { api } from './api';

export interface SetupItem {
  id: string;
  name: string;
  slug: string;
  description: string;
  field_count: number;
  status: string;
  version_id: string | null;
  version_number: number;
  created_at: string;
  last_scanned: string | null;
  fields?: FieldItem[];
}

export type SetupSummary = SetupItem;
export type SetupDetail = SetupItem;

export interface CandidateItem {
  value: string;
  context_before: string;
  context_after: string;
  anchor_found: string | null;
  confidence: number;
  page?: number;
}

export interface FieldItem {
  field_id: string;
  display_name: string;
  human_pattern: string;
  output_type: string;
  status: string;
  confidence_label: string;
  confidence_score: number;
  last_example_found?: string | null;
  explanation?: string[];
  strategy_used?: string;
  ambiguous?: boolean;
  candidates?: CandidateItem[];
}

export interface ScanSetupValue {
  field_id: string;
  display_name: string;
  value: string | null;
  raw_value: string | null;
  confidence_score: number;
  confidence_label: string;
  why: string[];
  validation_passed?: boolean;
}

export interface ScanSetupResult {
  setup_id: string;
  setup_name: string;
  document_id: string;
  overall_confidence: number;
  overall_confidence_label: string;
  extracted_values: ScanSetupValue[];
}

export const setupApi = {
  async listSetups(): Promise<SetupItem[]> {
    const res = await fetch('/api/setups');
    if (!res.ok) throw new Error('Failed to list setups');
    return res.json();
  },

  async createSetup(name: string, description?: string, fields?: any[]): Promise<SetupItem> {
    const res = await fetch('/api/setups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, fields }),
    });
    if (!res.ok) throw new Error('Failed to create setup');
    return res.json();
  },

  async getSetup(id: string): Promise<SetupItem> {
    const res = await fetch(`/api/setups/${id}`);
    if (!res.ok) throw new Error('Failed to get setup');
    return res.json();
  },

  async updateSetup(id: string, name: string, description?: string): Promise<SetupItem> {
    const res = await fetch(`/api/setups/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) throw new Error('Failed to update setup');
    return res.json();
  },

  async deleteSetup(id: string): Promise<void> {
    const res = await fetch(`/api/setups/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete setup');
  },

  async scanWithSetup(setupId: string, documentId: string): Promise<ScanSetupResult> {
    const res = await fetch(`/api/setups/${setupId}/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId }),
    });
    if (!res.ok) throw new Error('Failed to scan with setup');
    return res.json();
  },

  async listFields(setupId: string): Promise<FieldItem[]> {
    const res = await fetch(`/api/setups/${setupId}/fields`);
    if (!res.ok) throw new Error('Failed to list fields');
    return res.json();
  },

  async addField(
    setupId: string,
    payload: {
      display_name: string;
      human_pattern?: string;
      examples?: string[];
      description?: string;
      ocr_text?: string;
      ocr_tolerant?: boolean;
    }
  ): Promise<FieldItem> {
    const res = await fetch(`/api/setups/${setupId}/fields`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to add field');
    return res.json();
  },

  async deleteField(setupId: string, fieldId: string): Promise<void> {
    const res = await fetch(`/api/setups/${setupId}/fields/${fieldId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete field');
  },

  async getCandidates(setupId: string, fieldId: string, documentId: string) {
    const res = await fetch(
      `/api/setups/${setupId}/fields/${fieldId}/candidates?document_id=${encodeURIComponent(documentId)}`
    );
    if (!res.ok) throw new Error('Failed to get candidates');
    return res.json();
  },

  async resolveCandidate(setupId: string, fieldId: string, documentId: string, chosenValue: string) {
    const res = await fetch(`/api/setups/${setupId}/fields/${fieldId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, chosen_value: chosenValue }),
    });
    if (!res.ok) throw new Error('Failed to resolve candidate');
    return res.json();
  },
};

export const listSetups = () => setupApi.listSetups();
export const getSetup = (id: string) => setupApi.getSetup(id);

