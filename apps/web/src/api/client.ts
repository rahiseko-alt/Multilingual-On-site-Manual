const API_BASE = '/api';

export function getAuthToken(): string | null {
  return localStorage.getItem('token');
}

export function setAuthToken(token: string) {
  localStorage.setItem('token', token);
}

export function clearAuthToken() {
  localStorage.removeItem('token');
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || 'Request failed');
  }

  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user_id: string; tenant_id: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  getMe: () => request<{ id: string; email: string; full_name?: string }>('/auth/me'),

  getProjects: () => request<any[]>('/projects'),
  getProject: (id: string) => request<any>(`/projects/${id}`),
  createProject: (data: { title: string; source_language: string; target_languages: string }) =>
    request<any>('/projects', { method: 'POST', body: JSON.stringify(data) }),

  uploadVideo: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<any>(`/projects/${projectId}/video`, {
      method: 'POST',
      body: formData,
    });
  },

  startProcessing: (projectId: string) =>
    request<{ job_id: string; status: string; progress: number }>(`/projects/${projectId}/process`, {
      method: 'POST',
    }),
  getJob: (jobId: string) =>
    request<{ job_id: string; status: string; progress: number; current_stage?: string; error?: string }>(
      `/jobs/${jobId}`
    ),

  getManual: (projectId: string) => request<any>(`/projects/${projectId}/manual`),
  updateManual: (projectId: string, data: any) =>
    request<any>(`/projects/${projectId}/manual`, {
      method: 'PATCH',
      body: JSON.stringify({ data }),
    }),

  getTranslation: (projectId: string, lang: string) =>
    request<any>(`/projects/${projectId}/translations/${lang}`),
  updateTranslation: (projectId: string, lang: string, data: any) =>
    request<any>(`/projects/${projectId}/translations/${lang}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  createExport: (projectId: string, format: string, language: string) =>
    request<{ export_id: string; download_url: string }>(`/projects/${projectId}/exports`, {
      method: 'POST',
      body: JSON.stringify({ format, language }),
    }),
};
