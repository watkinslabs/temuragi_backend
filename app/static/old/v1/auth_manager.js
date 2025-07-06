// Authentication Manager Class
class AuthManager {
    constructor(token_manager, options = {}) {
        this.token_manager = token_manager;
        this.connection_monitor = null;
        
        this.options = {
            validation_frequency: options.validation_frequency || 60000,
            login_url: options.login_url,
            validate_url: options.validate_url,
            refresh_url: options.refresh_url ,
            logout_url: options.logout_url ,
            status_url: options.status_url 
        };
        
        this.is_validating = false;
        this.validation_interval = null;
    }
    
    set_connection_monitor(connection_monitor) {
        this.connection_monitor = connection_monitor;
    }
    
    async init() {
        console.log('Initializing authentication...');
        
        // Check if we have tokens
        if (!this.token_manager.has_tokens()) {
            console.log('No tokens found - redirecting to login');
            this.redirect_to_login();
            return false;
        }
        
        // Validate tokens
        const is_valid = await this.validate_tokens();
        if (!is_valid) {
            this.redirect_to_login();
            return false;
        }
        
        // Start continuous validation
        this.start_continuous_validation();
        
        // Configure HTMX headers
        this.configure_htmx();
        
        // Start connection monitoring
        if (this.connection_monitor) {
            this.connection_monitor.start_monitoring();
        }
        
        console.log('Authentication initialized successfully');
        return true;
    }
    
    async validate_tokens() {
        if (this.is_validating) return false;
        
        this.is_validating = true;
        const tokens = this.token_manager.get_tokens();
        
        try {
            const response = await fetch(this.options.validate_url, {
                headers: {
                    'Authorization': `Bearer ${tokens.api_token}`
                }
            });
            
            if (!response.ok) {
                console.log('Token validation failed with status:', response.status);
                return false;
            }
            
            const data = await response.json();
            
            // Update user info if provided
            if (data.user_info) {
                this.token_manager.set_user_info(data.user_info);
            }
            
            // Check if token is expiring soon (less than 5 minutes)
            if (data.token_info && data.token_info.expires_in < 300) {
                console.log('Token expiring soon, attempting refresh...');
                await this.refresh_token();
            }
            
            return true;
            
        } catch (error) {
            console.error('Token validation error:', error);
            return false;
        } finally {
            this.is_validating = false;
        }
    }
    
    async refresh_token() {
        const tokens = this.token_manager.get_tokens();
        
        try {
            const response = await fetch(this.options.refresh_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrf_token
                },
                body: JSON.stringify({
                    refresh_token: tokens.refresh_token
                })
            });
            
            if (!response.ok) {
                console.log('Token refresh failed with status:', response.status);
                return false;
            }
            
            const data = await response.json();
            
            // Update stored access token
            this.token_manager.update_api_token(data.api_token);
            
            console.log('Token refreshed successfully');
            return true;
            
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }
    
    start_continuous_validation() {
        // Clear any existing interval
        if (this.validation_interval) {
            clearInterval(this.validation_interval);
        }
        
        // Validate tokens periodically
        this.validation_interval = setInterval(async () => {
            console.log('Running periodic token validation...');
            const is_valid = await this.validate_tokens();
            
            if (!is_valid) {
                // Try to refresh token
                const refreshed = await this.refresh_token();
                if (!refreshed) {
                    console.log('Session expired - redirecting to login');
                    this.stop_continuous_validation();
                    this.redirect_to_login();
                }
            }
        }, this.options.validation_frequency);
    }
    
    stop_continuous_validation() {
        if (this.validation_interval) {
            clearInterval(this.validation_interval);
            this.validation_interval = null;
        }
        
        if (this.connection_monitor) {
            this.connection_monitor.stop_monitoring();
        }
    }
    
    configure_htmx() {
        document.body.addEventListener('htmx:configRequest', (evt) => {
            const tokens = this.token_manager.get_tokens();
            if (tokens.api_token) {
                evt.detail.headers['Authorization'] = `Bearer ${tokens.api_token}`;
            }
            evt.detail.headers['X-CSRF-Token'] = csrf_token;
        });
        
        // Handle 401 responses
        document.body.addEventListener('htmx:responseError', async (evt) => {
            if (evt.detail.xhr.status === 401) {
                console.log('401 error - attempting token refresh');
                
                const refreshed = await this.refresh_token();
                if (refreshed) {
                    // Retry the original request
                    htmx.trigger(evt.detail.elt, evt.detail.triggeringEvent);
                } else {
                    // Refresh failed - redirect to login
                    this.redirect_to_login();
                }
            }
        });
    }
    
    
    redirect_to_login() {
        if (this.connection_monitor && !this.connection_monitor.is_online) {
            console.log('Cannot redirect to login while offline');
            return;
        }
        
        this.stop_continuous_validation();
        this.token_manager.clear_tokens();
        window.location.href = this.options.login_url;
    }
    
    
    async handle_auth_failure() {
        // Don't redirect if we're offline
        if (this.connection_monitor && !this.connection_monitor.is_online) {
            console.log('Auth failure while offline - skipping redirect');
            return;
        }
        
        // Try to refresh token
        const refreshed = await this.refresh_token();
        if (!refreshed) {
            this.redirect_to_login();
        }
    }
    
    async logout() {
        console.log('Starting logout process...');
        
        // Stop validation timer
        this.stop_continuous_validation();
        
        try {
            const tokens = this.token_manager.get_tokens();
            
            // Call logout endpoint to revoke tokens on server
            if (tokens.api_token || tokens.user_id) {
                await fetch(this.options.logout_url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrf_token
                    },
                    body: JSON.stringify({
                        access_token: tokens.api_token,
                        user_id: tokens.user_id
                    })
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
            // Continue with logout even if server request fails
        }
        
        // Clear all auth data
        this.token_manager.clear_tokens();
        
        // Redirect to login page
        window.location.href = this.options.login_url;
    }
    
    async check_status() {
        const tokens = this.token_manager.get_tokens();
        
        if (!tokens.api_token) {
            return { authenticated: false };
        }
        
        try {
            const response = await fetch(this.options.status_url, {
                headers: {
                    'Authorization': `Bearer ${tokens.api_token}`
                }
            });
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('Auth status check error:', error);
            return { authenticated: false };
        }
    }
}
