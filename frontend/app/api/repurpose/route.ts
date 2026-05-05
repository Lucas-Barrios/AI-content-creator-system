import { NextResponse } from "next/server";
import type { RepurposeRequest, RepurposeResult } from "@/lib/types";

export const runtime = "nodejs";

const backend = process.env.PYTHON_API_BASE_URL;

async function readError(res: Response): Promise<string> {
  const raw = await res.text();
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return typeof parsed.detail === "string"
      ? parsed.detail
      : typeof parsed.error === "string"
        ? parsed.error
        : raw;
  } catch {
    return raw || `Backend returned status ${res.status}.`;
  }
}

export async function POST(request: Request) {
  if (!backend)
    return NextResponse.json({ error: "PYTHON_API_BASE_URL not configured." }, { status: 500 });

  let payload: RepurposeRequest;
  try {
    payload = (await request.json()) as RepurposeRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  if (!payload.sourceText?.trim())
    return NextResponse.json({ error: "sourceText is required." }, { status: 400 });
  if (!payload.targetFormats?.length)
    return NextResponse.json({ error: "Select at least one format." }, { status: 400 });

  const res = await fetch(`${backend.replace(/\/$/, "")}/repurpose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok)
    return NextResponse.json({ error: "Repurposing failed.", detail: await readError(res) }, { status: res.status });

  return NextResponse.json((await res.json()) as RepurposeResult);
}
