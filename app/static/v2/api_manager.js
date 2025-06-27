// api_manager.js
class ApiManager {
    constructor() {
        this.base_headers = {
            'Content-Type': 'application/json'
        };
        this.interceptors = {
            request: [],
            response: [],
            error: []
        };
        window.app.register('api', this);
    }

    async request(url, options = {}) {
        // Build headers
        const headers = {
            ...this.base_headers,
            ...this.get_auth_headers(),
            ...options.headers
        };

        // Run request interceptors
        for (const interceptor of this.interceptors.request) {
            options = await interceptor(u1rl, options) || options;
        }

        try {
            // Build fetch options
            const fetch_options = {
                method: options.method || 'POST',
                headers
            };

            // Only add body if there is one and method isn't GET/HEAD
            if (options.body !== undefined && !['GET', 'HEAD'].includes(fetch_options.method)) {
                fetch_options.body = JSON.stringify(options.body);
            }

            const response = await fetch(url, fetch_options);
            const data = await response.json();

            // Run response interceptors
            for (const interceptor of this.interceptors.response) {
                await interceptor(response, data);
            }

            if (!response.ok) {
                throw { response, data };
            }

            return data;

        } catch (error) {
            // Run error interceptors
            for (const interceptor of this.interceptors.error) {
                const handled = await interceptor(error);
                if (handled) return handled;
            }
            throw error;
        }
    }

    get_auth_headers() {
        const headers = {};

        // Use window.app instead of window
        if (window.app.token_manager) {
            const tokens = window.app.token_manager.get_tokens();
            if (tokens.api_token) {
                headers.Authorization = `Bearer ${tokens.api_token}`;
            }
        }

        const csrf_token = document.querySelector('meta[name="csrf-token"]')?.content || window.csrf_token;
        if (csrf_token) {
            headers['X-CSRF-Token'] = csrf_token;
        }

        return headers;
    }

    on_request(fn) {
        this.interceptors.request.push(fn);
    }

    on_response(fn) {
        this.interceptors.response.push(fn);
    }

    on_error(fn) {
        this.interceptors.error.push(fn);
    }

    // Convenience methods
    get(url, params) {
        const query = params ? '?' + new URLSearchParams(params) : '';
        return this.request(url + query, { method: 'GET' });
    }

    post(url, body) {
        return this.request(url, { method: 'POST', body: body });
    }
}