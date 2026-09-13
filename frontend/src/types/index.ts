export interface ParameterItem {
    name: string;
    type?: string;
    required?: boolean;
    description?: string;
    example?: string;
    default?: unknown;
}

export interface EndpointParameters {
    path?: ParameterItem[];
    query?: ParameterItem[];
    header?: ParameterItem[];
    cookie?: ParameterItem[];
}

export interface RequestBody {
    description?: string;
    required?: boolean;
    content_type?: string;
    schema?: Record<string, unknown>;
}

export interface AuthConfig {
    type: string;
    name?: string;
    location?: string;
    description?: string;
}

export interface Endpoint {
    path: string;
    method: string;
    summary?: string;
    description?: string;
    parameters?: EndpointParameters;
    request_body?: RequestBody;
    responses?: Record<string, unknown>;
}

export interface ApiSpecData {
    name: string;
    version: string;
    base_url?: string;
    endpoints: Endpoint[];
    authentication?: AuthConfig;
    source?: string;
    is_mock?: boolean;
    description?: string;
}

export interface Project {
    id: string;
    name: string;
    description?: string;
    url?: string;
    status?: 'ready' | 'generating' | 'failed';
    created_at?: string;
    spec?: ApiSpecData;
    sdk_code?: string;
    test_code?: string;
    sdk_id?: string;
    apiCallCount?: number;
}

export interface SpecVersionItem {
    id: string;
    project_id: string;
    version: number;
    spec_data: ApiSpecData;
    created_at: string;
}

export interface GeneratedSdkItem {
    id: string;
    api_spec_id: string;
    version: number;
    language: string;
    sdk_code: string;
    test_code?: string;
    created_at: string;
}

export interface SpecChange {
    type: string;
    description: string;
    path?: string;
    method?: string;
    parameter?: string;
    breaking: boolean;
}

export interface DiffResult {
    from_version: number;
    to_version: number;
    is_breaking: boolean;
    total_changes: number;
    breaking_changes_count: number;
    changes: SpecChange[];
    compared_at: string;
}

export interface PlaygroundExecuteRequest {
    base_url: string;
    path: string;
    method: string;
    params?: Record<string, string>;
    headers?: Record<string, string>;
    json_body?: unknown;
}

export interface PlaygroundExecuteResponse {
    status_code: number | null;
    response: unknown;
    error?: string;
}

export interface PlaygroundHistoryItem {
    id: string;
    project_id: string;
    method: string;
    path: string;
    base_url?: string;
    params?: Record<string, string>;
    request_headers?: Record<string, string>;
    request_body?: unknown;
    response_status: number | null;
    response_headers?: Record<string, string>;
    response_body?: unknown;
    execution_time_ms?: number;
    error_message?: string;
    created_at: string;
}

export interface GenerateResponse {
    name: string;
    version: string;
    spec: ApiSpecData;
    sdk_code: string;
    test_code?: string;
    is_mock: boolean;
    source?: string;
}

export type TabType = 'overview' | 'endpoints' | 'databases' | 'playground' | 'results' | 'tests' | 'changes';

export interface WorkspaceStats {
    total_projects: number;
    total_sdks: number;
    total_endpoints: number;
    total_api_calls: number;
}

