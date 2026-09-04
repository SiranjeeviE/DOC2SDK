import axios from 'axios';
import type {
    Project,
    SpecVersionItem,
    GeneratedSdkItem,
    DiffResult,
    SpecChange,
    PlaygroundExecuteRequest,
    PlaygroundExecuteResponse,
    PlaygroundHistoryItem,
    GenerateResponse,
    WorkspaceStats,
} from './types';

export type { DiffResult, SpecChange };

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 2 minutes (needed for large API processing)
    headers: {
        'Content-Type': 'application/json',
    },
});

// Attach Authorization header if an API key is stored
api.interceptors.request.use((config) => {
    const key = localStorage.getItem('doc2sdk_api_key');
    if (key && config.headers) {
        config.headers.Authorization = `Bearer ${key.trim()}`;
    }
    return config;
});

// Intercept 401 responses to alert UI that authentication is required
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            window.dispatchEvent(new CustomEvent('doc2sdk-auth-error', {
                detail: { message: error.response.data?.detail || 'Authentication required' }
            }));
        }
        return Promise.reject(error);
    }
);

export const authApi = {
    getStatus: async (): Promise<{ auth_enabled: boolean }> => {
        try {
            const response = await api.get<{ auth_enabled: boolean }>('/auth/status');
            return response.data;
        } catch {
            return { auth_enabled: false };
        }
    },
    verify: async (key: string): Promise<{ authenticated: boolean }> => {
        const response = await api.post<{ authenticated: boolean }>('/auth/verify', { api_key: key });
        return response.data;
    },
    getApiKey: (): string => {
        return localStorage.getItem('doc2sdk_api_key') || '';
    },
    setApiKey: (key: string): void => {
        if (key.trim()) {
            localStorage.setItem('doc2sdk_api_key', key.trim());
        } else {
            localStorage.removeItem('doc2sdk_api_key');
        }
    },
    clearApiKey: (): void => {
        localStorage.removeItem('doc2sdk_api_key');
    },
};

export const mvpApi = {
    generate: async (sourceUrl: string): Promise<GenerateResponse> => {
        const response = await api.post<GenerateResponse>('/generate', { source_url: sourceUrl });
        return response.data;
    },
    execute: async (data: PlaygroundExecuteRequest): Promise<PlaygroundExecuteResponse> => {
        const response = await api.post<PlaygroundExecuteResponse>('/playground/execute', data);
        return response.data;
    },
};

export const projectApi = {
    list: async (): Promise<Project[]> => {
        const response = await api.get<Project[]>('/projects');
        return response.data;
    },
    get: async (id: string): Promise<Project> => {
        const response = await api.get<Project>(`/projects/${id}`);
        return response.data;
    },
    create: async (name: string, url: string, description?: string): Promise<Project> => {
        const response = await api.post<Project>('/projects', { name, source_url: url, description });
        return response.data;
    },
    upload: async (file: File, name?: string, description?: string): Promise<Project> => {
        const formData = new FormData();
        formData.append('file', file);
        if (name) formData.append('name', name);
        if (description) formData.append('description', description);
        const response = await api.post<Project>('/projects/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },
    uploadSpec: async (id: string, file: File): Promise<SpecVersionItem> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post<SpecVersionItem>(`/projects/${id}/upload-spec`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },
    getSpecs: async (id: string): Promise<SpecVersionItem[]> => {
        const response = await api.get<SpecVersionItem[]>(`/projects/${id}/specs`);
        return response.data;
    },
    getSdks: async (id: string): Promise<GeneratedSdkItem[]> => {
        const response = await api.get<GeneratedSdkItem[]>(`/projects/${id}/sdks`);
        return response.data;
    },
    getDiff: async (id: string, fromVersion?: number, toVersion?: number): Promise<DiffResult> => {
        const params: Record<string, number> = {};
        if (fromVersion !== undefined) params.from_version = fromVersion;
        if (toVersion !== undefined) params.to_version = toVersion;
        const response = await api.get<DiffResult>(`/projects/${id}/diff`, { params });
        return response.data;
    },
    checkChanges: async (id: string): Promise<{ message: string; [key: string]: unknown }> => {
        const response = await api.post<{ message: string; [key: string]: unknown }>(`/projects/${id}/check-changes`);
        return response.data;
    },
    downloadTests: async (projectId: string, sdkId: string): Promise<Blob> => {
        const response = await api.get<Blob>(`/projects/${projectId}/sdk/${sdkId}/download-tests`, {
            responseType: 'blob'
        });
        return response.data;
    },
    rescrape: async (id: string, url: string): Promise<{ message: string }> => {
        const response = await api.post<{ message: string }>(`/projects/${id}/rescrape`, { source_url: url });
        return response.data;
    },
    regenerateSdk: async (id: string, language: string, specId?: string): Promise<GeneratedSdkItem> => {
        const response = await api.post<GeneratedSdkItem>(`/projects/${id}/regenerate-sdk`, { language, spec_id: specId });
        return response.data;
    },
    delete: async (id: string): Promise<void> => {
        await api.delete(`/projects/${id}`);
    },
    update: async (id: string, data: { name?: string; description?: string }): Promise<Project> => {
        const response = await api.put<Project>(`/projects/${id}`, data);
        return response.data;
    },
    patch: async (id: string, data: { name?: string; description?: string }): Promise<Project> => {
        const response = await api.patch<Project>(`/projects/${id}`, data);
        return response.data;
    }
};

export const playgroundApi = {
    run: async (projectId: string, data: PlaygroundExecuteRequest): Promise<PlaygroundExecuteResponse> => {
        const response = await api.post<PlaygroundExecuteResponse>(`/projects/${projectId}/playground/run`, data);
        return response.data;
    },
    history: async (projectId: string): Promise<PlaygroundHistoryItem[]> => {
        const response = await api.get<PlaygroundHistoryItem[]>(`/projects/${projectId}/playground/history`);
        return response.data;
    },
    replay: async (projectId: string, requestId: string): Promise<PlaygroundExecuteResponse> => {
        const response = await api.post<PlaygroundExecuteResponse>(`/projects/${projectId}/playground/history/${requestId}/replay`);
        return response.data;
    }
};

export const statsApi = {
    getOverview: async (): Promise<WorkspaceStats> => {
        const response = await api.get<WorkspaceStats>('/projects/stats/overview');
        return response.data;
    }
};

export default api;
