// Token Manager Class

// Connection Monitor Class


class AppInitializer {
    constructor(urls) {
        this.token_manager = null;
        this.auth_manager = null;
        this.connection_monitor = null;
        this.health_check_interval = window.health_check_interval || 10000;
        
        // Store URLs
        this.urls = {
            login_url: urls.login_url,
            validate_url: urls.validate_url,
            refresh_url: urls.refresh_url,
            logout_url: urls.logout_url,
            status_url: urls.status_url,
            health_endpoint: urls.health_endpoint,
            login_page_path: urls.login_page_path
        };
    }
    
    async init() {
        // Create instances
        this.token_manager = new TokenManager();
        
        this.auth_manager = new AuthManager(this.token_manager, {
            login_url: this.urls.login_url,
            validate_url: this.urls.validate_url,
            refresh_url: this.urls.refresh_url,
            logout_url: this.urls.logout_url,
            status_url: this.urls.status_url
        });
        
        this.connection_monitor = new ConnectionMonitor({
            health_endpoint: this.urls.health_endpoint,
            check_interval: this.health_check_interval,
            max_consecutive_failures: 1
        });
        
        // Set cross-references
        this.connection_monitor.set_token_manager(this.token_manager);
        this.connection_monitor.set_auth_manager(this.auth_manager);
        this.auth_manager.set_connection_monitor(this.connection_monitor);
        
        // Expose globally for backwards compatibility
        window.token_manager = this.token_manager;
        window.auth_manager = this.auth_manager;
        window.connection_monitor = this.connection_monitor;
        
        // Global functions
        window.logout = () => this.auth_manager.logout();
        window.check_auth_status = () => this.auth_manager.check_status();
        
        // Check if we're on login page
        const is_login_page = window.location.pathname === this.urls.login_page_path;
        
        if (!is_login_page) {
            // Initialize authentication
            const auth_success = await this.auth_manager.init();
            
            // Hide loading screen
            document.getElementById('auth-loading').classList.add('hidden');
            
            if (auth_success) {
                // Show app content
                document.getElementById('app-content').style.display = 'block';
            }
            // If auth fails, init() will redirect to login
        } else {
            // On login page - just hide loader and show content
            document.getElementById('auth-loading').classList.add('hidden');
            document.getElementById('app-content').style.display = 'block';
        }
        
        // Set up HTMX loading indicators
        this.setup_htmx_indicators();
        
        // Set up visibility change handler
        this.setup_visibility_handler();
    }
    
    setup_htmx_indicators() {
        document.body.addEventListener('htmx:beforeRequest', function(evt) {
            document.body.classList.add('htmx-loading');
        });
        
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            document.body.classList.remove('htmx-loading');
        });
        
        // Process new content after HTMX swaps
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            console.log('afterSwap fired, target:', evt.detail.target);
            
            // Process the swapped content for new HTMX elements
            if (evt.detail.target) {
                console.log('Processing HTMX on:', evt.detail.target);
                htmx.process(evt.detail.target);
                
                // Also process any tables that might have been loaded
                const tables = evt.detail.target.querySelectorAll('.dataTable');
                tables.forEach(table => {
                    console.log('Found table:', table.id);
                    htmx.process(table.parentElement);
                });
            }
            
            // Handle nav active states if needed
            if (evt.detail.elt && evt.detail.elt.classList.contains('nav_item')) {
                document.querySelectorAll('.nav_item[aria-current="page"]').forEach(el => {
                    el.removeAttribute('aria-current');
                });
                evt.detail.elt.setAttribute('aria-current', 'page');
            }
        });
        
        // Also process after settle (when all animations are done)
        document.body.addEventListener('htmx:afterSettle', function(evt) {
            console.log('afterSettle fired');
            if (evt.detail.target) {
                htmx.process(evt.detail.target);
            }
        });
    }
    
    setup_visibility_handler() {
        document.addEventListener('visibilitychange', async () => {
            if (!document.hidden && this.auth_manager.validation_interval) {
                console.log('Tab became active - validating tokens');
                const is_valid = await this.auth_manager.validate_tokens();
                if (!is_valid) {
                    this.auth_manager.redirect_to_login();
                }
            }
        });
    }
}