import { NextResponse } from "next/server";

export const runtime = "nodejs";

const backendBaseUrl = process.env.PYTHON_API_BASE_URL;

export async function GET() {
  if (!backendBaseUrl) {
    return NextResponse.json(
      { error: "Python backend URL is not configured.", detail: "Set PYTHON_API_BASE_URL in frontend/.env.local." },
      { status: 500 }
    );
  }

  const response = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/health`, { cache: "no-store" });
  if (!response.ok) {
    return NextResponse.json({ error: "Backend health check failed." }, { status: response.status });
  }
  return NextResponse.json(await response.json());
}
