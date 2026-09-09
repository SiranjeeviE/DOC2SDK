import { Terminal, Send, Loader, Share2, Copy, Check, History, RotateCcw, Clock, RefreshCw } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import GlassCard from '../GlassCard';
import MethodBadge from '../common/MethodBadge';
import EmptyState from '../common/EmptyState';
import { useWorkspace } from '../../context/WorkspaceContext';
import { playgroundApi } from '../../api';
import type { PlaygroundHistoryItem, Endpoint } from '../../types';

interface PlaygroundViewProps {
    onNavigateTab: (tab: string) => void;
}

export default function PlaygroundView({ onNavigateTab }: PlaygroundViewProps) {
    const {
        selectedProject,
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
    } = useWorkspace();

    const [copied, setCopied] = useState(false);
    const [sidebarTab, setSidebarTab] = useState<'endpoints' | 'history'>('endpoints');
    const [history, setHistory] = useState<PlaygroundHistoryItem[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [replayingId, setReplayingId] = useState<string | null>(null);

    const endpoints = selectedProject?.spec?.endpoints || [];

    const fetchHistory = useCallback(async () => {
        if (!selectedProject?.id) return;
        setHistoryLoading(true);
        try {
            const data = await playgroundApi.history(selectedProject.id);
            setHistory(data || []);
        } catch (err) {
            console.error('Failed to load playground history:', err);
        } finally {
            setHistoryLoading(false);
        }
    }, [selectedProject?.id]);

    useEffect(() => {
        if (selectedProject?.id) {
            fetchHistory();
        }
    }, [selectedProject?.id, fetchHistory]);

    if (!selectedProject || !selectedProject.spec || selectedProject.status === 'generating') {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                <EmptyState
                    icon={Terminal}
                    title="Playground is locked"
                    description={selectedProject?.status === 'generating' ? "Generating SDK... Waiting for endpoints to be discovered." : "Select or generate an API project first to test endpoints."}
                    actionLabel="Go to Overview"
                    onAction={() => onNavigateTab('overview')}
                />
            </motion.div>
        );
    }

    const handleSelectEndpoint = (ep: Endpoint) => {
        setSelectedEndpoint(ep);
        setPParams({});
        setPResponse(null);
    };

    const handleParamChange = (name: string, value: string) => {
        setPParams((prev) => ({ ...prev, [name]: value }));
    };

    const handleCopyResponse = () => {
        if (!pResponse) return;
        navigator.clipboard.writeText(JSON.stringify(pResponse, null, 2));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleLoadFromHistory = (item: PlaygroundHistoryItem) => {
        const matched = endpoints.find(
            (e) => e.path === item.path && e.method.toUpperCase() === item.method.toUpperCase()
        );
        setSelectedEndpoint(matched || {
            path: item.path,
            method: item.method,
            parameters: {},
        });
        setPParams(item.params || {});
        if (item.request_body) {
            setPBody(typeof item.request_body === 'string' ? item.request_body : JSON.stringify(item.request_body, null, 2));
        } else {
            setPBody('');
        }
        if (item.response_status !== null && item.response_status !== undefined) {
            setPResponse({
                status_code: item.response_status,
                response: item.response_body,
                error: item.error_message,
            });
        }
    };

    const handleInstantReplay = async (item: PlaygroundHistoryItem) => {
        if (!selectedProject?.id) return;
        setReplayingId(item.id);
        try {
            const res = await playgroundApi.replay(selectedProject.id, item.id);
            setPResponse(res);
            await fetchHistory();
        } catch (err: unknown) {
            const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
            setPResponse({
                status_code: 400,
                response: null,
                error: errorObj.response?.data?.detail || errorObj.message || 'Replay failed',
            });
        } finally {
            setReplayingId(null);
        }
    };

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="view-container">
            <div className="playground-grid">
                {/* Column 1: Endpoints & History List */}
                <GlassCard style={{ padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--gray-700)', paddingBottom: '0.5rem' }}>
                        <button
                            type="button"
                            onClick={() => setSidebarTab('endpoints')}
                            style={{
                                flex: 1,
                                padding: '0.4rem 0.6rem',
                                borderRadius: '6px',
                                border: 'none',
                                background: sidebarTab === 'endpoints' ? 'var(--gray-700)' : 'transparent',
                                color: sidebarTab === 'endpoints' ? 'var(--gray-100)' : 'var(--gray-400)',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                textTransform: 'uppercase',
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                            }}
                        >
                            Endpoints ({endpoints.length})
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                setSidebarTab('history');
                                fetchHistory();
                            }}
                            style={{
                                flex: 1,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.35rem',
                                padding: '0.4rem 0.6rem',
                                borderRadius: '6px',
                                border: 'none',
                                background: sidebarTab === 'history' ? 'var(--gray-700)' : 'transparent',
                                color: sidebarTab === 'history' ? 'var(--gray-100)' : 'var(--gray-400)',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                textTransform: 'uppercase',
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                            }}
                        >
                            <History size={13} />
                            History ({history.length})
                        </button>
                    </div>

                    {sidebarTab === 'endpoints' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', flex: 1, overflowY: 'auto' }}>
                            {endpoints.map((ep, i) => {
                                const isSelected = selectedEndpoint?.path === ep.path && selectedEndpoint?.method === ep.method;
                                return (
                                    <button
                                        key={i}
                                        type="button"
                                        onClick={() => handleSelectEndpoint(ep)}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            padding: '0.6rem 0.75rem',
                                            borderRadius: '8px',
                                            border: isSelected ? '1px solid var(--accent-primary)' : '1px solid transparent',
                                            backgroundColor: isSelected ? 'var(--gray-700)' : 'transparent',
                                            color: isSelected ? 'var(--gray-100)' : 'var(--gray-300)',
                                            textAlign: 'left',
                                            cursor: 'pointer',
                                            transition: 'all 0.15s ease',
                                        }}
                                    >
                                        <MethodBadge method={ep.method} />
                                        <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {ep.path}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, overflowY: 'auto' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 0.25rem 0.25rem' }}>
                                <span style={{ fontSize: '0.7rem', color: 'var(--gray-400)' }}>Past Executions</span>
                                <button
                                    type="button"
                                    onClick={fetchHistory}
                                    style={{ background: 'transparent', border: 'none', color: 'var(--gray-400)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.7rem' }}
                                    title="Refresh history"
                                >
                                    <RefreshCw size={11} className={historyLoading ? 'animate-spin' : ''} /> Refresh
                                </button>
                            </div>

                            {historyLoading && history.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--gray-400)', fontSize: '0.8rem' }}>
                                    <Loader className="animate-spin" size={16} style={{ margin: '0 auto 0.5rem' }} />
                                    Loading history...
                                </div>
                            ) : history.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--gray-500)', fontSize: '0.8rem' }}>
                                    No playground history yet.<br />Run a request to save execution logs.
                                </div>
                            ) : (
                                history.map((item) => (
                                    <div
                                        key={item.id}
                                        style={{
                                            display: 'flex',
                                            flexDirection: 'column',
                                            gap: '0.4rem',
                                            padding: '0.6rem 0.75rem',
                                            borderRadius: '8px',
                                            border: '1px solid var(--gray-700)',
                                            backgroundColor: 'rgba(255,255,255,0.02)',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                            <MethodBadge method={item.method} />
                                            <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--gray-200)' }}>
                                                {item.path}
                                            </span>
                                            {item.response_status && (
                                                <span style={{
                                                    fontSize: '0.7rem',
                                                    fontWeight: '700',
                                                    padding: '0.1rem 0.35rem',
                                                    borderRadius: '4px',
                                                    backgroundColor: item.response_status < 400 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                                    color: item.response_status < 400 ? '#10B981' : '#EF4444',
                                                }}>
                                                    {item.response_status}
                                                </span>
                                            )}
                                        </div>

                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--gray-400)' }}>
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                                <Clock size={11} />
                                                {item.execution_time_ms ? `${item.execution_time_ms}ms` : ''}
                                                {item.created_at ? ` · ${new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : ''}
                                            </span>
                                            <div style={{ display: 'flex', gap: '0.35rem' }}>
                                                <button
                                                    type="button"
                                                    onClick={() => handleLoadFromHistory(item)}
                                                    style={{
                                                        padding: '0.2rem 0.45rem',
                                                        borderRadius: '4px',
                                                        border: '1px solid var(--gray-600)',
                                                        background: 'transparent',
                                                        color: 'var(--gray-200)',
                                                        fontSize: '0.7rem',
                                                        cursor: 'pointer',
                                                    }}
                                                    title="Load request into editor"
                                                >
                                                    Load
                                                </button>
                                                <button
                                                    type="button"
                                                    disabled={replayingId === item.id}
                                                    onClick={() => handleInstantReplay(item)}
                                                    style={{
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '0.2rem',
                                                        padding: '0.2rem 0.45rem',
                                                        borderRadius: '4px',
                                                        border: '1px solid var(--accent-primary)',
                                                        background: 'rgba(245, 166, 35, 0.1)',
                                                        color: 'var(--accent-primary)',
                                                        fontSize: '0.7rem',
                                                        fontWeight: '600',
                                                        cursor: replayingId === item.id ? 'not-allowed' : 'pointer',
                                                    }}
                                                    title="Replay this request immediately"
                                                >
                                                    {replayingId === item.id ? <Loader size={10} className="animate-spin" /> : <RotateCcw size={10} />}
                                                    Replay
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </GlassCard>

                {/* Column 2: Request Editor */}
                <GlassCard style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', alignItems: 'center' }}>
                        <MethodBadge method={selectedEndpoint?.method || 'GET'} />
                        <div className="input-box" style={{ flex: 1 }}>
                            <input
                                readOnly
                                value={selectedEndpoint?.path || ''}
                                className="input-field"
                                style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
                            />
                        </div>
                    </div>

                    {/* Parameters Section */}
                    {selectedEndpoint?.parameters && Object.keys(selectedEndpoint.parameters).length > 0 && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ fontSize: '0.8rem', color: 'var(--gray-400)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                                Parameters
                            </h4>
                            {Object.entries(selectedEndpoint.parameters).map(([type, list]) => {
                                if (!Array.isArray(list) || list.length === 0) return null;
                                return (
                                    <div key={type} style={{ marginBottom: '1rem' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: '600', textTransform: 'capitalize' }}>
                                            {type} parameters:
                                        </span>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.4rem' }}>
                                            {list.map((p) => (
                                                <div key={p.name} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '0.8rem', width: '120px', fontFamily: 'var(--font-mono)', color: 'var(--gray-200)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                        {p.name}
                                                    </span>
                                                    <div className="input-box" style={{ flex: 1 }}>
                                                        <input
                                                            placeholder={p.example || p.type || 'value'}
                                                            value={pParams[p.name] || ''}
                                                            onChange={(e) => handleParamChange(p.name, e.target.value)}
                                                            className="input-field"
                                                            style={{ fontSize: '0.8rem' }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Request Body (for POST/PUT/PATCH) */}
                    {['POST', 'PUT', 'PATCH'].includes(selectedEndpoint?.method || '') && (
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', marginBottom: '1.5rem' }}>
                            <h4 style={{ fontSize: '0.8rem', color: 'var(--gray-400)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                                JSON Request Body
                            </h4>
                            <div className="input-box" style={{ flex: 1, padding: 0 }}>
                                <textarea
                                    placeholder='{\n  "key": "value"\n}'
                                    value={pBody}
                                    onChange={(e) => setPBody(e.target.value)}
                                    style={{
                                        width: '100%',
                                        height: '140px',
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--gray-100)',
                                        padding: '0.75rem',
                                        fontFamily: 'var(--font-mono)',
                                        fontSize: '0.8rem',
                                        outline: 'none',
                                        resize: 'vertical',
                                    }}
                                />
                            </div>
                        </div>
                    )}

                    <button
                        type="button"
                        onClick={async () => {
                            await executePlayground();
                            fetchHistory();
                        }}
                        disabled={pLoading || !selectedEndpoint}
                        className="btn btn-primary"
                        style={{ height: '46px', fontWeight: '700', marginTop: 'auto' }}
                    >
                        {pLoading ? <Loader className="animate-spin" size={18} /> : <><Send size={16} /> Send Request</>}
                    </button>
                </GlassCard>

                {/* Column 3: Response Viewer */}
                <GlassCard style={{ padding: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{ padding: '0.85rem 1.25rem', borderBottom: '1px solid var(--gray-700)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.02)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--gray-300)', fontWeight: '600' }}>Response</span>
                            {pResponse?.status_code && (
                                <span style={{
                                    fontSize: '0.75rem',
                                    fontWeight: '700',
                                    padding: '0.15rem 0.5rem',
                                    borderRadius: '4px',
                                    backgroundColor: pResponse.status_code < 400 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                    color: pResponse.status_code < 400 ? '#10B981' : '#EF4444',
                                }}>
                                    {pResponse.status_code}
                                </span>
                            )}
                        </div>
                        {pResponse && (
                            <button
                                type="button"
                                onClick={handleCopyResponse}
                                className="btn btn-outline"
                                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                            >
                                {copied ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
                                {copied ? 'Copied' : 'Copy'}
                            </button>
                        )}
                    </div>

                    <div style={{ flex: 1, padding: '1rem', backgroundColor: 'var(--bg-main)', overflow: 'auto' }}>
                        {pLoading ? (
                            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--gray-400)' }}>
                                <Loader className="animate-spin" size={28} style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }} />
                                <span style={{ fontSize: '0.85rem' }}>Executing request...</span>
                            </div>
                        ) : pResponse ? (
                            <pre style={{
                                margin: 0,
                                fontSize: '0.8rem',
                                fontFamily: 'var(--font-mono)',
                                color: pResponse.error ? 'var(--error)' : 'var(--gray-200)',
                                lineHeight: '1.5',
                            }}>
                                {JSON.stringify(pResponse, null, 2)}
                            </pre>
                        ) : (
                            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--gray-500)', textAlign: 'center' }}>
                                <Share2 size={32} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
                                <p style={{ fontSize: '0.85rem', margin: 0 }}>Send request to see live response</p>
                            </div>
                        )}
                    </div>
                </GlassCard>
            </div>
        </motion.div>
    );
}
