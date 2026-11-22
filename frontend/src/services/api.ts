import {
  CreateApplicationPayload,
  DocumentDetail,
  LoanApplication,
  UnderwritePayload,
  UnderwritingResult,
} from '../types';

const API_BASE = '/api/v1';

export async function fetchApplications(): Promise<LoanApplication[]> {
  const resp = await fetch(`${API_BASE}/applications`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch applications: ${resp.statusText}`);
  }
  const data = await resp.json();
  return data.items || [];
}

export async function fetchApplication(id: string): Promise<LoanApplication> {
  const resp = await fetch(`${API_BASE}/applications/${id}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch application: ${resp.statusText}`);
  }
  return resp.json();
}

export async function createApplication(
  payload: CreateApplicationPayload
): Promise<LoanApplication> {
  const resp = await fetch(`${API_BASE}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create application: ${resp.statusText}`);
  }
  return resp.json();
}

export async function deleteApplication(id: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/applications/${id}`, {
    method: 'DELETE',
  });
  if (!resp.ok) {
    throw new Error(`Failed to delete application: ${resp.statusText}`);
  }
}

export async function uploadDocument(
  file: File,
  loanApplicationId: string,
  documentType?: string
): Promise<DocumentDetail> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('loan_application_id', loanApplicationId);
  if (documentType) {
    formData.append('document_type', documentType);
  }

  const resp = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to upload document: ${resp.statusText}`);
  }
  return resp.json();
}

export async function fetchDocument(id: string): Promise<DocumentDetail> {
  const resp = await fetch(`${API_BASE}/documents/${id}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch document: ${resp.statusText}`);
  }
  return resp.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/documents/${id}`, {
    method: 'DELETE',
  });
  if (!resp.ok) {
    throw new Error(`Failed to delete document: ${resp.statusText}`);
  }
}

export function getDocumentDownloadUrl(id: string): string {
  return `${API_BASE}/documents/${id}/download`;
}

export async function triggerUnderwriting(
  applicationId: string,
  payload: UnderwritePayload = {}
): Promise<UnderwritingResult> {
  const resp = await fetch(`${API_BASE}/applications/${applicationId}/underwrite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Underwriting pipeline failed: ${resp.statusText}`);
  }
  return resp.json();
}

export async function fetchUnderwriting(
  applicationId: string
): Promise<UnderwritingResult> {
  const resp = await fetch(`${API_BASE}/applications/${applicationId}/underwrite`);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to load underwriting report: ${resp.statusText}`);
  }
  return resp.json();
}
