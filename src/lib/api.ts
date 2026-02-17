import type {
  GraphData,
  NodeDetail,
  PathResult,
} from "@/types/graph";
import type {
  ApiResponse,
  SearchResult,
  SearchResponse,
  AgencyConcentration,
  ContractorProfile,
  GraphStats,
  ChatRequest,
} from "@/types/api";
import { API_BASE } from "./constants";

class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchOnce<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { code: "UNKNOWN", message: response.statusText },
    }));
    throw new ApiError(error.error?.code || "UNKNOWN", error.error?.message || "Request failed");
  }

  const data = await response.json();
  return data.data || data;
}

const RETRY_DELAYS = [0, 8_000, 15_000, 25_000];

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  let lastError: unknown;

  for (let attempt = 0; attempt < RETRY_DELAYS.length; attempt++) {
    if (attempt > 0) {
      await new Promise((r) => setTimeout(r, RETRY_DELAYS[attempt]));
    }
    try {
      return await fetchOnce<T>(url, options);
    } catch (error) {
      lastError = error;
      // Don't retry client errors (4xx)
      if (error instanceof ApiError && error.code !== "NETWORK_ERROR") {
        throw error;
      }
    }
  }

  if (lastError instanceof ApiError) throw lastError;
  throw new ApiError("NETWORK_ERROR", lastError instanceof Error ? lastError.message : "Network request failed");
}

export async function fetchGraph(nodeId?: string, depth = 1): Promise<GraphData> {
  if (!nodeId) {
    return fetchApi<GraphData>("/graph/overview");
  }
  const params = new URLSearchParams({
    center: nodeId,
    depth: depth.toString(),
  });
  return fetchApi<GraphData>(`/graph/subgraph?${params}`);
}

export async function searchEntities(query: string, type?: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (type) {
    params.set("type", type);
  }

  const results = await fetchApi<SearchResult[]>(`/graph/search?${params}`);
  return { results: Array.isArray(results) ? results : [], total: Array.isArray(results) ? results.length : 0 };
}

export async function getNodeDetail(nodeId: string): Promise<NodeDetail> {
  return fetchApi<NodeDetail>(`/graph/node/${encodeURIComponent(nodeId)}`);
}

export async function getPath(fromId: string, toId: string): Promise<PathResult> {
  const params = new URLSearchParams({
    from: fromId,
    to: toId,
  });

  return fetchApi<PathResult>(`/graph/path?${params}`);
}

export async function getAgencyConcentration(agencyId: string): Promise<AgencyConcentration> {
  return fetchApi<AgencyConcentration>(`/analytics/agency/${encodeURIComponent(agencyId)}/concentration`);
}

export async function getContractorProfile(contractorId: string): Promise<ContractorProfile> {
  return fetchApi<ContractorProfile>(`/analytics/contractor/${encodeURIComponent(contractorId)}/profile`);
}

export async function getRedFlags(severity?: string): Promise<GraphData> {
  const params = new URLSearchParams();
  if (severity) {
    params.set("severity", severity);
  }

  return fetchApi<GraphData>(`/analytics/red-flags?${params}`);
}

export async function getStats(): Promise<GraphStats> {
  return fetchApi<GraphStats>("/analytics/stats");
}

export function streamChat(
  message: string,
  context?: ChatRequest["context"] & { history?: { role: string; content: string }[] },
  apiKey?: string,
): ReadableStream<string> {
  const url = `${API_BASE}/chat`;
  const { history, ...ctx } = context || {};
  const body = {
    message,
    context: Object.keys(ctx).length ? ctx : undefined,
    history,
  };

  const stream = new ReadableStream<string>({
    async start(controller) {
      try {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (apiKey) {
          headers["x-api-key"] = apiKey;
        }

        const response = await fetch(url, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
        });

        if (!response.ok) {
          throw new Error(`Chat request failed: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") {
                controller.close();
                return;
              }
              try {
                const parsed = JSON.parse(data);
                controller.enqueue(parsed);
              } catch {
                // Skip invalid JSON
              }
            }
          }
        }

        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return stream;
}
