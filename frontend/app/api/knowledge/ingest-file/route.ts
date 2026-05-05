import { NextResponse } from "next/server";

export const runtime = "nodejs";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

async function readError(response: Response): Promise<string> {
  const raw = await response.text();
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return typeof parsed.detail === "string" ? parsed.detail : typeof parsed.error === "string" ? parsed.error : raw;
  } catch {
    return raw || `Backend returned status ${response.status}.`;
  }
}

export async function POST(request: Request) {
  if (!backendBaseUrl) return NextResponse.json({ error: "PYTHON_API_BASE_URL not configured." }, { status: 500 });
  const form = await request.formData();
  const response = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/knowledge/ingest-file`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    return NextResponse.json({ error: "Knowledge file ingestion failed.", detail: await readError(response) }, { status: response.status });
  }
  return NextResponse.json(await response.json());
}
