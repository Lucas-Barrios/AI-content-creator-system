export function backendHeaders(extra?: HeadersInit): HeadersInit {
  const apiKey = process.env.PYTHON_API_KEY;
  return {
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
    ...(extra ?? {})
  };
}
