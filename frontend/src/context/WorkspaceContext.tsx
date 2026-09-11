import { createContext, useContext, useState, useEffect, useMemo, useCallback, type ReactNode } from 'react';
import type {
    Project,
    Endpoint,
    DiffResult,
    SpecVersionItem,
    PlaygroundExecuteResponse,
    WorkspaceStats,
} from '../types';
import { projectApi, playgroundApi, authApi, statsApi } from '../api';
import { SafeStorage } from '../utils/storage';
import { useToast } from './ToastContext';

interface WorkspaceContextType {
    // Projects
    projects: Project[];
    selectedProject: Project | null;
    selectProject: (p: Project) => Promise<void>;
    createProject: (name: string, url: string) => Promise<Project>;
    uploadProject: (file: File, name?: string) => Promise<Project>;
    updateProject: (id: string, name: string, description?: string) => Promise<void>;
    deleteProject: (id: string) => Promise<void>;
    loading: boolean;
    error: string | null;
    setError: (err: string | null) => void;

    // Workspace Real Database Stats
    workspaceStats: WorkspaceStats | null;
    statsLoading: boolean;
    fetchStats: () => Promise<void>;

    // Delete Modal
    isDeleteModalOpen: boolean;
    projectToDelete: Project | null;
    isDeleting: boolean;
    openDeleteModal: (p: Project) => void;
    closeDeleteModal: () => void;
    confirmDeleteProject: () => Promise<void>;

    // Search
    searchQuery: string;
    setSearchQuery: (q: string) => void;
    filteredProjects: Project[];
    filteredEndpoints: Endpoint[];

    // Metrics
    apiCalls: number;
    incrementApiCalls: () => void;

    // Modals
    isCreateModalOpen: boolean;
    setIsCreateModalOpen: (open: boolean) => void;
    isEditModalOpen: boolean;
    setIsEditModalOpen: (open: boolean) => void;
    editingProject: Project | null;
    openEditModal: (p: Project) => void;
    isApiKeyModalOpen: boolean;
    setIsApiKeyModalOpen: (open: boolean) => void;
    isUploadSpecModalOpen: boolean;
    setIsUploadSpecModalOpen: (open: boolean) => void;

    // Playground
    selectedEndpoint: Endpoint | null;
    setSelectedEndpoint: (ep: Endpoint | null) => void;
    pParams: Record<string, string>;
    setPParams: React.Dispatch<React.SetStateAction<Record<string, string>>>;
    pBody: string;
    setPBody: (body: string) => void;
    pResponse: PlaygroundExecuteResponse | null;
    setPResponse: (res: PlaygroundExecuteResponse | null) => void;
    pLoading: boolean;
    executePlayground: () => Promise<void>;

    // API Change Monitor
    diffResult: DiffResult | null;
    diffLoading: boolean;
    diffError: string | null;
    specVersions: SpecVersionItem[];
    checkingChanges: boolean;
    checkStatus: string | null;
    checkChanges: () => Promise<void>;
    uploadNewSpec: (file: File) => Promise<void>;
    fetchDiffAndVersions: (projectId: string) => Promise<void>;

    // Auth
    isAuthEnabled: boolean;
    hasApiKey: boolean;

    // File helpers
    downloadFile: (content: string, filename: string, mimeType: string) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
    const toast = useToast();
    const [projects, setProjects] = useState<Project[]>(() => {
        return SafeStorage.getItem('ag_projects', []);
    });
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [apiCalls, setApiCalls] = useState<number>(() => {
        return SafeStorage.getItem('ag_api_calls', 0);
    });

    // Real Workspace Statistics
    const [workspaceStats, setWorkspaceStats] = useState<WorkspaceStats | null>(null);
    const [statsLoading, setStatsLoading] = useState(false);

    // Delete Confirmation Modal
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    // Modals
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editingProject, setEditingProject] = useState<Project | null>(null);
    const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState(false);
    const [isUploadSpecModalOpen, setIsUploadSpecModalOpen] = useState(false);

    // Playground
    const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint | null>(null);
    const [pParams, setPParams] = useState<Record<string, string>>({});
    const [pBody, setPBody] = useState('');
    const [pResponse, setPResponse] = useState<PlaygroundExecuteResponse | null>(null);
    const [pLoading, setPLoading] = useState(false);

    // API Change Monitor
    const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
    const [diffLoading, setDiffLoading] = useState(false);
    const [diffError, setDiffError] = useState<string | null>(null);
    const [specVersions, setSpecVersions] = useState<SpecVersionItem[]>([]);
    const [checkingChanges, setCheckingChanges] = useState(false);
    const [checkStatus, setCheckStatus] = useState<string | null>(null);

    // Auth
    const [isAuthEnabled, setIsAuthEnabled] = useState(false);
    const hasApiKey = Boolean(authApi.getApiKey());

    const fetchStats = useCallback(async () => {
        setStatsLoading(true);
        try {
            const data = await statsApi.getOverview();
            setWorkspaceStats(data);
        } catch (err) {
            console.error('Failed to fetch workspace stats', err);
        } finally {
            setStatsLoading(false);
        }
    }, []);

    // Fetch initial projects and stats
    useEffect(() => {
        let isMounted = true;
        projectApi.list().then((data) => {
            if (!isMounted) return;
            setProjects((prev) => {
                const merged = data.map((serverProj) => {
                    const localProj = prev.find((p) => p.id === serverProj.id);
                    return { ...localProj, ...serverProj };
                });
                merged.sort((a, b) => new Date(b.created_at || b.id).getTime() - new Date(a.created_at || a.id).getTime());
                SafeStorage.setItem('ag_projects', merged);
                return merged;
            });
        }).catch((err) => console.error('Failed to fetch projects', err));

        fetchStats();

        authApi.getStatus().then((status) => {
            if (isMounted) setIsAuthEnabled(Boolean(status?.auth_enabled));
        }).catch(() => {});

        const handleAuthError = () => {
            setIsApiKeyModalOpen(true);
            setError('Authentication required: Please configure your API key.');
            toast.error('Authentication required: Please configure your API key.');
        };
        window.addEventListener('doc2sdk-auth-error', handleAuthError);

        return () => {
            isMounted = false;
            window.removeEventListener('doc2sdk-auth-error', handleAuthError);
        };
    }, [fetchStats]);

    const incrementApiCalls = () => {
        const next = apiCalls + 1;
        setApiCalls(next);
        SafeStorage.setItem('ag_api_calls', next);
    };

    const downloadFile = (content: string, filename: string, mimeType: string) => {
        const blob = new Blob([content], { type: mimeType });
        const fileUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = fileUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(fileUrl);
    };

    const pollProjectData = (projectId: string) => {
        const maxAttempts = 30;
        let attempts = 0;

        const poll = setInterval(async () => {
            attempts++;
            try {
                const specs = await projectApi.getSpecs(projectId);
                if (specs && specs.length > 0) {
                    clearInterval(poll);
                    const sdks = await projectApi.getSdks(projectId);
                    const specData = specs[0].spec_data;
                    const latestSdk = sdks.length > 0 ? sdks[sdks.length - 1] : null;
                    const sdkCode = latestSdk ? latestSdk.sdk_code : '';
                    const testCode = latestSdk ? latestSdk.test_code : '';
                    const sdkId = latestSdk ? latestSdk.id : '';

                    setProjects((prev) => {
                        const updated = prev.map((p) => (p.id === projectId ? {
                            ...p, spec: specData, sdk_code: sdkCode, test_code: testCode, sdk_id: sdkId, status: 'ready' as const
                        } : p));
                        SafeStorage.setItem('ag_projects', updated);
                        return updated;
                    });

                    setSelectedProject((prev) => {
                        if (prev && prev.id === projectId) {
                            const newRes: Project = { ...prev, spec: specData, sdk_code: sdkCode, test_code: testCode, sdk_id: sdkId, status: 'ready' };
                            if (specData.endpoints && specData.endpoints.length > 0) {
                                setSelectedEndpoint(specData.endpoints[0]);
                            }
                            return newRes;
                        }
                        return prev;
                    });
                    fetchStats();
                }
            } catch {
                // Ignore errors during polling
            }
            if (attempts >= maxAttempts) clearInterval(poll);
        }, 2000);
    };

    const selectProject = async (p: Project) => {
        setSelectedProject(p);
        if (p.spec?.endpoints && p.spec.endpoints.length > 0) {
            setSelectedEndpoint(p.spec.endpoints[0]);
        }

        if (p.status === 'generating') {
            pollProjectData(p.id);
            return;
        }

        try {
            const specs = await projectApi.getSpecs(p.id);
            const sdks = await projectApi.getSdks(p.id);

            const specData = specs && specs.length > 0 ? specs[0].spec_data : undefined;
            const latestSdk = sdks && sdks.length > 0 ? sdks[sdks.length - 1] : null;

            const updatedProject: Project = {
                ...p,
                spec: specData,
                sdk_code: latestSdk ? latestSdk.sdk_code : (p.sdk_code || ''),
                test_code: latestSdk ? latestSdk.test_code : (p.test_code || ''),
                sdk_id: latestSdk ? latestSdk.id : (p.sdk_id || ''),
                status: 'ready',
            };

            setSelectedProject(updatedProject);
            setProjects((prev) => {
                const next = prev.map((item) => (item.id === p.id ? updatedProject : item));
                SafeStorage.setItem('ag_projects', next);
                return next;
            });

            if (specData?.endpoints && specData.endpoints.length > 0) {
                setSelectedEndpoint(specData.endpoints[0]);
            }
        } catch {
            // Use existing project data if network request fails
        }
    };

    const createProject = async (name: string, url: string): Promise<Project> => {
        setLoading(true);
        setError(null);
        try {
            const data = await projectApi.create(name, url);
            const newProject: Project = {
                ...data,
                url,
                status: 'generating',
                created_at: new Date().toISOString(),
            };

            const updated = [newProject, ...projects];
            SafeStorage.setItem('ag_projects', updated);
            setProjects(updated);
            setSelectedProject(newProject);
            pollProjectData(data.id);
            fetchStats();
            toast.success(`Project "${name}" created successfully`);
            return newProject;
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            const msg = errorObj.response?.data?.detail || errorObj.message || 'Failed to create project';
            setError(msg);
            toast.error(msg);
            throw new Error(msg);
        } finally {
            setLoading(false);
        }
    };

    const uploadProject = async (file: File, name?: string): Promise<Project> => {
        setLoading(true);
        setError(null);
        try {
            const data = await projectApi.upload(file, name);
            const specs = await projectApi.getSpecs(data.id);
            const sdks = await projectApi.getSdks(data.id);
            const specData = specs && specs.length > 0 ? specs[0].spec_data : undefined;
            const latestSdk = sdks && sdks.length > 0 ? sdks[sdks.length - 1] : null;

            const newProject: Project = {
                ...data,
                spec: specData,
                sdk_code: latestSdk ? latestSdk.sdk_code : '',
                test_code: latestSdk ? latestSdk.test_code : '',
                sdk_id: latestSdk ? latestSdk.id : '',
                status: 'ready',
            };

            const updated = [newProject, ...projects];
            SafeStorage.setItem('ag_projects', updated);
            setProjects(updated);
            setSelectedProject(newProject);
            if (specData?.endpoints && specData.endpoints.length > 0) {
                setSelectedEndpoint(specData.endpoints[0]);
            }
            fetchStats();
            toast.success(`Project "${newProject.name}" uploaded successfully`);
            return newProject;
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            const msg = errorObj.response?.data?.detail || errorObj.message || 'Failed to upload project';
            toast.error(msg);
            throw new Error(msg);
        } finally {
            setLoading(false);
        }
    };

    const updateProject = async (id: string, name: string, description?: string) => {
        try {
            const updated = await projectApi.update(id, { name, description });
            const updatedProjects = projects.map((p) => (String(p.id) === String(id) ? {
                ...p,
                name: updated.name,
                description: updated.description,
                url: updated.description || p.url,
            } : p));
            setProjects(updatedProjects);
            SafeStorage.setItem('ag_projects', updatedProjects);
            if (selectedProject && String(selectedProject.id) === String(id)) {
                setSelectedProject({
                    ...selectedProject,
                    name: updated.name,
                    description: updated.description,
                    url: updated.description || selectedProject.url,
                });
            }
            toast.success('Project updated successfully');
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            const msg = errorObj.response?.data?.detail || errorObj.message || 'Failed to update project';
            toast.error(msg);
            throw new Error(msg);
        }
    };

    const deleteProject = async (id: string) => {
        await projectApi.delete(id);
        const updatedProjects = projects.filter((p) => String(p.id) !== String(id));
        setProjects(updatedProjects);
        SafeStorage.setItem('ag_projects', updatedProjects);
        if (selectedProject && String(selectedProject.id) === String(id)) {
            setSelectedProject(null);
        }
        fetchStats();
    };

    const openDeleteModal = (p: Project) => {
        setProjectToDelete(p);
        setIsDeleteModalOpen(true);
    };

    const closeDeleteModal = () => {
        setIsDeleteModalOpen(false);
        setProjectToDelete(null);
    };

    const confirmDeleteProject = async () => {
        if (!projectToDelete) return;
        const targetName = projectToDelete.name;
        setIsDeleting(true);
        try {
            await deleteProject(projectToDelete.id);
            toast.success(`Project "${targetName}" deleted successfully`);
            closeDeleteModal();
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            const msg = errorObj.response?.data?.detail || errorObj.message || 'Failed to delete project';
            setError(msg);
            toast.error(msg);
        } finally {
            setIsDeleting(false);
        }
    };

    const openEditModal = (p: Project) => {
        setEditingProject(p);
        setIsEditModalOpen(true);
    };

    const executePlayground = async () => {
        if (!selectedProject || !selectedEndpoint) return;
        setPLoading(true);
        try {
            let path = selectedEndpoint.path;
            const pathParams = selectedEndpoint.parameters?.path || [];
            pathParams.forEach((tp) => {
                if (pParams[tp.name]) {
                    path = path.replace(`{${tp.name}}`, encodeURIComponent(pParams[tp.name]));
                }
            });

            let parsedBody: unknown = undefined;
            if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method) && pBody) {
                try {
                    parsedBody = JSON.parse(pBody);
                } catch {
                    parsedBody = pBody;
                }
            }

            const response = await playgroundApi.run(selectedProject.id, {
                base_url: selectedProject.spec?.base_url || 'https://api.example.com',
                path,
                method: selectedEndpoint.method,
                params: pParams,
                json_body: parsedBody,
            });

            setPResponse(response);
            incrementApiCalls();
            fetchStats();
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            setPResponse({
                status_code: 400,
                response: null,
                error: errorObj.response?.data?.detail || errorObj.message || 'Execution failed',
            });
        } finally {
            setPLoading(false);
        }
    };

    const fetchDiffAndVersions = async (projectId: string) => {
        setDiffLoading(true);
        setDiffError(null);
        try {
            const specs = await projectApi.getSpecs(projectId);
            setSpecVersions(specs || []);
            if (specs && specs.length >= 2) {
                const diff = await projectApi.getDiff(projectId);
                setDiffResult(diff);
            } else {
                setDiffResult(null);
            }
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } } };
            setDiffError(errorObj.response?.data?.detail || 'Could not fetch API specification diff');
        } finally {
            setDiffLoading(false);
        }
    };

    const checkChanges = async () => {
        if (!selectedProject?.id) return;
        setCheckingChanges(true);
        setCheckStatus(null);
        try {
            const res = await projectApi.checkChanges(selectedProject.id);
            setCheckStatus(res.message || 'Change check completed.');
            await fetchDiffAndVersions(selectedProject.id);
            await selectProject(selectedProject);
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } } };
            setCheckStatus(errorObj.response?.data?.detail || 'Failed to check for changes.');
        } finally {
            setCheckingChanges(false);
        }
    };

    const uploadNewSpec = async (file: File) => {
        if (!selectedProject?.id) return;
        try {
            await projectApi.uploadSpec(selectedProject.id, file);
            await fetchDiffAndVersions(selectedProject.id);
            await selectProject(selectedProject);
            fetchStats();
            toast.success('New API specification uploaded successfully');
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            const msg = errorObj.response?.data?.detail || errorObj.message || 'Failed to upload specification';
            toast.error(msg);
            throw new Error(msg);
        }
    };

    const filteredProjects = useMemo(() => {
        if (!searchQuery.trim()) return projects;
        const q = searchQuery.toLowerCase();
        return projects.filter((p) => (
            (p.name && p.name.toLowerCase().includes(q)) ||
            (p.description && p.description.toLowerCase().includes(q)) ||
            (p.url && p.url.toLowerCase().includes(q))
        ));
    }, [projects, searchQuery]);

    const allEndpoints = selectedProject?.spec?.endpoints || [];
    const filteredEndpoints = useMemo(() => {
        if (!searchQuery.trim()) return allEndpoints;
        const q = searchQuery.toLowerCase();
        return allEndpoints.filter((ep) => (
            (ep.path && ep.path.toLowerCase().includes(q)) ||
            (ep.method && ep.method.toLowerCase().includes(q)) ||
            (ep.summary && ep.summary.toLowerCase().includes(q)) ||
            (ep.description && ep.description.toLowerCase().includes(q))
        ));
    }, [allEndpoints, searchQuery]);

    return (
        <WorkspaceContext.Provider
            value={{
                projects,
                selectedProject,
                selectProject,
                createProject,
                uploadProject,
                updateProject,
                deleteProject,
                loading,
                error,
                setError,
                workspaceStats,
                statsLoading,
                fetchStats,
                isDeleteModalOpen,
                projectToDelete,
                isDeleting,
                openDeleteModal,
                closeDeleteModal,
                confirmDeleteProject,
                searchQuery,
                setSearchQuery,
                filteredProjects,
                filteredEndpoints,
                apiCalls,
                incrementApiCalls,
                isCreateModalOpen,
                setIsCreateModalOpen,
                isEditModalOpen,
                setIsEditModalOpen,
                editingProject,
                openEditModal,
                isApiKeyModalOpen,
                setIsApiKeyModalOpen,
                isUploadSpecModalOpen,
                setIsUploadSpecModalOpen,
                selectedEndpoint,
                setSelectedEndpoint,
                pParams,
                setPParams,
                pBody,
                setPBody,
                pResponse,
                setPResponse,
                pLoading,
                executePlayground,
                diffResult,
                diffLoading,
                diffError,
                specVersions,
                checkingChanges,
                checkStatus,
                checkChanges,
                uploadNewSpec,
                fetchDiffAndVersions,
                isAuthEnabled,
                hasApiKey,
                downloadFile,
            }}
        >
            {children}
        </WorkspaceContext.Provider>
    );
}

export function useWorkspace() {
    const context = useContext(WorkspaceContext);
    if (!context) {
        throw new Error('useWorkspace must be used within a WorkspaceProvider');
    }
    return context;
}
