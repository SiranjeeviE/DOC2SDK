import { motion } from 'framer-motion';
import { Database } from 'lucide-react';
import GlassCard from '../GlassCard';
import { useWorkspace } from '../../context/WorkspaceContext';

interface DatabasesViewProps {
    onNavigateTab: (tab: string) => void;
}

export default function DatabasesView({ onNavigateTab }: DatabasesViewProps) {
    const { setIsCreateModalOpen } = useWorkspace();

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="view-container">
            <div className="view-header">
                <div>
                    <h1 className="view-title">Databases</h1>
                    <p className="view-subtitle">Connect SQL and NoSQL database schemas to automatically generate typed SDK clients.</p>
                </div>
            </div>

            <GlassCard style={{ padding: '3.5rem 2rem', textAlign: 'center', maxWidth: '820px', margin: '0 auto' }}>
                <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '16px',
                    background: 'var(--accent-primary-muted)',
                    border: '1px solid rgba(245, 166, 35, 0.25)',
                    color: 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 1.5rem',
                }}>
                    <Database size={32} />
                </div>

                <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '20px',
                    background: 'rgba(245, 166, 35, 0.15)',
                    color: 'var(--accent-primary)',
                    fontSize: '0.75rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '1rem',
                }}>
                    Roadmap Feature
                </div>

                <h2 style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--gray-100)', marginBottom: '0.75rem' }}>
                    Database Schema Introspection Coming Soon
                </h2>

                <p style={{ color: 'var(--gray-300)', fontSize: '0.95rem', lineHeight: '1.6', maxWidth: '580px', margin: '0 auto 2rem' }}>
                    Doc2SDK currently specializes in scraping REST API and OpenAPI documentation to generate client SDKs. Direct database schema introspection (PostgreSQL, MySQL, SQLite, MongoDB) to generate typed query SDKs is actively being developed.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2.5rem', textAlign: 'left' }}>
                    <div style={{ padding: '1.25rem', borderRadius: '10px', background: 'var(--bg-card)', border: '1px solid var(--gray-700)' }}>
                        <h4 style={{ fontSize: '0.9rem', color: 'var(--gray-100)', marginBottom: '0.4rem', fontWeight: '600' }}>PostgreSQL & MySQL</h4>
                        <p style={{ fontSize: '0.8rem', color: 'var(--gray-400)', margin: 0 }}>Auto-introspect relational tables, foreign keys, and indexes.</p>
                    </div>
                    <div style={{ padding: '1.25rem', borderRadius: '10px', background: 'var(--bg-card)', border: '1px solid var(--gray-700)' }}>
                        <h4 style={{ fontSize: '0.9rem', color: 'var(--gray-100)', marginBottom: '0.4rem', fontWeight: '600' }}>Type-Safe Clients</h4>
                        <p style={{ fontSize: '0.8rem', color: 'var(--gray-400)', margin: 0 }}>Generate TypeScript, Python, and Go ORM-like typed wrappers.</p>
                    </div>
                    <div style={{ padding: '1.25rem', borderRadius: '10px', background: 'var(--bg-card)', border: '1px solid var(--gray-700)' }}>
                        <h4 style={{ fontSize: '0.9rem', color: 'var(--gray-100)', marginBottom: '0.4rem', fontWeight: '600' }}>Live Schema Browser</h4>
                        <p style={{ fontSize: '0.8rem', color: 'var(--gray-400)', margin: 0 }}>Explore entities, types, and run mock queries in the browser.</p>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                    <button type="button" onClick={() => onNavigateTab('overview')} className="btn btn-outline" style={{ padding: '0.6rem 1.25rem' }}>
                        Return to Overview
                    </button>
                    <button type="button" onClick={() => setIsCreateModalOpen(true)} className="btn btn-primary" style={{ padding: '0.6rem 1.25rem' }}>
                        Generate API SDK
                    </button>
                </div>
            </GlassCard>
        </motion.div>
    );
}
