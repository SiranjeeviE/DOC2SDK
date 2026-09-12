import { useEffect } from 'react';
import { useLocation, useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import type { TabType } from '../types';
import { useWorkspace } from '../context/WorkspaceContext';
import Layout from '../components/Layout';
import OverviewView from '../components/views/OverviewView';
import EndpointsView from '../components/views/EndpointsView';
import DatabasesView from '../components/views/DatabasesView';
import PlaygroundView from '../components/views/PlaygroundView';
import ResultsView from '../components/views/ResultsView';
import TestsView from '../components/views/TestsView';
import ChangesView from '../components/views/ChangesView';

import CreateProjectModal from '../components/modals/CreateProjectModal';
import EditProjectModal from '../components/modals/EditProjectModal';
import ApiKeyModal from '../components/modals/ApiKeyModal';
import UploadSpecModal from '../components/modals/UploadSpecModal';
import ConfirmDeleteModal from '../components/modals/ConfirmDeleteModal';

interface WorkspaceProps {
    tab?: TabType;
}

export default function Workspace({ tab: propTab }: WorkspaceProps) {
    const location = useLocation();
    const params = useParams<{ projectId?: string; tab?: string }>();
    const [searchParams] = useSearchParams();
    const {
        projects,
        selectedProject,
        selectProject,
        isDeleteModalOpen,
        projectToDelete,
        closeDeleteModal,
        confirmDeleteProject,
        isDeleting,
    } = useWorkspace();

    // Global keyboard shortcut: Cmd/Ctrl + K to focus search
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('global-search-input') as HTMLInputElement | null;
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    // Determine current tab from props, route params, or pathname
    const pathSegment = location.pathname.slice(1).split('/')[0] as TabType;
    const validTabs: TabType[] = ['overview', 'endpoints', 'databases', 'playground', 'results', 'tests', 'changes'];
    const activeTab: TabType = propTab || (
        params.tab && validTabs.includes(params.tab as TabType)
            ? (params.tab as TabType)
            : validTabs.includes(pathSegment)
                ? pathSegment
                : 'overview'
    );

    // Support deep-linking project by URL path parameter or search param
    const targetProjectId = params.projectId || searchParams.get('project');
    useEffect(() => {
        if (targetProjectId && (!selectedProject || selectedProject.id !== targetProjectId)) {
            const match = projects.find((p) => p.id === targetProjectId);
            if (match) {
                selectProject(match);
            }
        }
    }, [targetProjectId, projects, selectedProject, selectProject]);

    const navigate = useNavigate();
    const handleNavigateTab = (tab: string) => {
        navigate(tab === 'overview' ? '/' : `/${tab}`);
    };

    return (
        <>
            <Layout activeTab={activeTab}>
                <AnimatePresence mode="wait">
                    {activeTab === 'overview' && <OverviewView key="overview" onNavigateTab={handleNavigateTab} />}
                    {activeTab === 'endpoints' && <EndpointsView key="endpoints" onNavigateTab={handleNavigateTab} />}
                    {activeTab === 'databases' && <DatabasesView key="databases" onNavigateTab={handleNavigateTab} />}
                    {activeTab === 'playground' && <PlaygroundView key="playground" onNavigateTab={handleNavigateTab} />}
                    {activeTab === 'results' && <ResultsView key="results" />}
                    {activeTab === 'tests' && <TestsView key="tests" />}
                    {activeTab === 'changes' && <ChangesView key="changes" />}
                </AnimatePresence>
            </Layout>

            {/* Modals */}
            <CreateProjectModal />
            <EditProjectModal />
            <ApiKeyModal />
            <UploadSpecModal />
            <ConfirmDeleteModal
                isOpen={isDeleteModalOpen}
                projectName={projectToDelete?.name || ''}
                onClose={closeDeleteModal}
                onConfirm={confirmDeleteProject}
                loading={isDeleting}
            />
        </>
    );
}
