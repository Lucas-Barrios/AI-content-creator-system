import { NextResponse } from "next/server";

export const runtime = "nodejs";

const backend = process.env.PYTHON_API_BASE_URL;

export async function POST(request: Request) {
  if (!backend)
    return NextResponse.json({ error: "PYTHON_API_BASE_URL not configured." }, { status: 500 });

  const formData = await request.formData();
  const res = await fetch(`${backend.replace(/\/$/, "")}/repurpose/extract-file`, {
    method: "POST",
    body: formData
  });

  if (!res.ok) {
    const raw = await res.text();
    return NextResponse.json({ error: "File extraction failed.", detail: raw }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
