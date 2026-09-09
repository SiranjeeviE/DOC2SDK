import { motion } from 'framer-motion';
import { Globe, Search } from 'lucide-react';
import GlassCard from '../GlassCard';
import MethodBadge from '../common/MethodBadge';
import EmptyState from '../common/EmptyState';
import { useWorkspace } from '../../context/WorkspaceContext';

interface EndpointsViewProps {
    onNavigateTab: (tab: string) => void;
}

export default function EndpointsView({ onNavigateTab }: EndpointsViewProps) {
    const { selectedProject, filteredEndpoints, setSelectedEndpoint, searchQuery, setSearchQuery } = useWorkspace();

    if (!selectedProject || !selectedProject.spec) {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                <EmptyState
                    icon={Globe}
                    title="No project selected"
                    description="Select or generate a project from the Overview tab to inspect its discovered API endpoints."
                    actionLabel="Go to Overview"
                    onAction={() => onNavigateTab('overview')}
                />
            </motion.div>
        );
    }

    const handleTestEndpoint = (ep: typeof filteredEndpoints[0]) => {
        setSelectedEndpoint(ep);
        onNavigateTab('playground');
    };

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="view-container">
            <div className="view-header">
                <div>
                    <h1 className="view-title">Discovered Endpoints</h1>
                    <p className="view-subtitle">
                        Endpoints discovered from <strong>{selectedProject.name}</strong> ({selectedProject.spec.endpoints.length} total).
                    </p>
                </div>
            </div>

            <GlassCard style={{ padding: '0', overflow: 'hidden' }}>
                <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--gray-700)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--gray-300)', fontWeight: '600' }}>
                        {searchQuery ? `Filtered Endpoints (${filteredEndpoints.length})` : 'All Endpoints'}
                    </span>
                    {searchQuery && (
                        <button type="button" onClick={() => setSearchQuery('')} className="btn btn-outline" style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}>
                            Clear Search
                        </button>
                    )}
                </div>

                {filteredEndpoints.length === 0 ? (
                    <div style={{ padding: '3rem 2rem', textAlign: 'center' }}>
                        <Search size={32} style={{ opacity: 0.3, margin: '0 auto 0.75rem', display: 'block' }} />
                        <h4 style={{ color: 'var(--gray-200)', marginBottom: '0.25rem' }}>No matching endpoints</h4>
                        <p style={{ color: 'var(--gray-400)', fontSize: '0.85rem' }}>Try adjusting your search query.</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {filteredEndpoints.map((ep, i) => (
                            <div
                                key={i}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '1rem 1.5rem',
                                    borderBottom: i < filteredEndpoints.length - 1 ? '1px solid var(--gray-800)' : 'none',
                                    transition: 'background-color 0.15s ease',
                                }}
                            >
                                <MethodBadge method={ep.method} />
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <p style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.2rem', fontFamily: 'var(--font-mono)', color: 'var(--gray-100)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {ep.path}
                                    </p>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--gray-400)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {ep.summary || ep.description || 'No description provided'}
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleTestEndpoint(ep)}
                                    className="btn btn-outline"
                                    style={{ padding: '0.35rem 0.8rem', fontSize: '0.8rem', color: 'var(--accent-primary)', borderColor: 'rgba(245, 166, 35, 0.3)' }}
                                >
                                    Test →
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </GlassCard>
        </motion.div>
    );
}
