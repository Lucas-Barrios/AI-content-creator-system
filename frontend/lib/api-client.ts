import type { ApiErrorBody, FeedbackRequest, FeedbackResponse, GenerateRequest, GenerateResponse, UploadedFile } from "@/lib/types";

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
    body?.error ?? `Request failed with status ${response.status}`,
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

export function downloadMarkdown(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
