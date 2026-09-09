/**
 * Teach From Examples API client.
 */

export interface TeachLayoutItem {
  id: string;
  label: string;
  document_count: number;
  sample_document_id?: string | null;
}

export interface TeachProposalItem {
  id: string;
  suggested_name: string;
  human_pattern: string;
  example_found: string;
  confidence_label: string;
  confidence_score: number;
  why: string[];
  action: 'pending' | 'use' | 'edit' | 'skip';
}

export interface TeachSessionResponse {
  session_id: string;
  status: 'uploaded' | 'analyzing' | 'completed';
  layout_count?: number;
  proposal_count?: number;
}

export const teachApi = {
  async startTeachSession(documentIds: string[]): Promise<TeachSessionResponse> {
    const res = await fetch('/api/teach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_ids: documentIds }),
    });
    if (!res.ok) throw new Error('Failed to start teach session');
    return res.json();
  },

  async getSessionStatus(sessionId: string): Promise<TeachSessionResponse> {
    const res = await fetch(`/api/teach/${sessionId}`);
    if (!res.ok) throw new Error('Failed to get teach session status');
    return res.json();
  },

  async getLayouts(sessionId: string): Promise<TeachLayoutItem[]> {
    const res = await fetch(`/api/teach/${sessionId}/layouts`);
    if (!res.ok) throw new Error('Failed to get layouts');
    const data = await res.json();
    return data.layouts || [];
  },

  async getProposals(sessionId: string): Promise<TeachProposalItem[]> {
    const res = await fetch(`/api/teach/${sessionId}/proposals`);
    if (!res.ok) throw new Error('Failed to get proposals');
    const data = await res.json();
    return data.proposals || [];
  },

  async saveSetupFromTeach(
    sessionId: string,
    setupName: string,
    acceptedProposalIds?: string[]
  ): Promise<any> {
    const res = await fetch(`/api/teach/${sessionId}/save-setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        setup_name: setupName,
        accepted_proposal_ids: acceptedProposalIds,
      }),
    });
    if (!res.ok) throw new Error('Failed to save setup from teach session');
    return res.json();
  },
};
