import { useState, type FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, UploadCloud, Loader, AlertCircle } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function UploadSpecModal() {
    const { isUploadSpecModalOpen, setIsUploadSpecModalOpen, uploadNewSpec } = useWorkspace();
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isUploadSpecModalOpen) return null;

    const handleClose = () => {
        setIsUploadSpecModalOpen(false);
        setFile(null);
        setError(null);
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        setError(null);
        try {
            await uploadNewSpec(file);
            handleClose();
        } catch (err: unknown) {
            const errObj = err as { response?: { data?: { detail?: string } }; message?: string };
            setError(errObj.response?.data?.detail || errObj.message || 'Failed to upload new specification.');
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

                    <h2 style={{ fontSize: '1.4rem', marginBottom: '0.5rem', color: 'var(--gray-100)' }}>Upload New Spec Version</h2>
                    <p style={{ color: 'var(--gray-300)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
                        Upload an updated OpenAPI JSON/YAML or Postman collection to compare against existing versions.
                    </p>

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div className="form-group">
                            <input
                                type="file"
                                accept=".json,.yaml,.yml"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                                id="new-spec-file-input"
                                style={{ display: 'none' }}
                            />
                            <label htmlFor="new-spec-file-input" className="file-dropzone">
                                <UploadCloud size={32} color="var(--accent-primary)" />
                                <span style={{ fontSize: '0.9rem', color: 'var(--gray-200)', fontWeight: '500' }}>
                                    {file ? file.name : 'Click to browse spec file'}
                                </span>
                                <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)' }}>
                                    Supports OpenAPI 3.0 (JSON/YAML) and Postman v2.0/v2.1
                                </span>
                            </label>
                        </div>

                        {error && (
                            <div className="alert-banner error">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                            <button type="button" onClick={handleClose} className="btn btn-outline" style={{ flex: 1, height: '46px' }}>
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={!file || loading}
                                className="btn btn-primary"
                                style={{ flex: 2, height: '46px', fontWeight: '700' }}
                            >
                                {loading ? <Loader className="animate-spin" size={18} /> : 'Upload & Diff'}
                            </button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
