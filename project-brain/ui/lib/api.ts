const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

const buildUrl = (path: string) => `${API_BASE_URL}${path}`;

type ApiResponse<T> = {
  data: T;
  status: number;
};

async function request<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const response = await fetch(buildUrl(path), {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }

  const data = (await response.json()) as T;
  return { data, status: response.status };
}

export const documentAPI = {
  list: (skip = 0, limit = 10) =>
    request<{ documents: any[]; total: number; skip: number; limit: number }>(
      `/documents?skip=${skip}&limit=${limit}`
    ),
  search: (payload: { query: string; limit?: number; offset?: number }) =>
    request<{ results: any[]; total: number; limit: number; offset: number }>(
      '/search',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    ),
  ask: (payload: { question: string; max_context_chunks?: number }) =>
    request<{ answer: string; sources?: any[]; status?: string }>(
      '/ask',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    ),
};

export const reportAPI = {
  list: () =>
    request<{ reports: any[] }>('/state/reports', {
      method: 'GET',
    }),
};

export const registryAPI = {
  listEntities: (projectKey: string) =>
    request<{ entities: any[] }>(`/registry/entities?project_key=${projectKey}`),
};
