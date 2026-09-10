import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileCheck, Download } from 'lucide-react';
import EmptyState from '../common/EmptyState';
import CodeViewer from '../common/CodeViewer';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function TestsView() {
    const navigate = useNavigate();
    const { selectedProject: result, downloadFile } = useWorkspace();

    if (!result || !result.test_code) {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                <EmptyState
                    icon={FileCheck}
                    title="No Test Suite Available"
                    description="Select or generate an SDK project to view automated unit and integration tests."
                    actionLabel="Back to Overview"
                    onAction={() => navigate('/')}
                />
            </motion.div>
        );
    }

    const testFilename = `${result.name.replace(/\s+/g, '_')}_test.py`;

    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 style={{ fontSize: '1.75rem', margin: '0 0 0.5rem 0', color: 'var(--gray-100)' }}>Automated Test Suite</h1>
                        <p style={{ color: 'var(--gray-300)', margin: 0, fontSize: '0.9rem' }}>
                            Ready-to-run unit &amp; integration tests covering parameters, request bodies, mock responses, 200 OK success, 400 Bad Request, and 500 error handling.
                        </p>
                    </div>
                </div>

                <CodeViewer
                    code={result.test_code}
                    language="python"
                    filename={testFilename}
                    actions={
                        <button
                            type="button"
                            onClick={() => downloadFile(result.test_code || '', testFilename, 'text/x-python')}
                            className="btn btn-primary"
                            style={{ padding: '0.35rem 0.85rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                            title="Download Test Suite"
                        >
                            <Download size={13} /> Download Test Suite
                        </button>
                    }
                />
            </div>
        </motion.div>
    );
}
