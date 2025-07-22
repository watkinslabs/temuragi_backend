// auth_manager.js
class AuthManager {
    constructor(token_manager, urls) {
        this.token_manager = token_manager;
        this.urls = urls;
        this.validation_interval = null;
        this.connection_monitor = null; // Add this

        // Self-register to window.app
        window.app.register('auth_manager', this);

        // Register 401 handler using window.app.api
        window.app.api.on_error(async (error) => {
            if (error.response?.status === 401) {
                if (error.data?.message == "Invalid or expired refresh token" || error.data?.success == false) {
                    // Refresh token is invalid - go straight to login
                    this.redirect_to_login();
                    return false;
                }
                const refreshed = await this.refresh_token();
                if (!refreshed) {
                    this.redirect_to_login();
                }
                return false;
            }
        });
    }

    set_connection_monitor(connection_monitor) {
        this.connection_monitor = connection_monitor;
    }

    async init() {
        if (!this.token_manager.has_tokens()) {
            this.redirect_to_login();
            return false;
        }

        if (!await this.validate_tokens()) {
            this.redirect_to_login();
            return false;
        }

        this.start_validation_timer();
        this.setup_htmx();
        return true;
    }

    async validate_tokens() {
        try {
            const data = await window.app.api.get(this.urls.validate_url);

            if (data.user_info) {
                this.token_manager.set_user_info(data.user_info);
            }

            if (data.token_info?.expires_in < 300) {
                await this.refresh_token();
            }

            return true;
        } catch {
            return false;
        }
    }

    async refresh_token() {
        try {
            const tokens = this.token_manager.get_tokens();
            const data = await window.app.api.post(this.urls.refresh_url, {
                refresh_token: tokens.refresh_token
            });

            this.token_manager.update_api_token(data.api_token);
            return true;
        } catch {
            return false;
        }
    }

    start_validation_timer() {
        this.validation_interval = setInterval(() => this.validate_tokens(), 60000);
    }

    stop() {
        if (this.validation_interval) {
            clearInterval(this.validation_interval);
        }
    }

    setup_htmx() {
        document.body.addEventListener('htmx:configRequest', (evt) => {
            Object.assign(evt.detail.headers, window.app.api.get_auth_headers()); // Fix: use window.app.api
        });
    }

    redirect_to_login(reason = 'token_expired') {
        this.stop();
        this.token_manager.clear_tokens();

        // Add reason to login URL
        const login_url = new URL(this.urls.login_url, window.location.origin);
        login_url.searchParams.set('reason', reason);

        window.location.href = login_url.toString();
    }

    async logout() {
        try {
            const tokens = this.token_manager.get_tokens();
            await window.app.api.post(this.urls.logout_url, {
                access_token: tokens.api_token,
                user_id: tokens.user_id
            });
        } catch {
            // Continue logout even if server fails
        }

        this.redirect_to_login('logout');
    }

    async check_status() {
        try {
            const response = await window.app.api.get(this.urls.status_url);
            return response;
        } catch (error) {
            console.error('Auth status check error:', error.message);
            return { authenticated: false };
        }
    }
}