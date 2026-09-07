import { useState, useEffect, type FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader, Check, AlertCircle } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function EditProjectModal() {
    const { isEditModalOpen, setIsEditModalOpen, editingProject, updateProject } = useWorkspace();
    const [name, setName] = useState('');
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    useEffect(() => {
        if (editingProject) {
            setName(editingProject.name || '');
            setUrl(editingProject.url || editingProject.description || '');
            setError(null);
            setSuccess(null);
        }
    }, [editingProject]);

    if (!isEditModalOpen || !editingProject) return null;

    const handleClose = () => {
        setIsEditModalOpen(false);
        setError(null);
        setSuccess(null);
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            await updateProject(editingProject.id, name.trim(), url.trim());
            setSuccess('Project updated successfully!');
            setTimeout(() => {
                handleClose();
            }, 600);
        } catch (err: unknown) {
            const errObj = err as { response?: { data?: { detail?: string } }; message?: string };
            setError(errObj.response?.data?.detail || errObj.message || 'Failed to update project.');
        } finally {
            setLoading(false);
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

                    <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--gray-100)' }}>Edit Project</h2>
                    <p style={{ color: 'var(--gray-300)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                        Modify project name or documentation URL.
                    </p>

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div className="form-group">
                            <label className="input-label">PROJECT NAME</label>
                            <div className="input-box">
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    className="input-field"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="input-label">DOCUMENTATION URL</label>
                            <div className="input-box">
                                <input
                                    type="text"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    required
                                    className="input-field"
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="alert-banner error">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        {success && (
                            <div className="alert-banner success">
                                <Check size={16} />
                                <span>{success}</span>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
                            <button type="button" onClick={handleClose} className="btn btn-outline" style={{ flex: 1, height: '48px' }}>
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary" disabled={loading} style={{ flex: 2, height: '48px', fontWeight: '700' }}>
                                {loading ? <Loader className="animate-spin" size={18} /> : 'Save Changes'}
                            </button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
