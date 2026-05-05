import { NextResponse } from "next/server";
import type { CampaignRequest, CampaignResult } from "@/lib/types";

export const runtime = "nodejs";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

async function readError(response: Response): Promise<string> {
  const raw = await response.text();
  if (!raw) return `Backend returned status ${response.status}.`;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (typeof parsed.detail === "string") return parsed.detail;
    if (typeof parsed.error === "string") return parsed.error;
  } catch {
    return raw;
  }
  return raw;
}

export async function POST(request: Request) {
  if (!backendBaseUrl) {
    return NextResponse.json(
      { error: "Python backend URL is not configured.", detail: "Set PYTHON_API_BASE_URL in frontend/.env.local." },
      { status: 500 }
    );
  }

  let payload: CampaignRequest;
  try {
    payload = (await request.json()) as CampaignRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  if (!payload.goal?.trim()) return NextResponse.json({ error: "Campaign goal is required." }, { status: 400 });
  if (!payload.channels?.length) return NextResponse.json({ error: "At least one channel must be selected." }, { status: 400 });

  const backendResponse = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/campaigns/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!backendResponse.ok) {
    const detail = await readError(backendResponse);
    return NextResponse.json({ error: "Campaign generation failed.", detail }, { status: backendResponse.status });
  }

  const result = (await backendResponse.json()) as CampaignResult;
  return NextResponse.json(result);
}
