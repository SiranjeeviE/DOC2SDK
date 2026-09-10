import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader, Code, Download, FileCheck } from 'lucide-react';
import EmptyState from '../common/EmptyState';
import CodeViewer from '../common/CodeViewer';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function ResultsView() {
    const navigate = useNavigate();
    const { selectedProject: result, downloadFile } = useWorkspace();

    if (!result || result.status === 'generating' || !result.spec) {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                {result?.status === 'generating' ? (
                    <div style={{ textAlign: 'center', padding: '4rem' }}>
                        <Loader className="animate-spin" size={48} style={{ opacity: 0.5, margin: '0 auto 1rem', color: 'var(--accent-primary)', display: 'block' }} />
                        <h3>Generating SDK...</h3>
                        <p style={{ color: 'var(--gray-300)' }}>Hold tight, we&apos;re building your SDK. This may take up to a minute.</p>
                    </div>
                ) : (
                    <EmptyState
                        icon={Code}
                        title="No results yet"
                        description="Go to Overview to generate your first SDK client."
                        actionLabel="Back to Overview"
                        onAction={() => navigate('/')}
                    />
                )}
            </motion.div>
        );
    }

    const specJson = JSON.stringify(result.spec, null, 2);
    const sdkFilename = `${result.name.replace(/\s+/g, '_')}_sdk.py`;
    const specFilename = `${result.name.replace(/\s+/g, '_')}_spec.json`;

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div className="results-grid">
                {/* SDK Code */}
                <div>
                    <CodeViewer
                        code={result.sdk_code || '# No SDK code generated'}
                        language="python"
                        filename={sdkFilename}
                        actions={
                            <>
                                <button
                                    type="button"
                                    onClick={() => downloadFile(result.sdk_code || '', sdkFilename, 'text/x-python')}
                                    className="btn btn-outline"
                                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                                    title="Download Python SDK"
                                >
                                    <Download size={13} /> Download
                                </button>
                                {result.test_code && (
                                    <button
                                        type="button"
                                        onClick={() => downloadFile(result.test_code || '', `${result.name.replace(/\s+/g, '_')}_test.py`, 'text/x-python')}
                                        className="btn btn-outline"
                                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                                        title="Download Test Suite"
                                    >
                                        <FileCheck size={13} color="var(--accent-primary)" /> Tests
                                    </button>
                                )}
                            </>
                        }
                    />
                </div>

                {/* Spec JSON */}
                <div>
                    <CodeViewer
                        code={specJson}
                        language="json"
                        filename={specFilename}
                        actions={
                            <button
                                type="button"
                                onClick={() => downloadFile(specJson, specFilename, 'application/json')}
                                className="btn btn-outline"
                                style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                                title="Download OpenAPI JSON Spec"
                            >
                                <Download size={13} /> Download
                            </button>
                        }
                    />
                </div>
            </div>
        </motion.div>
    );
}
