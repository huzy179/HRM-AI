const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API Error: ${response.status}`);
  }

  return response;
}

export const api = {
  get: (path: string, options?: RequestInit) => request(path, { ...options, method: "GET" }),
  post: (path: string, body?: any, options?: RequestInit) =>
    request(path, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: (path: string, body?: any, options?: RequestInit) =>
    request(path, {
      ...options,
      method: "PUT",
      body: JSON.stringify(body),
    }),
  delete: (path: string, options?: RequestInit) => request(path, { ...options, method: "DELETE" }),

  // Helper for reading streaming responses
  async readStream(
    path: string,
    body: any,
    onChunk: (text: string) => void,
    onCitations: (citations: any[]) => void
  ) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `API Error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body reader");

    const decoder = new TextDecoder();
    let citationsRead = false;
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!citationsRead && line.startsWith("CITATIONS: ")) {
          try {
            const citations = JSON.parse(line.slice(11));
            onCitations(citations);
          } catch (e) {
            console.error("Failed to parse citations:", e);
          }
          citationsRead = true;
        } else {
          onChunk(line);
        }
      }
    }
    
    if (buffer) {
      onChunk(buffer);
    }
  },
};
