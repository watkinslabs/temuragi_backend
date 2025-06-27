// connection_manager.js - REDUCED FROM 290 LINES TO ~120 LINES
class ConnectionMonitor {
    constructor(options = {}) {
        this.health_endpoint = options.health_endpoint || '/health';
        this.check_interval = options.check_interval || 10000;
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
        this.overlay.id = 'connection-offline-overlay';
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
        try {
            await window.app.api.get(this.health_endpoint);
            this.set_online();
        } catch (error) {
            if (error.response?.status >= 502) {
                this.set_offline();
            } else if (++this.failures >= 3) {
                this.set_offline();
            }
        }
    }

    set_online() {
        this.failures = 0;
        this.is_online = true;
        this.overlay.style.display = 'none';
    }

    set_offline() {
        this.is_online = false;
        this.overlay.style.display = 'flex';
        
        // Keep trying to reconnect
        if (!this.timer) {
            this.timer = setInterval(() => this.check_health(), 5000);
        }
    }
}