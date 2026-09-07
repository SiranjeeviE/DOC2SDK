import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Trash2, X, Loader } from 'lucide-react';
import GlassCard from '../GlassCard';

interface ConfirmDeleteModalProps {
    isOpen: boolean;
    projectName: string;
    onClose: () => void;
    onConfirm: () => Promise<void>;
    loading?: boolean;
}

export default function ConfirmDeleteModal({
    isOpen,
    projectName,
    onClose,
    onConfirm,
    loading = false,
}: ConfirmDeleteModalProps) {
    const cancelButtonRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        if (isOpen) {
            // Autofocus cancel button to prevent accidental enter-key deletion
            setTimeout(() => cancelButtonRef.current?.focus(), 50);
        }
    }, [isOpen]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!isOpen) return;
            if (e.key === 'Escape') {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div
                className="modal-backdrop"
                onClick={onClose}
                role="dialog"
                aria-modal="true"
                aria-labelledby="delete-modal-title"
                aria-describedby="delete-modal-description"
            >
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 10 }}
                    onClick={(e) => e.stopPropagation()}
                    style={{ width: '100%', maxWidth: '440px', padding: '1.25rem' }}
                >
                    <GlassCard style={{ padding: '2rem', position: 'relative' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            className="modal-close-btn"
                            aria-label="Close dialog"
                        >
                            <X size={18} />
                        </button>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.25rem' }}>
                            <div
                                style={{
                                    width: '44px',
                                    height: '44px',
                                    borderRadius: '12px',
                                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: '#EF4444',
                                    flexShrink: 0,
                                }}
                            >
                                <AlertTriangle size={24} />
                            </div>
                            <div>
                                <h3 id="delete-modal-title" style={{ fontSize: '1.15rem', margin: '0 0 0.2rem 0', color: 'var(--gray-100)' }}>
                                    Delete Project
                                </h3>
                                <span style={{ fontSize: '0.75rem', color: '#EF4444', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                    Permanent Action
                                </span>
                            </div>
                        </div>

                        <p
                            id="delete-modal-description"
                            style={{
                                color: 'var(--gray-300)',
                                fontSize: '0.875rem',
                                lineHeight: '1.5',
                                marginBottom: '1.5rem',
                            }}
                        >
                            Are you sure you want to delete <strong style={{ color: 'var(--gray-100)' }}>{projectName}</strong>? All API specifications, generated SDKs, and playground test history will be permanently deleted.
                        </p>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                            <button
                                ref={cancelButtonRef}
                                type="button"
                                onClick={onClose}
                                disabled={loading}
                                className="btn btn-outline"
                                style={{ padding: '0.6rem 1.25rem', fontSize: '0.85rem' }}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={onConfirm}
                                disabled={loading}
                                className="btn"
                                style={{
                                    padding: '0.6rem 1.25rem',
                                    fontSize: '0.85rem',
                                    backgroundColor: '#EF4444',
                                    color: '#FFFFFF',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.4rem',
                                    fontWeight: '600',
                                }}
                            >
                                {loading ? <Loader size={16} className="animate-spin" /> : <Trash2 size={16} />}
                                {loading ? 'Deleting...' : 'Delete Project'}
                            </button>
                        </div>
                    </GlassCard>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
