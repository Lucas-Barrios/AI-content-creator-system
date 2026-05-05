import { NextResponse } from "next/server";

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

export async function POST(request: Request) {
  if (!backendBaseUrl) {
    return NextResponse.json(
      {
        error: "Python backend URL is not configured.",
        detail: "Set PYTHON_API_BASE_URL before using chat."
      },
      { status: 500 }
    );
  }

  const body = await request.json();
  const base = backendBaseUrl.replace(/\/$/, "");

  const streamResponse = await fetch(`${base}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (streamResponse.ok && streamResponse.body) {
    return new Response(streamResponse.body, {
      status: 200,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache, no-transform"
      }
    });
  }

  const fallbackResponse = await fetch(`${base}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!fallbackResponse.ok) {
    return NextResponse.json(
      { error: "Chat request failed.", detail: await readBackendError(fallbackResponse) },
      { status: fallbackResponse.status }
    );
  }

  const data = (await fallbackResponse.json()) as Record<string, unknown>;
  const text =
    typeof data.content === "string"
      ? data.content
      : typeof data.message === "string"
        ? data.message
        : typeof data.output === "string"
          ? data.output
          : "";

  return new Response(text, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache"
    }
  });
}
