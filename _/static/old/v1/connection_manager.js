class ConnectionMonitor {
    constructor(options = {}) {
        this.options = {
            health_endpoint: options.health_endpoint || '/health',
            check_interval: options.check_interval || 10000,
            retry_interval: options.retry_interval || 5000,
            max_consecutive_failures: options.max_consecutive_failures || 3
        };
        
        this.is_online = true;
        this.consecutive_failures = 0;
        this.health_check_timer = null;
        this.reconnect_timer = null;
        this.overlay = null;
        this.auth_manager = null;
        this.token_manager = null;
        
        this.init();
    }
    
    set_auth_manager(auth_manager) {
        this.auth_manager = auth_manager;
    }
    
    set_token_manager(token_manager) {
        this.token_manager = token_manager;
    }
    
    init() {
        this.create_overlay();
        this.bind_events();
    }
    
    create_overlay() {
        // Create overlay element
        const overlay = document.createElement('div');
        overlay.id = 'connection-offline-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 10000;
            display: none;
            align-items: center;
            justify-content: center;
        `;
        
        overlay.innerHTML = `
            <div style="
                background: var(--theme-surface-dark);
                border: var(--theme-border-width) solid var(--theme-border-color-dark);
                padding: 3rem;
                border-radius: var(--theme-card-border-radius);
                box-shadow: var(--theme-shadow-lg);
                text-align: center;
                max-width: 450px;
            ">
                <div style="
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 1.5rem;
                    background: var(--theme-danger);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <i class="fas fa-wifi-slash" style="font-size: 2.5rem; color: white;"></i>
                </div>
                <h3 style="
                    color: var(--theme-text-dark);
                    font-family: var(--theme-font-heading);
                    font-weight: var(--theme-font-weight-bold);
                    margin-bottom: 1rem;
                    font-size: 1.75rem;
                ">Connection Lost</h3>
                <p style="
                    color: var(--theme-text-muted-dark);
                    font-family: var(--theme-font-primary);
                    margin-bottom: 2rem;
                    font-size: 1.125rem;
                ">Unable to reach the server. Attempting to reconnect...</p>
                <div class="spinner-border" style="
                    color: var(--theme-primary-dark);
                    width: 2.5rem;
                    height: 2.5rem;
                    border-width: 0.25rem;
                    margin-bottom: 1.5rem;
                " role="status">
                    <span class="visually-hidden">Reconnecting...</span>
                </div>
                <p style="
                    color: var(--theme-text-muted-dark);
                    font-size: 0.875rem;
                    margin: 0;
                ">
                    <span id="reconnect-status">Checking connection...</span>
                </p>
            </div>
        `;
        
        document.body.appendChild(overlay);
        this.overlay = overlay;
    }
    
    
    set_online() {
        this.is_online = true;
        this.overlay.style.display = 'none';
        document.body.style.overflow = '';
        console.log('Connection restored');
    }

    set_offline() {
        this.is_online = false;
        this.overlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        console.log('Connection lost');
    }
    
    bind_events() {
        // Browser online/offline events
        window.addEventListener('online', () => this.handle_online());
        window.addEventListener('offline', () => this.handle_offline());
        
        // Visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.is_online) {
                this.check_health();
            }
        });
    }
    
    start_monitoring() {
        // Initial check
        this.check_health();
        
        // Set up periodic checking
        this.health_check_timer = setInterval(() => {
            this.check_health();
        }, this.options.check_interval);
    }
    
    stop_monitoring() {
        if (this.health_check_timer) {
            clearInterval(this.health_check_timer);
            this.health_check_timer = null;
        }
        if (this.reconnect_timer) {
            clearInterval(this.reconnect_timer);
            this.reconnect_timer = null;
        }
    }
    
    async check_health() {
        console.log('Checking health...');
        
        const timeout_promise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), 5000)
        );
        
        const fetch_promise = fetch(this.options.health_endpoint, {
            method: 'GET',
            headers: {
                'Authorization': this.token_manager?.get_tokens()?.api_token ? 
                    `Bearer ${this.token_manager.get_tokens().api_token}` : '',
                'X-CSRF-Token': csrf_token
            }
        });
        
        try {
            const response = await Promise.race([fetch_promise, timeout_promise]);
            console.log('Health check response:', response.status);
            
            if (response.ok) {
                this.handle_health_success();
            } else {
                this.handle_health_failure(response.status);
            }
        } catch (error) {
            console.log('Health check error:', error.message);
            this.handle_health_failure(0);
        }
    }

    handle_health_success() {
        this.consecutive_failures = 0;
        
        if (!this.is_online) {
            this.set_online();
            
            // Stop reconnection attempts
            if (this.reconnect_timer) {
                clearInterval(this.reconnect_timer);
                this.reconnect_timer = null;
            }
            
            // Resume normal monitoring
            this.start_monitoring();
        }
    }
    
    
    handle_health_failure(status) {
        this.consecutive_failures++;
        
        // Handle auth failures
        if (status === 401 || status === 403) {
            // Only handle auth failure if we're online
            if (this.auth_manager && this.is_online) {
                this.auth_manager.handle_auth_failure();
            }
            return;
        }
        
        // Handle server errors immediately (502, 503, 504, etc)
        if (status >= 502 && status <= 504) {
            console.log(`Server error ${status} - going offline immediately`);
            if (this.is_online) {
                this.set_offline();
                this.start_reconnection_attempts();
            }
            return;
        }
        
        // Show offline after enough failures
        if (this.consecutive_failures >= this.options.max_consecutive_failures && this.is_online) {
            this.set_offline();
            this.start_reconnection_attempts();
        }
    }

    
    start_reconnection_attempts() {
        let attempt = 0;
        
        // Stop regular monitoring
        if (this.health_check_timer) {
            clearInterval(this.health_check_timer);
            this.health_check_timer = null;
        }
        
        // Update status immediately
        this.update_reconnect_status('Attempting to reconnect...');
        
        // Start reconnection attempts
        this.reconnect_timer = setInterval(() => {
            attempt++;
            this.update_reconnect_status(`Reconnection attempt ${attempt}...`);
            this.check_health();
        }, this.options.retry_interval);
    }
    
    update_reconnect_status(message) {
        const status_element = document.getElementById('reconnect-status');
        if (status_element) {
            status_element.textContent = message;
        }
    }
    
    handle_online() {
        console.log('Browser reports online');
        if (!this.is_online) {
            this.check_health();
        }
    }
    
    handle_offline() {
        console.log('Browser reports offline');
        this.set_offline();
        this.start_reconnection_attempts();
    }
}
