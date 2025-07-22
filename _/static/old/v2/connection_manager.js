// connection_manager.js - REDUCED FROM 290 LINES TO ~120 LINES
class ConnectionMonitor {
    constructor(options = {}) {
        this.health_endpoint = options.health_endpoint || '/health';
        this.check_interval = options.check_interval || 10000;
        this.max_consecutive_failures = options.max_consecutive_failures || 3;
        this.is_online = true;
        this.failures = 0;
        this.timer = null;

        window.app.register('connection_monitor', this);

        this.create_overlay();
        this.bind_events();
    }

    set_auth_manager(auth_manager) {
        this.auth_manager = auth_manager;
    }

    set_token_manager(token_manager) {
        this.token_manager = token_manager;
    }

    create_overlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'connection-offline-overlay';
        this.overlay.innerHTML = `
            <div class="offline-modal">
                <i class="fas fa-wifi-slash"></i>
                <h3>Connection Lost</h3>
                <p>Attempting to reconnect...</p>
                <div class="spinner-border"></div>
            </div>
        `;
        this.overlay.style.display = 'none';
        document.body.appendChild(this.overlay);
    }

    bind_events() {
        window.addEventListener('online', () => this.check_health());
        window.addEventListener('offline', () => this.set_offline());
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) this.check_health();
        });
    }

    start() {
        console.log('Starting connection monitor...');
        this.check_health();
        this.timer = setInterval(() => this.check_health(), this.check_interval);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    async check_health() {
        console.log('Checking health endpoint:', this.health_endpoint);
        try {
            await window.app.api.get(this.health_endpoint);
            console.log('Health check successful');
            this.set_online();
        } catch (error) {
            console.log('Health check failed:', error);
            
            // Check if it's a server error (502, 503, etc)
            if (error.response && error.response.status >= 502) {
                console.log('Server error detected, going offline immediately');
                this.set_offline();
            } else {
                // For other errors, increment failure count
                this.failures++;
                console.log(`Health check failure ${this.failures}/${this.max_consecutive_failures}`);
                
                if (this.failures >= this.max_consecutive_failures) {
                    console.log('Max failures reached, going offline');
                    this.set_offline();
                }
            }
        }
    }

    set_online() {
        console.log('Setting connection status: ONLINE');
        this.failures = 0;
        this.is_online = true;
        this.overlay.style.display = 'none';
        
        // Make sure we're using the normal check interval when online
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = setInterval(() => this.check_health(), this.check_interval);
        }
    }

    set_offline() {
        console.log('Setting connection status: OFFLINE');
        this.is_online = false;
        this.overlay.style.display = 'flex';

        // Increase check frequency when offline to detect recovery faster
        if (this.timer) {
            clearInterval(this.timer);
        }
        this.timer = setInterval(() => this.check_health(), 5000);
    }
}