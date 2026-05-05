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

export async function GET(request: Request) {
  if (!backendBaseUrl) return NextResponse.json({ error: "PYTHON_API_BASE_URL not configured." }, { status: 500 });
  const url = new URL(request.url);
  const clientId = url.searchParams.get("clientId");
  const projectId = url.searchParams.get("projectId");
  if (!clientId) return NextResponse.json({ error: "clientId is required." }, { status: 400 });
  const params = new URLSearchParams({ clientId });
  if (projectId) params.set("projectId", projectId);
  const response = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/brand-profile?${params.toString()}`, { cache: "no-store" });
  if (!response.ok) return NextResponse.json({ error: "Brand profile fetch failed.", detail: await readError(response) }, { status: response.status });
  return NextResponse.json(await response.json());
}

export async function POST(request: Request) {
  if (!backendBaseUrl) return NextResponse.json({ error: "PYTHON_API_BASE_URL not configured." }, { status: 500 });
  const payload = await request.json();
  const response = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/brand-profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) return NextResponse.json({ error: "Brand profile save failed.", detail: await readError(response) }, { status: response.status });
  return NextResponse.json(await response.json());
}
