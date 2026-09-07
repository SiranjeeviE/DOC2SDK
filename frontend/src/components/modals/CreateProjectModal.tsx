import { useState, type FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Cpu, UploadCloud, AlertCircle } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface CreateProjectModalProps {
    onSuccess?: () => void;
}

export default function CreateProjectModal({ onSuccess }: CreateProjectModalProps) {
    const { isCreateModalOpen, setIsCreateModalOpen, createProject, uploadProject, loading, error, setError } = useWorkspace();
    const [mode, setMode] = useState<'url' | 'file'>('url');
    const [projectName, setProjectName] = useState('');
    const [url, setUrl] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    if (!isCreateModalOpen) return null;

    const handleClose = () => {
        setIsCreateModalOpen(false);
        setError(null);
        setProjectName('');
        setUrl('');
        setSelectedFile(null);
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);

        try {
            if (mode === 'url') {
                if (!url.startsWith('http://') && !url.startsWith('https://')) {
                    setError('Please enter a valid URL starting with http:// or https://');
                    return;
                }
                await createProject(projectName.trim(), url.trim());
            } else {
                if (!selectedFile) {
                    setError('Please select an OpenAPI JSON/YAML or Postman collection file.');
                    return;
                }
                await uploadProject(selectedFile, projectName.trim() || undefined);
            }
            handleClose();
            onSuccess?.();
        } catch (err: unknown) {
            const errObj = err as { response?: { data?: { detail?: string } }; message?: string };
            setError(errObj.response?.data?.detail || errObj.message || 'Project creation failed');
        }
    };

    return (
        <AnimatePresence>
            <div className="modal-backdrop">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="glass-modal modal-dialog"
                >
                    <button type="button" onClick={handleClose} className="modal-close-btn" title="Close modal">
                        <X size={20} />
                    </button>

                    <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--gray-100)' }}>Create New Project</h2>
                    <p style={{ color: 'var(--gray-300)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                        Scrape documentation or upload an OpenAPI/Postman specification.
                    </p>

                    {/* Mode Switcher */}
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--gray-700)', paddingBottom: '0.75rem' }}>
                        <button
                            type="button"
                            onClick={() => { setMode('url'); setError(null); }}
                            style={{
                                flex: 1,
                                padding: '0.5rem',
                                borderRadius: '6px',
                                background: mode === 'url' ? 'var(--accent-primary-muted)' : 'transparent',
                                border: mode === 'url' ? '1px solid var(--accent-primary)' : '1px solid transparent',
                                color: mode === 'url' ? 'var(--gray-100)' : 'var(--gray-400)',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: '600',
                            }}
                        >
                            Documentation URL
                        </button>
                        <button
                            type="button"
                            onClick={() => { setMode('file'); setError(null); }}
                            style={{
                                flex: 1,
                                padding: '0.5rem',
                                borderRadius: '6px',
                                background: mode === 'file' ? 'var(--accent-primary-muted)' : 'transparent',
                                border: mode === 'file' ? '1px solid var(--accent-primary)' : '1px solid transparent',
                                color: mode === 'file' ? 'var(--gray-100)' : 'var(--gray-400)',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: '600',
                            }}
                        >
                            Upload Specification
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div className="form-group">
                            <label className="input-label">PROJECT NAME</label>
                            <div className="input-box">
                                <input
                                    type="text"
                                    placeholder="e.g. Stripe Payment API"
                                    value={projectName}
                                    onChange={(e) => setProjectName(e.target.value)}
                                    className="input-field"
                                />
                            </div>
                        </div>

                        {mode === 'url' ? (
                            <div className="form-group">
                                <label className="input-label">DOCUMENTATION URL</label>
                                <div className="input-box">
                                    <input
                                        type="url"
                                        placeholder="https://api.example.com/docs"
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                        required={mode === 'url'}
                                        className="input-field"
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="form-group">
                                <label className="input-label">API SPECIFICATION FILE</label>
                                <input
                                    type="file"
                                    accept=".json,.yaml,.yml"
                                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                                    id="modal-file-upload-input"
                                    style={{ display: 'none' }}
                                />
                                <label htmlFor="modal-file-upload-input" className="file-dropzone">
                                    <UploadCloud size={32} color="var(--accent-primary)" />
                                    <span style={{ fontSize: '0.9rem', color: 'var(--gray-200)', fontWeight: '500' }}>
                                        {selectedFile ? selectedFile.name : 'Choose OpenAPI (.json/.yaml) or Postman (.json)'}
                                    </span>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)' }}>Max file size 10MB</span>
                                </label>
                            </div>
                        )}

                        {error && (
                            <div className="alert-banner error">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
                            <button type="button" onClick={handleClose} className="btn btn-outline" style={{ flex: 1, height: '48px' }}>
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary" disabled={loading} style={{ flex: 2, height: '48px', fontWeight: '700' }}>
                                {loading ? <Cpu className="animate-spin" size={18} /> : (mode === 'file' ? 'Upload & Generate' : 'Generate SDK')}
                            </button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
