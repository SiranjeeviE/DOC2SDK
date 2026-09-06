import type { LucideIcon } from 'lucide-react';
import GlassCard from '../GlassCard';

interface EmptyStateProps {
    icon: LucideIcon;
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
}

export default function EmptyState({
    icon: Icon,
    title,
    description,
    actionLabel,
    onAction,
}: EmptyStateProps) {
    return (
        <GlassCard style={{ textAlign: 'center', padding: '4rem 2rem', maxWidth: '640px', margin: '2rem auto' }}>
            <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '16px',
                background: 'var(--accent-primary-muted)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1.5rem',
            }}>
                <Icon size={32} />
            </div>
            <h3 style={{ fontSize: '1.35rem', color: 'var(--gray-100)', marginBottom: '0.5rem' }}>{title}</h3>
            <p style={{ color: 'var(--gray-400)', fontSize: '0.9rem', lineHeight: '1.6', maxWidth: '480px', margin: '0 auto 1.5rem' }}>
                {description}
            </p>
            {actionLabel && onAction && (
                <button type="button" onClick={onAction} className="btn btn-outline" style={{ padding: '0.6rem 1.25rem' }}>
                    {actionLabel}
                </button>
            )}
        </GlassCard>
    );
}
