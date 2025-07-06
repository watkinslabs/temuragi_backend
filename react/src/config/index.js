// react/src/config/index.js
const config = {
    api: {
        base: '/v2/api',
        endpoints: {
            // Auth endpoints
            auth: {
                login: '/auth/login',
                logout: '/auth/logout',
                validate: '/auth/validate',
                refresh: '/auth/refresh',
                status: '/auth/status'
            },
            // Template endpoints
            templates: {
                get: '/templates/:slug'
            },
            // Route resolution
            routes: {
                resolve: '/routes/resolve',
                list: '/routes'
            },
            // Data endpoint
            data: '/data'
        }
    },
    
    // Build full URL from endpoint
    getUrl: (endpoint, params = {}) => {
        let url = `${config.api.base}${endpoint}`;
        
        // Replace URL parameters like :name
        Object.keys(params).forEach(key => {
            url = url.replace(`:${key}`, params[key]);
        });
        
        return url;
    },
    
    // Get auth headers
    getAuthHeaders: () => ({
        'Authorization': `Bearer ${localStorage.getItem('api_token') || ''}`,
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || '',
        'Content-Type': 'application/json'
    })
};

// Make it available globally if needed
window.appConfig = config;

export default config;