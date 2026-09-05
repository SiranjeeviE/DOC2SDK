import { useState, useMemo } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-bash';
import { Copy, Check, Code } from 'lucide-react';

interface CodeViewerProps {
    code: string;
    language?: 'python' | 'typescript' | 'json' | 'bash' | string;
    filename?: string;
    showLineNumbers?: boolean;
    maxHeight?: string;
    actions?: React.ReactNode;
}

export default function CodeViewer({
    code,
    language = 'python',
    filename,
    showLineNumbers = true,
    maxHeight = 'calc(100vh - 280px)',
    actions,
}: CodeViewerProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const highlightedHtml = useMemo(() => {
        const lang = language.toLowerCase();
        const grammar = Prism.languages[lang] || Prism.languages.python;
        return Prism.highlight(code, grammar, lang);
    }, [code, language]);

    const lines = useMemo(() => code.split('\n'), [code]);

    return (
        <div
            style={{
                display: 'flex',
                flexDirection: 'column',
                borderRadius: '12px',
                border: '1px solid var(--surface-base-border)',
                backgroundColor: 'var(--code-bg)',
                overflow: 'hidden',
                width: '100%',
            }}
        >
            {/* Header bar */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem 1.25rem',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Code size={16} color="var(--accent-primary)" />
                    {filename ? (
                        <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--gray-100)', fontFamily: 'var(--font-mono)' }}>
                            {filename}
                        </span>
                    ) : (
                        <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--accent-primary)', letterSpacing: '0.05em' }}>
                            {language}
                        </span>
                    )}
                    <span style={{ fontSize: '0.7rem', color: 'var(--gray-500)' }}>
                        {lines.length} lines · {(new Blob([code]).size / 1024).toFixed(1)} KB
                    </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {actions}
                    <button
                        type="button"
                        onClick={handleCopy}
                        aria-label="Copy code to clipboard"
                        className="btn btn-outline"
                        style={{
                            padding: '0.35rem 0.75rem',
                            fontSize: '0.75rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                        }}
                    >
                        {copied ? <Check size={13} color="var(--success)" /> : <Copy size={13} />}
                        {copied ? 'Copied' : 'Copy'}
                    </button>
                </div>
            </div>

            {/* Code Body with optional line numbers */}
            <div
                style={{
                    maxHeight,
                    overflowX: 'auto',
                    overflowY: 'auto',
                    display: 'flex',
                    fontSize: '0.85rem',
                    lineHeight: '1.6',
                    fontFamily: 'var(--font-mono)',
                    backgroundColor: 'var(--code-bg)',
                }}
            >
                {showLineNumbers && (
                    <div
                        aria-hidden="true"
                        style={{
                            userSelect: 'none',
                            padding: '1.25rem 0.75rem 1.25rem 1rem',
                            textAlign: 'right',
                            color: 'var(--gray-600)',
                            borderRight: '1px solid rgba(255, 255, 255, 0.05)',
                            backgroundColor: 'rgba(0, 0, 0, 0.2)',
                            minWidth: '42px',
                        }}
                    >
                        {lines.map((_, i) => (
                            <div key={i}>{i + 1}</div>
                        ))}
                    </div>
                )}

                <pre
                    tabIndex={0}
                    aria-label={`${language} code output`}
                    style={{
                        margin: 0,
                        padding: '1.25rem',
                        color: 'var(--gray-100)',
                        flex: 1,
                        whiteSpace: 'pre',
                        wordBreak: 'normal',
                        overflowX: 'auto',
                        outline: 'none',
                    }}
                >
                    <code dangerouslySetInnerHTML={{ __html: highlightedHtml }} />
                </pre>
            </div>
        </div>
    );
}
