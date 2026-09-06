interface MethodBadgeProps {
    method: string;
    className?: string;
}

export default function MethodBadge({ method, className = '' }: MethodBadgeProps) {
    const normalized = (method || 'GET').toLowerCase();
    return (
        <span className={`method-badge ${normalized} ${className}`}>
            {method?.toUpperCase() || 'GET'}
        </span>
    );
}
