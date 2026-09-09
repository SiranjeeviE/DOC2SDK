import { useState, type FormEvent } from 'react';
import { motion } from 'framer-motion';
import { Box, Globe, Code, Zap, Cpu, Pencil, Trash2, Loader, Plus, Search, RefreshCw } from 'lucide-react';
import GlassCard from '../GlassCard';
import EmptyState from '../common/EmptyState';
import { useWorkspace } from '../../context/WorkspaceContext';

interface OverviewViewProps {
    onNavigateTab: (tab: string) => void;
}

export default function OverviewView({ onNavigateTab }: OverviewViewProps) {
    const {
        projects,
        filteredProjects,
        selectedProject,
        selectProject,
        createProject,
        openDeleteModal,
        openEditModal,
        setIsCreateModalOpen,
        apiCalls,
        loading,
        error,
        searchQuery,
        setSearchQuery,
        workspaceStats,
        statsLoading,
        fetchStats,
    } = useWorkspace();

    const [quickName, setQuickName] = useState('');
    const [quickUrl, setQuickUrl] = useState('');

    const calculatedEndpoints = projects.reduce((sum, p) => sum + (p.spec?.endpoints?.length || 0), 0);
    const calculatedSdks = projects.filter((p) => Boolean(p.sdk_code || p.status === 'ready')).length;

    const stats = [
        {
            label: 'Total Projects',
            value: workspaceStats ? workspaceStats.total_projects : projects.length,
            icon: Box,
            color: 'var(--accent-primary)',
            badge: 'Live',
            hint: 'All created projects',
        },
        {
            label: 'Discovered Endpoints',
            value: workspaceStats ? workspaceStats.total_endpoints : calculatedEndpoints,
            icon: Globe,
            color: 'var(--info)',
            badge: 'Real-time',
            hint: 'Across all project specs',
        },
        {
            label: 'Generated SDKs',
            value: workspaceStats ? workspaceStats.total_sdks : calculatedSdks,
            icon: Code,
            color: 'var(--success)',
            badge: 'Active',
            hint: 'Ready-to-use clients',
        },
        {
            label: 'Playground Requests',
            value: workspaceStats ? workspaceStats.total_api_calls : apiCalls,
            icon: Zap,
            color: 'var(--warning)',
            badge: 'Live',
            hint: 'Total executed calls',
        },
    ];

    const handleQuickGenerate = async (e: FormEvent) => {
        e.preventDefault();
        if (!quickUrl.trim()) return;
        await createProject(quickName.trim(), quickUrl.trim());
        setQuickName('');
        setQuickUrl('');
        onNavigateTab('results');
    };

    const handleSelectProject = async (p: typeof projects[0]) => {
        await selectProject(p);
        onNavigateTab('results');
    };

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="view-container">
            {error && (
                <div className="alert-banner error" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>{error}</span>
                    <button
                        type="button"
                        onClick={() => fetchStats()}
                        className="btn btn-outline"
                        style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                    >
                        <RefreshCw size={12} /> Retry
                    </button>
                </div>
            )}

            {/* Quick Stats Grid */}
            <div className="stats-grid">
                {stats.map((stat, i) => {
                    const Icon = stat.icon;
                    return (
                        <GlassCard key={i} className="stat-card">
                            <div className="stat-card-header">
                                <span className="stat-card-label">{stat.label}</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                    <span style={{
                                        fontSize: '0.7rem',
                                        color: 'var(--gray-400)',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        padding: '0.15rem 0.45rem',
                                        borderRadius: '4px',
                                        fontWeight: '500',
                                    }}>
                                        {stat.badge}
                                    </span>
                                    <Icon size={18} color={stat.color} />
                                </div>
                            </div>
                            <h3 className="stat-card-value">
                                {statsLoading && !workspaceStats ? (
                                    <span style={{ opacity: 0.4, fontSize: '1.2rem' }}>...</span>
                                ) : (
                                    stat.value
                                )}
                            </h3>
                            <span style={{ fontSize: '0.7rem', color: 'var(--gray-500)', marginTop: '0.2rem', display: 'block' }}>
                                {stat.hint}
                            </span>
                        </GlassCard>
                    );
                })}
            </div>

            <div className="two-col-grid">
                {/* Quick Generate Card */}
                <GlassCard style={{ padding: '2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                        <h2 style={{ fontSize: '1.2rem', color: 'var(--gray-100)', margin: 0 }}>Create New Project</h2>
                        <button
                            type="button"
                            onClick={() => setIsCreateModalOpen(true)}
                            className="btn btn-outline"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                        >
                            <Plus size={14} /> Upload Spec
                        </button>
                    </div>

                    <form onSubmit={handleQuickGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="form-group">
                            <label htmlFor="quick-project-name" className="input-label">Project Name</label>
                            <div className="input-box">
                                <input
                                    id="quick-project-name"
                                    type="text"
                                    placeholder="e.g., Stripe API Client"
                                    value={quickName}
                                    onChange={(e) => setQuickName(e.target.value)}
                                    className="input-field"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="quick-doc-url" className="input-label">Documentation URL *</label>
                            <div className="input-box">
                                <input
                                    id="quick-doc-url"
                                    type="url"
                                    required
                                    placeholder="https://docs.example.com/api"
                                    value={quickUrl}
                                    onChange={(e) => setQuickUrl(e.target.value)}
                                    className="input-field"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || !quickUrl.trim()}
                            className="btn btn-primary"
                            style={{ padding: '0.85rem', fontWeight: '700', marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                        >
                            {loading ? <Loader className="animate-spin" size={18} /> : <><Cpu size={18} /> Generate SDK Client</>}
                        </button>
                    </form>
                </GlassCard>

                {/* Selected Project Summary Card */}
                <GlassCard style={{ padding: '2rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                            <Code size={18} color="var(--accent-primary)" />
                            <h3 style={{ fontSize: '1rem', margin: 0, color: 'var(--gray-100)' }}>Active Project Context</h3>
                        </div>
                        {selectedProject ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                <div>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)', textTransform: 'uppercase' }}>Selected Project</span>
                                    <h4 style={{ fontSize: '1.15rem', color: 'var(--gray-100)', margin: '0.2rem 0' }}>{selectedProject.name}</h4>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--gray-400)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {selectedProject.description || selectedProject.url}
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                                    <div>
                                        <span style={{ fontSize: '0.7rem', color: 'var(--gray-500)', textTransform: 'uppercase' }}>Endpoints</span>
                                        <p style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--gray-200)', margin: 0 }}>
                                            {selectedProject.spec?.endpoints?.length || 0}
                                        </p>
                                    </div>
                                    <div>
                                        <span style={{ fontSize: '0.7rem', color: 'var(--gray-500)', textTransform: 'uppercase' }}>Status</span>
                                        <p style={{ fontSize: '1rem', fontWeight: '700', color: selectedProject.status === 'generating' ? 'var(--accent-primary)' : '#10B981', margin: 0 }}>
                                            {selectedProject.status === 'generating' ? 'Generating...' : 'Ready'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div style={{ padding: '1.5rem 0', color: 'var(--gray-500)', fontSize: '0.85rem' }}>
                                No project selected. Select a project from the list below or create a new one to view SDK code and test endpoints.
                            </div>
                        )}
                    </div>

                    {selectedProject && (
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                            <button
                                type="button"
                                onClick={() => onNavigateTab('results')}
                                className="btn btn-outline"
                                style={{ flex: 1, padding: '0.6rem', fontSize: '0.8rem' }}
                            >
                                View SDK Code
                            </button>
                            <button
                                type="button"
                                onClick={() => onNavigateTab('playground')}
                                className="btn btn-primary"
                                style={{ flex: 1, padding: '0.6rem', fontSize: '0.8rem' }}
                            >
                                Open Playground
                            </button>
                        </div>
                    )}
                </GlassCard>
            </div>

            {/* Projects List */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <h2 style={{ fontSize: '1.25rem', color: 'var(--gray-100)', margin: 0 }}>
                        All Projects ({filteredProjects.length})
                    </h2>
                    <div className="input-box" style={{ width: '260px' }}>
                        <Search size={14} style={{ color: 'var(--gray-500)', marginRight: '0.4rem' }} />
                        <input
                            type="text"
                            placeholder="Filter projects..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="input-field"
                            style={{ fontSize: '0.8rem', padding: '0.2rem' }}
                            aria-label="Filter projects"
                        />
                    </div>
                </div>

                {filteredProjects.length === 0 ? (
                    <EmptyState
                        icon={Box}
                        title="No projects found"
                        description={searchQuery ? `No projects matching "${searchQuery}"` : "Create your first API project above to get started."}
                        actionLabel={searchQuery ? "Clear Search" : undefined}
                        onAction={searchQuery ? () => setSearchQuery('') : undefined}
                    />
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                        {filteredProjects.map((proj) => {
                            const isSelected = selectedProject?.id === proj.id;
                            return (
                                <GlassCard
                                    key={proj.id}
                                    style={{
                                        padding: '1.25rem',
                                        cursor: 'pointer',
                                        border: isSelected ? '1px solid var(--accent-primary)' : undefined,
                                        backgroundColor: isSelected ? 'rgba(245, 166, 35, 0.04)' : undefined,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        justifyContent: 'space-between',
                                    }}
                                    onClick={() => handleSelectProject(proj)}
                                >
                                    <div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                            <h4 style={{ margin: 0, fontSize: '1rem', color: isSelected ? 'var(--accent-primary)' : 'var(--gray-100)' }}>
                                                {proj.name}
                                            </h4>
                                            <div style={{ display: 'flex', gap: '0.4rem' }}>
                                                <button
                                                    type="button"
                                                    onClick={(e) => { e.stopPropagation(); openEditModal(proj); }}
                                                    style={{ background: 'none', border: 'none', color: 'var(--gray-400)', cursor: 'pointer', padding: '2px' }}
                                                    title="Edit project"
                                                    aria-label={`Edit project ${proj.name}`}
                                                >
                                                    <Pencil size={14} />
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={(e) => { e.stopPropagation(); openDeleteModal(proj); }}
                                                    style={{ background: 'none', border: 'none', color: 'var(--gray-400)', cursor: 'pointer', padding: '2px' }}
                                                    title="Delete project"
                                                    aria-label={`Delete project ${proj.name}`}
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        </div>
                                        <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--gray-400)', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                            {proj.description || proj.url || 'No documentation URL provided'}
                                        </p>
                                    </div>

                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--gray-700)' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)' }}>
                                            {proj.spec?.endpoints?.length || 0} endpoints
                                        </span>
                                        {proj.status === 'generating' ? (
                                            <span style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                                                <Loader className="animate-spin" size={12} /> Generating
                                            </span>
                                        ) : (
                                            <span style={{ fontSize: '0.75rem', color: '#10B981', fontWeight: '500' }}>Ready</span>
                                        )}
                                    </div>
                                </GlassCard>
                            );
                        })}
                    </div>
                )}
            </div>
        </motion.div>
    );
}
