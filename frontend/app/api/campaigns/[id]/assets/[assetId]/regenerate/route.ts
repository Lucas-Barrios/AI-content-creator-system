import { NextResponse } from "next/server";
import type { AssetRegenerateRequest } from "@/lib/types";

export const runtime = "nodejs";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string; assetId: string }> }
) {
  if (!backendBaseUrl) {
    return NextResponse.json({ error: "Python backend URL is not configured." }, { status: 500 });
  }

  const { id, assetId } = await params;
  let payload: AssetRegenerateRequest;
  try {
    payload = (await request.json()) as AssetRegenerateRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const backendResponse = await fetch(
    `${backendBaseUrl.replace(/\/$/, "")}/campaigns/${id}/assets/${assetId}/regenerate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }
  );

  if (!backendResponse.ok) {
    const raw = await backendResponse.text();
    return NextResponse.json({ error: "Asset regeneration failed.", detail: raw }, { status: backendResponse.status });
  }

  return NextResponse.json(await backendResponse.json());
}
