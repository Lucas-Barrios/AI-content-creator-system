import type {
  ApiErrorBody,
  BrandProfile,
  BrandProfileRequest,
  CampaignRequest,
  CampaignResult,
  CampaignSummary,
  FeedbackRequest,
  FeedbackResponse,
  GenerateRequest,
  GenerateResponse,
  GeneratedOutputRecord,
  HealthResponse,
  KnowledgeIngestionResponse,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  KnowledgeTextRequest,
  RepurposeRequest,
  RepurposeResult,
  UploadedFile
} from "@/lib/types";

const defaultHeaders = {
  "Content-Type": "application/json"
};

export class ApiClientError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseError(response: Response): Promise<ApiClientError> {
  let body: ApiErrorBody | undefined;
  try {
    body = (await response.json()) as ApiErrorBody;
  } catch {
    body = undefined;
  }

  return new ApiClientError(
    body?.error ?? body?.detail ?? `Request failed with status ${response.status}`,
    response.status,
    body?.detail
  );
}

async function requestJson<T>(url: string, init: RequestInit, retries = 1): Promise<T> {
  try {
    const response = await fetch(url, init);
    if (!response.ok) {
      throw await parseError(response);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (retries > 0 && !(error instanceof ApiClientError && error.status < 500)) {
      await new Promise((resolve) => setTimeout(resolve, 350));
      return requestJson<T>(url, init, retries - 1);
    }
    throw error;
  }
}

export async function generateContent(payload: GenerateRequest): Promise<GenerateResponse> {
  return requestJson<GenerateResponse>("/api/generate", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function uploadFiles(files: File[]): Promise<UploadedFile[]> {
  if (!files.length) return [];

  const form = new FormData();
  files.forEach((file) => form.append("files", file));

  return requestJson<UploadedFile[]>("/api/upload", {
    method: "POST",
    body: form
  });
}

export async function submitFeedback(payload: FeedbackRequest): Promise<FeedbackResponse> {
  return requestJson<FeedbackResponse>("/api/feedback", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function getBackendHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/api/health", { method: "GET" }, 0);
}

export async function generateCampaign(payload: CampaignRequest): Promise<CampaignResult> {
  return requestJson<CampaignResult>("/api/campaigns/generate", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function listCampaigns(clientId: string, projectId?: string): Promise<{ campaigns: CampaignSummary[]; count: number }> {
  const params = new URLSearchParams({ clientId });
  if (projectId) params.set("projectId", projectId);
  return requestJson<{ campaigns: CampaignSummary[]; count: number }>(`/api/campaigns?${params.toString()}`, { method: "GET" });
}

export async function repurposeContent(payload: RepurposeRequest): Promise<RepurposeResult> {
  return requestJson<RepurposeResult>("/api/repurpose", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function ingestKnowledgeText(payload: KnowledgeTextRequest): Promise<KnowledgeIngestionResponse> {
  return requestJson<KnowledgeIngestionResponse>("/api/knowledge/ingest-text", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function ingestKnowledgeFile(payload: {
  organizationId: string;
  clientId: string;
  projectId?: string;
  title: string;
  sourceKind: string;
  contentType?: string;
  language?: string;
  channel?: string;
  tags?: string[];
  file: File;
}): Promise<KnowledgeIngestionResponse> {
  const form = new FormData();
  form.append("organizationId", payload.organizationId);
  form.append("clientId", payload.clientId);
  if (payload.projectId) form.append("projectId", payload.projectId);
  form.append("title", payload.title);
  form.append("sourceKind", payload.sourceKind);
  if (payload.contentType) form.append("contentType", payload.contentType);
  if (payload.language) form.append("language", payload.language);
  if (payload.channel) form.append("channel", payload.channel);
  form.append("tags", (payload.tags ?? []).join(","));
  form.append("file", payload.file, payload.file.name);

  return requestJson<KnowledgeIngestionResponse>("/api/knowledge/ingest-file", {
    method: "POST",
    body: form
  });
}

export async function searchKnowledge(payload: KnowledgeSearchRequest): Promise<KnowledgeSearchResponse> {
  return requestJson<KnowledgeSearchResponse>("/api/knowledge/search", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function getBrandProfile(clientId: string, projectId?: string): Promise<{ profile: BrandProfile | null }> {
  const params = new URLSearchParams({ clientId });
  if (projectId) params.set("projectId", projectId);
  return requestJson<{ profile: BrandProfile | null }>(`/api/brand-profile?${params.toString()}`, { method: "GET" });
}

export async function saveBrandProfile(payload: BrandProfileRequest): Promise<{ profile: BrandProfile }> {
  return requestJson<{ profile: BrandProfile }>("/api/brand-profile", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload)
  });
}

export async function listGeneratedOutputs(clientId: string, projectId?: string): Promise<{ outputs: GeneratedOutputRecord[]; count: number }> {
  const params = new URLSearchParams({ clientId });
  if (projectId) params.set("projectId", projectId);
  return requestJson<{ outputs: GeneratedOutputRecord[]; count: number }>(`/api/generated-outputs?${params.toString()}`, { method: "GET" });
}

export function downloadMarkdown(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
