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

    // Wrap fetch to check for CSRF invalid
    apiCall: async (url, options = {}) => {
        const response = await fetch(url, options);
        
        // Check for CSRF invalid
        if (!response.ok) {
            const content_type = response.headers.get('content-type');
            if (content_type && content_type.includes('application/json')) {
                const data = await response.json();
                
                if (data.success === false && data.csrf_invalid === true) {
                    console.log('CSRF invalid - clearing auth and reloading');
                    
                    // Clear everything
                    localStorage.removeItem('api_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_id');
                    localStorage.removeItem('user_info');
                    localStorage.removeItem('default_context');
                    sessionStorage.clear();
                    
                    // Just reload the page - the app will show login since auth is cleared
                    window.location.reload();
                    
                    // Return the response anyway
                    return response;
                }
                
                // Re-create response since we consumed it
                return new Response(JSON.stringify(data), {
                    status: response.status,
                    statusText: response.statusText,
                    headers: response.headers
                });
            }
        }
        
        return response;
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