import { NextResponse } from "next/server";

export const runtime = "nodejs";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!backendBaseUrl) {
    return NextResponse.json({ error: "Python backend URL is not configured." }, { status: 500 });
  }

  const { id } = await params;
  const backendResponse = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/campaigns/${id}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" }
  });

  if (!backendResponse.ok) {
    return NextResponse.json({ error: `Campaign '${id}' not found.` }, { status: backendResponse.status });
  }

  return NextResponse.json(await backendResponse.json());
}
