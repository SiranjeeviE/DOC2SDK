import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Compass, ArrowLeft } from 'lucide-react';
import GlassCard from '../components/GlassCard';

export default function NotFound() {
    const navigate = useNavigate();

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'var(--bg-main)',
            padding: '2rem',
        }}>
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                style={{ maxWidth: '480px', width: '100%' }}
            >
                <GlassCard style={{ padding: '3rem 2rem', textAlign: 'center' }}>
                    <div style={{
                        width: '64px',
                        height: '64px',
                        borderRadius: '16px',
                        background: 'rgba(245, 166, 35, 0.1)',
                        border: '1px solid rgba(245, 166, 35, 0.25)',
                        color: 'var(--accent-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 1.5rem',
                    }}>
                        <Compass size={32} />
                    </div>

                    <div style={{
                        fontSize: '3rem',
                        fontWeight: '800',
                        color: 'var(--accent-primary)',
                        lineHeight: 1,
                        marginBottom: '0.5rem',
                        fontFamily: 'var(--font-mono)',
                    }}>
                        404
                    </div>

                    <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--gray-100)', marginBottom: '0.75rem' }}>
                        Page Not Found
                    </h1>

                    <p style={{ color: 'var(--gray-400)', fontSize: '0.9rem', lineHeight: '1.6', marginBottom: '2rem' }}>
                        The route you are looking for doesn&apos;t exist or may have moved. Return to the workspace overview to explore your projects.
                    </p>

                    <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="btn btn-primary"
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.75rem 1.5rem',
                            fontSize: '0.9rem',
                            margin: '0 auto',
                        }}
                    >
                        <ArrowLeft size={16} /> Return to Overview
                    </button>
                </GlassCard>
            </motion.div>
        </div>
    );
}
