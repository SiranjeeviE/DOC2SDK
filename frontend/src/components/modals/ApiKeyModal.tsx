import { useState, type FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Key, Loader, ShieldCheck, ShieldAlert } from 'lucide-react';
import { authApi } from '../../api';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function ApiKeyModal() {
    const { isApiKeyModalOpen, setIsApiKeyModalOpen, isAuthEnabled } = useWorkspace();
    const [apiKeyInput, setApiKeyInput] = useState(() => authApi.getApiKey());
    const [verifying, setVerifying] = useState(false);
    const [verifyStatus, setVerifyStatus] = useState<string | null>(null);

    if (!isApiKeyModalOpen) return null;

    const handleSave = async (e: FormEvent) => {
        e.preventDefault();
        setVerifying(true);
        setVerifyStatus(null);
        try {
            if (!apiKeyInput.trim()) {
                authApi.clearApiKey();
                setVerifyStatus('API key cleared.');
                setTimeout(() => setIsApiKeyModalOpen(false), 1000);
                return;
            }
            const res = await authApi.verify(apiKeyInput.trim());
            if (res.authenticated) {
                authApi.setApiKey(apiKeyInput.trim());
                setVerifyStatus('API key verified and saved successfully!');
                setTimeout(() => setIsApiKeyModalOpen(false), 1200);
            } else {
                setVerifyStatus('Invalid API key. Please check your credentials.');
            }
        } catch {
            setVerifyStatus('Verification failed. Could not reach server.');
        } finally {
            setVerifying(false);
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
                    <button type="button" onClick={() => setIsApiKeyModalOpen(false)} className="modal-close-btn" title="Close modal">
                        <X size={20} />
                    </button>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'var(--accent-primary-muted)', color: 'var(--accent-primary)' }}>
                            <Key size={22} />
                        </div>
                        <h2 style={{ fontSize: '1.4rem', color: 'var(--gray-100)', margin: 0 }}>API Key Settings</h2>
                    </div>
                    <p style={{ color: 'var(--gray-300)', marginBottom: '1.5rem', fontSize: '0.85rem', lineHeight: '1.5' }}>
                        {isAuthEnabled
                            ? 'This server requires an API key to access generation and playground endpoints.'
                            : 'Authentication is currently optional on this server. You can configure your API key below.'}
                    </p>

                    <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div className="form-group">
                            <label className="input-label">DOC2SDK API KEY</label>
                            <div className="input-box">
                                <input
                                    type="password"
                                    value={apiKeyInput}
                                    onChange={(e) => setApiKeyInput(e.target.value)}
                                    placeholder="Enter your API key"
                                    className="input-field"
                                />
                            </div>
                        </div>

                        {verifyStatus && (
                            <div className={`alert-banner ${verifyStatus.includes('successfully') ? 'success' : 'error'}`}>
                                {verifyStatus.includes('successfully') ? <ShieldCheck size={16} /> : <ShieldAlert size={16} />}
                                <span>{verifyStatus}</span>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                            <button
                                type="button"
                                onClick={() => {
                                    authApi.clearApiKey();
                                    setApiKeyInput('');
                                    setVerifyStatus('API key cleared.');
                                }}
                                className="btn btn-outline"
                                style={{ flex: 1, height: '46px' }}
                            >
                                Clear
                            </button>
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={verifying}
                                style={{ flex: 2, height: '46px', fontWeight: '700' }}
                            >
                                {verifying ? <Loader className="animate-spin" size={18} /> : 'Verify & Save'}
                            </button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
