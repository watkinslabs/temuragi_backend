class AppInitializer {
    constructor(urls) {
        this.health_check_interval = window.health_check_interval || 10000;

        // Store config in window.app
        window.app.config = {
            login_url: urls.login_url,
            validate_url: urls.validate_url,
            refresh_url: urls.refresh_url,
            logout_url: urls.logout_url,
            status_url: urls.status_url,
            health_endpoint: urls.health_endpoint,
            login_page_path: urls.login_page_path,
            api_url:urls.api_url
        };

        // Self-register
        window.app.register('initializer', this);
        window.showToast = function(message, type = 'info', duration = 3000) {
            // Map types to Bootstrap classes
            const type_map = {
                'success': 'bg-success text-white',
                'error': 'bg-danger text-white',
                'warning': 'bg-warning',
                'info': 'bg-info text-white'
            };

            const toast_html = `
                <div class="toast align-items-center ${type_map[type] || ''} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;

            // Create container if needed
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container position-fixed top-0 end-0 p-3';
                container.style.zIndex = '1000';
                document.body.appendChild(container);
            }

            // Add toast to container
            const toast_element = document.createElement('div');
            toast_element.innerHTML = toast_html;
            container.appendChild(toast_element);

            // Initialize Bootstrap toast
            const toast = new bootstrap.Toast(toast_element.firstElementChild, {
                autohide: true,
                delay: duration
            });

            // Show toast
            toast.show();

            // Clean up after hidden
            toast_element.firstElementChild.addEventListener('hidden.bs.toast', () => {
                toast_element.remove();
            });
        };
    }

    async init() {
        console.log('Starting app initialization...');

        // Create instances - they self-register to window.app
        new TokenManager();
        new ApiManager();

        new AuthManager(window.app.token_manager, window.app.config);

        new ConnectionMonitor({
            health_endpoint: window.app.config.health_endpoint,
            check_interval: this.health_check_interval,
            max_consecutive_failures: 1
        });

        // Set cross-references
        window.app.connection_monitor.set_token_manager(window.app.token_manager);
        window.app.connection_monitor.set_auth_manager(window.app.auth_manager);
        window.app.auth_manager.set_connection_monitor(window.app.connection_monitor);

        // START THE CONNECTION MONITOR - THIS WAS MISSING!
        window.app.connection_monitor.start();

        // Add convenience methods to window.app
        window.app.logout = () => window.app.auth_manager.logout();
        window.app.check_auth_status = () => window.app.auth_manager.check_status();

        // Check if we're on login page
        const is_login_page = window.location.pathname === window.app.config.login_page_path;

        if (!is_login_page) {
            const auth_success = await window.app.auth_manager.init();
            document.getElementById('auth-loading').classList.add('hidden');
            if (auth_success) {
                document.getElementById('app-content').style.display = 'block';
            }
        } else {
            document.getElementById('auth-loading').classList.add('hidden');
            document.getElementById('app-content').style.display = 'block';
        }

        this.setup_htmx_indicators();
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
            if (evt.detail.target) {
                htmx.process(evt.detail.target);
                const tables = evt.detail.target.querySelectorAll('.dataTable');
                tables.forEach(table => {
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
            if (evt.detail.target) {
                htmx.process(evt.detail.target);
            }
        });
    }

    setup_visibility_handler() {
        document.addEventListener('visibilitychange', async () => {
            // Fix: use window.app.auth_manager instead of this.auth_manager
            if (!document.hidden && window.app.auth_manager && window.app.auth_manager.validation_interval) {
                const is_valid = await window.app.auth_manager.validate_tokens();
                if (!is_valid) {
                    window.app.auth_manager.redirect_to_login();
                }
            }
        });
    }

}