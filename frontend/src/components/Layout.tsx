import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    Home,
    FolderCode,
    Terminal,
    Search,
    Plus,
    Globe,
    Database,
    Key,
    X,
    Menu,
    FileCheck,
    GitCompare,
} from 'lucide-react';
import type { TabType } from '../types';
import { useWorkspace } from '../context/WorkspaceContext';

interface LayoutProps {
    children: React.ReactNode;
    activeTab?: TabType;
    onTabChange?: (tab: TabType) => void;
    onNewProject?: () => void;
    endpointCount?: number;
    onApiKeyClick?: () => void;
    hasApiKey?: boolean;
    isAuthEnabled?: boolean;
    searchQuery?: string;
    onSearchChange?: (query: string) => void;
}

export default function Layout({
    children,
    activeTab: propActiveTab,
    onTabChange,
    onNewProject: propNewProject,
    endpointCount: propEndpointCount,
    onApiKeyClick: propApiKeyClick,
    hasApiKey: propHasApiKey,
    isAuthEnabled: propIsAuthEnabled,
    searchQuery: propSearchQuery,
    onSearchChange: propSearchChange,
}: LayoutProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const workspace = useWorkspace();
    const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

    // Close mobile nav on route change
    useEffect(() => {
        setIsMobileNavOpen(false);
    }, [location.pathname]);

    // Determine active tab from prop or URL
    const pathSegment = location.pathname.slice(1).split('/')[0] as TabType;
    const activeTab: TabType = propActiveTab || (
        ['endpoints', 'databases', 'playground', 'results', 'tests', 'changes'].includes(pathSegment)
            ? pathSegment
            : 'overview'
    );

    const searchQuery = propSearchQuery ?? workspace.searchQuery;
    const handleSearchChange = propSearchChange ?? workspace.setSearchQuery;
    const handleNewProject = propNewProject ?? (() => workspace.setIsCreateModalOpen(true));
    const handleApiKeyClick = propApiKeyClick ?? (() => workspace.setIsApiKeyModalOpen(true));
    const hasApiKey = propHasApiKey ?? workspace.hasApiKey;
    const isAuthEnabled = propIsAuthEnabled ?? workspace.isAuthEnabled;
    const endpointCount = propEndpointCount ?? (workspace.selectedProject?.spec?.endpoints?.length || 0);

    const menuItems: { icon: typeof Home; label: string; id: TabType; path: string }[] = [
        { icon: Home, label: 'Overview', id: 'overview', path: '/' },
        { icon: Globe, label: 'Endpoints', id: 'endpoints', path: '/endpoints' },
        { icon: Database, label: 'Databases', id: 'databases', path: '/databases' },
        { icon: Terminal, label: 'Playground', id: 'playground', path: '/playground' },
        { icon: FolderCode, label: 'Results', id: 'results', path: '/results' },
        { icon: FileCheck, label: 'Tests', id: 'tests', path: '/tests' },
        { icon: GitCompare, label: 'Change Monitor', id: 'changes', path: '/changes' },
    ];

    const handleMenuClick = (item: typeof menuItems[0]) => {
        if (onTabChange) {
            onTabChange(item.id);
        }
        if (location.pathname !== item.path) {
            navigate(item.path);
        }
        setIsMobileNavOpen(false);
    };

    const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);
    const shortcutLabel = isMac ? '⌘K' : 'Ctrl K';

    return (
        <div style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: 'var(--bg-main)', color: 'var(--gray-100)', overflow: 'hidden' }}>
            {/* Desktop Sidebar */}
            <div
                className="desktop-sidebar"
                style={{
                    width: '260px',
                    height: '100%',
                    backgroundColor: 'var(--bg-sidebar)',
                    borderRight: '1px solid var(--surface-base-border)',
                    flexDirection: 'column',
                    padding: '1.5rem 1rem',
                }}
            >
                <div
                    onClick={() => navigate('/')}
                    style={{
                        padding: '0 0.5rem 2rem 0',
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                    }}
                >
                    <img src="/logo.svg" alt="Doc2SDK" style={{ height: '56px', width: 'auto' }} />
                </div>

                <nav aria-label="Desktop Main Menu" style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.7rem', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '1rem 0.5rem 0.5rem' }}>
                        Main Menu
                    </p>
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isCurrent = activeTab === item.id;
                        return (
                            <button
                                key={item.id}
                                type="button"
                                onClick={() => handleMenuClick(item)}
                                aria-current={isCurrent ? 'page' : undefined}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.75rem',
                                    width: '100%',
                                    padding: '0.75rem 1rem',
                                    borderRadius: '8px',
                                    border: isCurrent ? '1px solid var(--accent-primary)' : '1px solid transparent',
                                    cursor: 'pointer',
                                    color: isCurrent ? 'var(--gray-100)' : 'var(--gray-300)',
                                    backgroundColor: isCurrent ? 'var(--accent-primary-muted)' : 'transparent',
                                    transition: 'all 0.2s ease',
                                    marginBottom: '0.25rem',
                                    textAlign: 'left',
                                }}
                            >
                                <Icon size={20} color={isCurrent ? 'var(--accent-primary)' : 'currentColor'} />
                                <span style={{ fontSize: '0.875rem', fontWeight: '500', flex: 1 }}>{item.label}</span>
                                {item.id === 'endpoints' && endpointCount > 0 && (
                                    <span style={{
                                        fontSize: '0.7rem',
                                        backgroundColor: isCurrent ? 'var(--accent-primary)' : 'var(--gray-700)',
                                        color: isCurrent ? '#0F0F10' : 'var(--gray-300)',
                                        padding: '0.1rem 0.5rem',
                                        borderRadius: '10px',
                                        fontWeight: '700',
                                    }}>
                                        {endpointCount}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Mobile Sidebar Overlay & Drawer */}
            {isMobileNavOpen && (
                <>
                    <div
                        className="mobile-nav-backdrop"
                        onClick={() => setIsMobileNavOpen(false)}
                        aria-hidden="true"
                    />
                    <div
                        className="mobile-sidebar-drawer"
                        role="dialog"
                        aria-label="Mobile navigation"
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', padding: '0 0.5rem' }}>
                            <img src="/logo.svg" alt="Doc2SDK" style={{ height: '44px', width: 'auto' }} />
                            <button
                                type="button"
                                onClick={() => setIsMobileNavOpen(false)}
                                aria-label="Close navigation"
                                style={{ background: 'none', border: 'none', color: 'var(--gray-400)', cursor: 'pointer', padding: '4px' }}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <nav aria-label="Mobile Menu" style={{ flex: 1 }}>
                            {menuItems.map((item) => {
                                const Icon = item.icon;
                                const isCurrent = activeTab === item.id;
                                return (
                                    <button
                                        key={item.id}
                                        type="button"
                                        onClick={() => handleMenuClick(item)}
                                        aria-current={isCurrent ? 'page' : undefined}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.75rem',
                                            width: '100%',
                                            padding: '0.85rem 1rem',
                                            borderRadius: '8px',
                                            border: isCurrent ? '1px solid var(--accent-primary)' : '1px solid transparent',
                                            cursor: 'pointer',
                                            color: isCurrent ? 'var(--gray-100)' : 'var(--gray-300)',
                                            backgroundColor: isCurrent ? 'var(--accent-primary-muted)' : 'transparent',
                                            marginBottom: '0.35rem',
                                            textAlign: 'left',
                                        }}
                                    >
                                        <Icon size={20} color={isCurrent ? 'var(--accent-primary)' : 'currentColor'} />
                                        <span style={{ fontSize: '0.9rem', fontWeight: '500', flex: 1 }}>{item.label}</span>
                                        {item.id === 'endpoints' && endpointCount > 0 && (
                                            <span style={{
                                                fontSize: '0.7rem',
                                                backgroundColor: isCurrent ? 'var(--accent-primary)' : 'var(--gray-700)',
                                                color: isCurrent ? '#0F0F10' : 'var(--gray-300)',
                                                padding: '0.1rem 0.5rem',
                                                borderRadius: '10px',
                                                fontWeight: '700',
                                            }}>
                                                {endpointCount}
                                            </span>
                                        )}
                                    </button>
                                );
                            })}
                        </nav>
                    </div>
                </>
            )}

            {/* Main Content Area */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {/* Top Header */}
                <header style={{
                    height: '64px',
                    background: 'var(--surface-base-bg)',
                    backdropFilter: 'var(--surface-base-blur)',
                    WebkitBackdropFilter: 'var(--surface-base-blur)',
                    borderBottom: '1px solid var(--surface-base-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0 1.5rem',
                    position: 'sticky',
                    top: 0,
                    zIndex: 10,
                    gap: '1rem',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, maxWidth: '400px' }}>
                        <button
                            type="button"
                            className="mobile-menu-toggle"
                            onClick={() => setIsMobileNavOpen(true)}
                            aria-label="Open navigation menu"
                        >
                            <Menu size={22} />
                        </button>

                        <div style={{ position: 'relative', width: '100%' }}>
                            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--gray-500)', pointerEvents: 'none' }} />
                            <input
                                id="global-search-input"
                                type="text"
                                placeholder="Search projects, SDKs, docs..."
                                value={searchQuery ?? ''}
                                onChange={(e) => handleSearchChange(e.target.value)}
                                aria-label="Global search projects and documentation"
                                style={{
                                    width: '100%',
                                    padding: '0.5rem 4rem 0.5rem 2.5rem',
                                    backgroundColor: 'var(--bg-card)',
                                    border: '1px solid var(--gray-700)',
                                    borderRadius: '8px',
                                    color: 'var(--gray-100)',
                                    fontSize: '0.85rem',
                                    outline: 'none',
                                }}
                            />
                            {searchQuery ? (
                                <button
                                    type="button"
                                    onClick={() => handleSearchChange('')}
                                    aria-label="Clear search"
                                    style={{
                                        position: 'absolute',
                                        right: '10px',
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        background: 'none',
                                        border: 'none',
                                        color: 'var(--gray-500)',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        padding: '2px',
                                        borderRadius: '4px',
                                    }}
                                    title="Clear search"
                                >
                                    <X size={14} />
                                </button>
                            ) : (
                                <span className="search-shortcut-badge">{shortcutLabel}</span>
                            )}
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <button
                            type="button"
                            onClick={handleApiKeyClick}
                            aria-label={hasApiKey ? 'API Key Active' : 'Configure API Key'}
                            style={{
                                height: '36px',
                                padding: '0 0.85rem',
                                borderRadius: '8px',
                                background: hasApiKey ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-card)',
                                color: hasApiKey ? '#10B981' : 'var(--gray-300)',
                                border: hasApiKey ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid var(--gray-700)',
                                fontWeight: '500',
                                fontSize: '0.8rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.4rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                whiteSpace: 'nowrap',
                            }}
                            title="Configure Doc2SDK API Key"
                        >
                            <Key size={15} />
                            <span>{hasApiKey ? 'API Key Active' : (isAuthEnabled ? 'Set API Key' : 'API Key')}</span>
                        </button>
                        <button
                            type="button"
                            onClick={handleNewProject}
                            aria-label="Create new project"
                            style={{
                                height: '36px',
                                padding: '0 1rem',
                                borderRadius: '8px',
                                background: 'linear-gradient(135deg, #F5A623 0%, #E09410 100%)',
                                color: '#0F0F10',
                                border: 'none',
                                fontWeight: '600',
                                fontSize: '0.85rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.4rem',
                                cursor: 'pointer',
                                boxShadow: '0 4px 14px rgba(245, 166, 35, 0.3)',
                                whiteSpace: 'nowrap',
                            }}
                        >
                            <Plus size={16} /> <span>New Project</span>
                        </button>
                    </div>
                </header>

                <main style={{ flex: 1, overflowY: 'auto', padding: '1.5rem 2rem' }}>
                    {children}
                </main>
            </div>
        </div>
    );
}
