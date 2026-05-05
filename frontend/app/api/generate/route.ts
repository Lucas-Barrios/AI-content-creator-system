import { NextResponse } from "next/server";
import type { GenerateRequest, GenerateResponse, SourceFile } from "@/lib/types";

export const runtime = "nodejs";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

async function readBackendError(response: Response): Promise<string> {
  const raw = await response.text();
  if (!raw) return `Backend returned status ${response.status}.`;

  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const detail = parsed.detail;
    if (typeof detail === "string") return detail;
    if (typeof parsed.error === "string") return parsed.error;
  } catch {
    return raw;
  }

  return raw;
}

function normaliseGenerateResponse(body: unknown, request: GenerateRequest): GenerateResponse {
  const record = (body ?? {}) as Record<string, unknown>;
  const content =
    typeof record.content === "string"
      ? record.content
      : typeof record.output === "string"
        ? record.output
        : typeof record.result === "string"
          ? record.result
          : "";

  if (!content.trim()) {
    throw new Error("Backend response did not include generated content.");
  }

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
      source: item.source === "secondary" ? "secondary" : "primary"
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
      wordCount: content.split(/\s+/).filter(Boolean).length,
      generatedAt: new Date().toISOString(),
      generationId: crypto.randomUUID()
    }
  };
}

export async function POST(request: Request) {
  if (!backendBaseUrl) {
    return NextResponse.json(
      {
        error: "Python backend URL is not configured.",
        detail: "Set PYTHON_API_BASE_URL in frontend/.env.local, for example http://localhost:8000."
      },
      { status: 500 }
    );
  }

  let payload: GenerateRequest;
  try {
    payload = (await request.json()) as GenerateRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  if (!payload.topic?.trim()) {
    return NextResponse.json({ error: "Topic is required." }, { status: 400 });
  }

  const backendResponse = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!backendResponse.ok) {
    const detail = await readBackendError(backendResponse);
    return NextResponse.json(
      { error: "Content generation failed.", detail },
      { status: backendResponse.status }
    );
  }

  try {
    const body = await backendResponse.json();
    return NextResponse.json(normaliseGenerateResponse(body, payload));
  } catch (error) {
    return NextResponse.json(
      {
        error: "Could not parse backend response.",
        detail: error instanceof Error ? error.message : "Unknown parser error"
      },
      { status: 502 }
    );
  }
}
