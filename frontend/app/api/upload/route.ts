import { NextResponse } from "next/server";
import { backendHeaders } from "@/lib/server/backend";
import type { UploadedFile } from "@/lib/types";

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
        detail: "Set PYTHON_API_BASE_URL before enabling uploads."
      },
      { status: 500 }
    );
  }

  const formData = await request.formData();
  const files = formData.getAll("files").filter((item): item is File => item instanceof File);

  if (!files.length) {
    return NextResponse.json([]);
  }

  const backendForm = new FormData();
  files.forEach((file) => backendForm.append("files", file, file.name));

  const backendResponse = await fetch(`${backendBaseUrl.replace(/\/$/, "")}/upload`, {
    method: "POST",
    headers: backendHeaders(),
    body: backendForm
  });

  if (!backendResponse.ok) {
    return NextResponse.json(
      { error: "File upload failed.", detail: await readBackendError(backendResponse) },
      { status: backendResponse.status }
    );
  }

  const body = (await backendResponse.json()) as unknown;
  if (Array.isArray(body)) {
    return NextResponse.json(body as UploadedFile[]);
  }

  const record = body as Record<string, unknown>;
  return NextResponse.json((record.files ?? []) as UploadedFile[]);
}
