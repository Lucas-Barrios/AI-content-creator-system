import { backendHeaders } from "@/lib/server/backend";
import type { BrandProfile, GenerateRequest, GenerateResponse, KnowledgeMatch, SourceFile } from "@/lib/types";
import type { LegacyGenerationClient } from "./types";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

function backendUrl(path: string): string {
  if (!backendBaseUrl) throw new Error("PYTHON_API_BASE_URL is not configured.");
  return `${backendBaseUrl.replace(/\/$/, "")}${path}`;
}

export async function readBackendError(response: Response): Promise<string> {
  const raw = await response.text();
  if (!raw) return `Backend returned status ${response.status}.`;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return typeof parsed.detail === "string" ? parsed.detail : typeof parsed.error === "string" ? parsed.error : raw;
  } catch {
    return raw;
  }
}

function wordCount(content: string): number {
  return content.split(/\s+/).filter(Boolean).length;
}

export function normaliseGenerateResponse(
  body: unknown,
  request: GenerateRequest,
  metadata?: Partial<GenerateResponse["metadata"]>,
): GenerateResponse {
  const record = (body ?? {}) as Record<string, unknown>;
  const content =
    typeof record.content === "string"
      ? record.content
      : typeof record.output === "string"
        ? record.output
        : typeof record.result === "string"
          ? record.result
          : "";

  if (!content.trim()) throw new Error("Backend response did not include generated content.");

  const rawSources = Array.isArray(record.sources)
    ? record.sources
    : Array.isArray(record.file_meta)
      ? record.file_meta
      : Array.isArray(record.fileMeta)
        ? record.fileMeta
        : [];

  const sources: SourceFile[] = rawSources
    .map((item) => item as Record<string, unknown>)
    .filter((item) => typeof item.filename === "string")
    .map((item) => ({
      filename: item.filename as string,
      words: typeof item.words === "number" ? item.words : Number(item.words ?? 0),
      source: item.source === "secondary" ? "secondary" : "primary",
    }));

  return {
    content,
    sources,
    metadata: {
      topic: request.topic,
      contentType: request.contentType,
      language: request.language,
      tone: request.tone,
      length: request.length,
      knowledgeBase: request.knowledgeBase,
      wordCount: wordCount(content),
      generatedAt: new Date().toISOString(),
      generationId: crypto.randomUUID(),
      ...metadata,
    },
  };
}

async function fetchJson<T>(url: string, init: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) throw new Error(await readBackendError(response));
  return (await response.json()) as T;
}

export class PythonGenerationClient implements LegacyGenerationClient {
  async generate(payload: GenerateRequest): Promise<GenerateResponse> {
    const body = await fetchJson<unknown>(backendUrl("/generate"), {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return normaliseGenerateResponse(body, payload, {
      framework: "legacy-python",
    });
  }

  async generateText(input: { system?: string; prompt: string; metadata?: Record<string, unknown> }): Promise<string> {
    const body = await fetchJson<Record<string, unknown>>(backendUrl("/llm/generate"), {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ system: input.system ?? "", prompt: input.prompt, metadata: input.metadata }),
    });
    const content = typeof body.content === "string" ? body.content : "";
    if (!content.trim()) throw new Error("LLM response did not include content.");
    return content;
  }

  async getBrandProfile(input: { clientId: string; projectId?: string }): Promise<BrandProfile | null> {
    const params = new URLSearchParams({ clientId: input.clientId });
    if (input.projectId) params.set("projectId", input.projectId);
    const body = await fetchJson<{ profile: BrandProfile | null }>(backendUrl(`/brand-profile?${params.toString()}`), {
      method: "GET",
      headers: backendHeaders(),
      cache: "no-store",
    });
    return body.profile;
  }

  async searchKnowledge(input: {
    query: string;
    clientId: string;
    projectId?: string;
    contentType?: string;
    language?: string;
    channel?: string;
  }): Promise<KnowledgeMatch[]> {
    const body = await fetchJson<{ matches: KnowledgeMatch[] }>(backendUrl("/knowledge/search"), {
      method: "POST",
      headers: backendHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        query: input.query,
        clientId: input.clientId,
        projectId: input.projectId,
        contentType: input.contentType,
        language: input.language,
        channel: input.channel,
        matchCount: 6,
        matchThreshold: 0.55,
      }),
    });
    return body.matches ?? [];
  }

  async saveGeneratedOutput(input: {
    request: GenerateRequest;
    response: GenerateResponse;
    prompt?: string;
    retrievedChunkIds?: string[];
  }): Promise<void> {
    if (!input.request.organizationId || !input.request.clientId || !input.request.projectId) return;
    try {
      await fetchJson<unknown>(backendUrl("/generated-outputs"), {
        method: "POST",
        headers: backendHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          organizationId: input.request.organizationId,
          clientId: input.request.clientId,
          projectId: input.request.projectId,
          title: input.request.topic,
          prompt: input.prompt,
          content: input.response.content,
          contentType: input.request.contentType,
          channel: input.request.contentType === "social" || input.request.contentType === "social_post" ? "linkedin" : undefined,
          language: input.request.language,
          status: "draft",
          wordCount: input.response.metadata.wordCount,
          retrievedChunkIds: input.retrievedChunkIds ?? [],
          metadata: input.response.metadata,
        }),
      });
    } catch (error) {
      console.warn("Generated output persistence skipped:", error);
    }
  }
}
