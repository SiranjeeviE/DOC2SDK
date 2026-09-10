import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContextType {
    showToast: (message: string, type?: ToastType, duration?: number) => void;
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
    removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const showToast = useCallback((message: string, type: ToastType = 'info', duration = 4000) => {
        const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        setToasts((prev) => [...prev, { id, type, message, duration }]);

        if (duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    }, [removeToast]);

    const success = useCallback((msg: string, d?: number) => showToast(msg, 'success', d), [showToast]);
    const error = useCallback((msg: string, d?: number) => showToast(msg, 'error', d ?? 5000), [showToast]);
    const warning = useCallback((msg: string, d?: number) => showToast(msg, 'warning', d), [showToast]);
    const info = useCallback((msg: string, d?: number) => showToast(msg, 'info', d), [showToast]);

    const getIcon = (type: ToastType) => {
        switch (type) {
            case 'success':
                return <CheckCircle2 size={18} color="#10B981" />;
            case 'error':
                return <AlertCircle size={18} color="#EF4444" />;
            case 'warning':
                return <AlertTriangle size={18} color="#F5A623" />;
            case 'info':
            default:
                return <Info size={18} color="#60A5FA" />;
        }
    };

    const getBorderColor = (type: ToastType) => {
        switch (type) {
            case 'success':
                return 'rgba(16, 185, 129, 0.4)';
            case 'error':
                return 'rgba(239, 68, 68, 0.4)';
            case 'warning':
                return 'rgba(245, 166, 35, 0.4)';
            case 'info':
            default:
                return 'rgba(96, 165, 250, 0.4)';
        }
    };

    return (
        <ToastContext.Provider value={{ showToast, success, error, warning, info, removeToast }}>
            {children}
            {/* Toast Container */}
            <div
                aria-live="polite"
                aria-atomic="true"
                style={{
                    position: 'fixed',
                    bottom: '1.5rem',
                    right: '1.5rem',
                    zIndex: 9999,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.6rem',
                    maxWidth: '380px',
                    width: 'calc(100vw - 3rem)',
                    pointerEvents: 'none',
                }}
            >
                <AnimatePresence>
                    {toasts.map((t) => (
                        <motion.div
                            key={t.id}
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
                            layout
                            style={{
                                pointerEvents: 'auto',
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '0.75rem',
                                padding: '0.85rem 1rem',
                                borderRadius: '10px',
                                backgroundColor: 'rgba(20, 20, 22, 0.95)',
                                backdropFilter: 'blur(16px)',
                                WebkitBackdropFilter: 'blur(16px)',
                                border: `1px solid ${getBorderColor(t.type)}`,
                                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)',
                                color: 'var(--gray-100)',
                                fontSize: '0.85rem',
                                lineHeight: '1.4',
                            }}
                        >
                            <div style={{ flexShrink: 0, marginTop: '1px' }}>{getIcon(t.type)}</div>
                            <div style={{ flex: 1, wordBreak: 'break-word' }}>{t.message}</div>
                            <button
                                type="button"
                                onClick={() => removeToast(t.id)}
                                aria-label="Dismiss notification"
                                style={{
                                    flexShrink: 0,
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--gray-400)',
                                    cursor: 'pointer',
                                    padding: '2px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    transition: 'color 0.15s ease',
                                }}
                            >
                                <X size={14} />
                            </button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
}

export function useToast(): ToastContextType {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
}
