export class SafeStorage {
    static setItem(key: string, value: any): boolean {
        try {
            const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
            localStorage.setItem(key, stringValue);
            return true;
        } catch (e: any) {
            if (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
                console.warn(`Storage quota exceeded for key: ${key}. Attempting to clean up...`);
                return this.handleQuotaExceeded(key, value);
            }
            console.error('Storage error:', e);
            return false;
        }
    }

    static getItem<T>(key: string, defaultValue: T): T {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Error reading from storage:', e);
            return defaultValue;
        }
    }

    private static handleQuotaExceeded(key: string, value: any): boolean {
        if (key === 'ag_projects' && Array.isArray(value)) {
            // Strategy 1: Truncate existing projects even further
            const truncatedValue = value.map(p => ({
                ...p,
                sdk_code: p.sdk_code?.length > 500 ? p.sdk_code.substring(0, 500) + "\n... (Truncated due to storage limits) ..." : p.sdk_code,
                spec: {
                    ...p.spec,
                    endpoints: p.spec?.endpoints?.slice(0, 5).map((e: any) => ({
                        method: e.method,
                        path: e.path,
                        summary: e.summary
                    })) || [],
                    truncated: true
                }
            }));

            try {
                localStorage.setItem(key, JSON.stringify(truncatedValue));
                console.info("Successfully saved truncated projects to storage.");
                return true;
            } catch (retryError) {
                // Strategy 2: Remove oldest projects
                if (truncatedValue.length > 1) {
                    console.warn("Truncation not enough, removing oldest project.");
                    return this.handleQuotaExceeded(key, truncatedValue.slice(0, -1));
                }
            }
        }

        // If it's not ag_projects or we still can't save, just fail
        return false;
    }

    static clearProjects() {
        localStorage.removeItem('ag_projects');
    }
}
