import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    GitCompare,
    UploadCloud,
    RefreshCw,
    Loader,
    CheckCircle2,
    AlertTriangle,
} from 'lucide-react';
import GlassCard from '../GlassCard';
import EmptyState from '../common/EmptyState';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function ChangesView() {
    const navigate = useNavigate();
    const {
        selectedProject: result,
        diffResult,
        diffLoading,
        diffError,
        specVersions,
        checkingChanges,
        checkStatus,
        checkChanges,
        setIsUploadSpecModalOpen,
    } = useWorkspace();

    if (!result) {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                <EmptyState
                    icon={GitCompare}
                    title="No Project Selected"
                    description="Select a project from the Overview to monitor API schema changes and detect breaking modifications."
                    actionLabel="Go to Overview"
                    onAction={() => navigate('/')}
                />
            </motion.div>
        );
    }

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 style={{ fontSize: '1.75rem', margin: '0 0 0.5rem 0', color: 'var(--gray-100)' }}>API Change Monitor</h1>
                        <p style={{ color: 'var(--gray-300)', margin: 0, fontSize: '0.9rem' }}>
                            Automatically detect breaking changes, removed endpoints, and schema diffs across specification versions for <strong>{result.name}</strong>.
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <button
                            type="button"
                            onClick={() => checkChanges()}
                            disabled={checkingChanges}
                            className="btn btn-outline"
                            style={{ padding: '0.6rem 1.25rem', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                        >
                            {checkingChanges ? <Loader className="animate-spin" size={16} /> : <RefreshCw size={16} />}
                            Check for Changes
                        </button>
                        <button
                            type="button"
                            onClick={() => setIsUploadSpecModalOpen(true)}
                            className="btn btn-primary"
                            style={{ padding: '0.6rem 1.25rem', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                        >
                            <UploadCloud size={16} /> Upload New Version
                        </button>
                    </div>
                </div>

                {checkStatus && (
                    <div style={{
                        padding: '0.75rem 1.25rem',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        color: '#60A5FA',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                    }}>
                        <CheckCircle2 size={16} />
                        {checkStatus}
                    </div>
                )}

                {diffError && (
                    <div style={{
                        padding: '0.75rem 1.25rem',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        color: '#EF4444',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                    }}>
                        <AlertTriangle size={16} />
                        {diffError}
                    </div>
                )}

                {diffLoading ? (
                    <div style={{ textAlign: 'center', padding: '4rem' }}>
                        <Loader className="animate-spin" size={36} style={{ opacity: 0.6, margin: '0 auto 1rem', color: 'var(--accent-primary)', display: 'block' }} />
                        <p style={{ color: 'var(--gray-300)' }}>Analyzing specification versions and computing diff...</p>
                    </div>
                ) : diffResult ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {/* Diff Summary Card */}
                        <GlassCard style={{
                            padding: '1.5rem',
                            borderLeft: diffResult.is_breaking ? '4px solid #EF4444' : '4px solid #10B981',
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                    <div style={{
                                        padding: '0.75rem',
                                        borderRadius: '10px',
                                        background: diffResult.is_breaking ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                                        color: diffResult.is_breaking ? '#EF4444' : '#10B981',
                                    }}>
                                        {diffResult.is_breaking ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
                                    </div>
                                    <div>
                                        <h3 style={{ margin: '0 0 0.25rem 0', color: 'var(--gray-100)', fontSize: '1.2rem' }}>
                                            {diffResult.is_breaking
                                                ? `Breaking Changes Detected (v${diffResult.from_version} → v${diffResult.to_version})`
                                                : diffResult.total_changes === 0
                                                ? `No Changes Detected (v${diffResult.from_version} → v${diffResult.to_version})`
                                                : `Backward-Compatible Changes (v${diffResult.from_version} → v${diffResult.to_version})`}
                                        </h3>
                                        <p style={{ margin: 0, color: 'var(--gray-300)', fontSize: '0.875rem' }}>
                                            {diffResult.is_breaking
                                                ? `${diffResult.breaking_changes_count} breaking change${diffResult.breaking_changes_count === 1 ? '' : 's'} require client updates. Total changes: ${diffResult.total_changes}.`
                                                : diffResult.total_changes === 0
                                                ? 'Both specification versions have identical endpoints, parameters, schemas, and authentication.'
                                                : `All ${diffResult.total_changes} change${diffResult.total_changes === 1 ? '' : 's'} are safe and backward-compatible.`}
                                        </p>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                    <span style={{
                                        padding: '0.4rem 0.8rem',
                                        borderRadius: '20px',
                                        fontSize: '0.75rem',
                                        fontWeight: '700',
                                        letterSpacing: '0.05em',
                                        textTransform: 'uppercase',
                                        background: diffResult.is_breaking ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                                        color: diffResult.is_breaking ? '#F87171' : '#34D399',
                                        border: diffResult.is_breaking ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)',
                                    }}>
                                        {diffResult.is_breaking ? 'BREAKING CHANGE' : 'COMPATIBLE'}
                                    </span>
                                </div>
                            </div>
                        </GlassCard>

                        {/* Changes Detail List */}
                        <GlassCard style={{ padding: '1.5rem' }}>
                            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', color: 'var(--gray-100)', fontWeight: '600' }}>
                                Change Details ({diffResult.changes.length})
                            </h3>
                            {diffResult.changes.length === 0 ? (
                                <p style={{ color: 'var(--gray-400)', margin: 0, fontSize: '0.9rem' }}>
                                    No differences between version {diffResult.from_version} and version {diffResult.to_version}.
                                </p>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    {diffResult.changes.map((change, idx) => (
                                        <div
                                            key={idx}
                                            style={{
                                                padding: '1rem',
                                                borderRadius: '8px',
                                                background: 'var(--bg-card)',
                                                border: change.breaking ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid var(--gray-700)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'space-between',
                                                gap: '1rem',
                                            }}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1 }}>
                                                <span style={{
                                                    padding: '0.2rem 0.5rem',
                                                    borderRadius: '4px',
                                                    fontSize: '0.7rem',
                                                    fontWeight: '700',
                                                    textTransform: 'uppercase',
                                                    background: change.breaking ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.15)',
                                                    color: change.breaking ? '#EF4444' : '#60A5FA',
                                                    border: change.breaking ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(59, 130, 246, 0.3)',
                                                }}>
                                                    {change.breaking ? 'BREAKING' : 'INFO'}
                                                </span>
                                                {change.method && (
                                                    <span style={{
                                                        fontSize: '0.75rem',
                                                        fontWeight: '700',
                                                        padding: '0.15rem 0.4rem',
                                                        borderRadius: '4px',
                                                        background: 'var(--gray-700)',
                                                        color: 'var(--gray-100)',
                                                    }}>
                                                        {change.method}
                                                    </span>
                                                )}
                                                {change.path && (
                                                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--gray-200)' }}>
                                                        {change.path}
                                                    </span>
                                                )}
                                                <span style={{ color: 'var(--gray-300)', fontSize: '0.85rem' }}>
                                                    {change.description}
                                                </span>
                                            </div>
                                            <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)', textTransform: 'capitalize' }}>
                                                {change.type.replace(/_/g, ' ')}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                ) : (
                    /* Only 1 version exists or no diff */
                    <GlassCard style={{ padding: '3.5rem 2rem', textAlign: 'center', maxWidth: '720px', margin: '0 auto' }}>
                        <div style={{
                            width: '56px',
                            height: '56px',
                            borderRadius: '14px',
                            background: 'rgba(59, 130, 246, 0.1)',
                            border: '1px solid rgba(59, 130, 246, 0.25)',
                            color: '#60A5FA',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            margin: '0 auto 1.25rem',
                        }}>
                            <GitCompare size={28} />
                        </div>
                        <h3 style={{ fontSize: '1.25rem', color: 'var(--gray-100)', marginBottom: '0.5rem' }}>
                            Single Specification Version Active ({specVersions.length === 1 ? `v${specVersions[0].version}` : 'v1.0'})
                        </h3>
                        <p style={{ color: 'var(--gray-300)', fontSize: '0.9rem', lineHeight: '1.6', maxWidth: '520px', margin: '0 auto 1.75rem' }}>
                            API Change Monitor tracks version changes and flags breaking alterations. To start detecting changes, upload an updated OpenAPI or Postman specification, or trigger a remote change check.
                        </p>
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                            <button
                                type="button"
                                onClick={() => setIsUploadSpecModalOpen(true)}
                                className="btn btn-primary"
                                style={{ padding: '0.6rem 1.25rem' }}
                            >
                                <UploadCloud size={16} /> Upload New Spec Version
                            </button>
                            <button
                                type="button"
                                onClick={() => checkChanges()}
                                disabled={checkingChanges}
                                className="btn btn-outline"
                                style={{ padding: '0.6rem 1.25rem' }}
                            >
                                {checkingChanges ? <Loader className="animate-spin" size={16} /> : <RefreshCw size={16} />}
                                Check for Remote Changes
                            </button>
                        </div>
                    </GlassCard>
                )}
            </div>
        </motion.div>
    );
}
