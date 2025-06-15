// Token Manager Class
class TokenManager {
    constructor() {
        this.storage_keys = {
            api_token: 'api_token',
            refresh_token: 'refresh_token',
            user_uuid: 'user_uuid',
            user_info: 'user_info'
        };
    }
    
    get_tokens() {
        return {
            api_token: localStorage.getItem(this.storage_keys.api_token),
            refresh_token: localStorage.getItem(this.storage_keys.refresh_token),
            user_uuid: localStorage.getItem(this.storage_keys.user_uuid)
        };
    }
    
    set_tokens(api_token, refresh_token, user_uuid) {
        if (api_token) localStorage.setItem(this.storage_keys.api_token, api_token);
        if (refresh_token) localStorage.setItem(this.storage_keys.refresh_token, refresh_token);
        if (user_uuid) localStorage.setItem(this.storage_keys.user_uuid, user_uuid);
    }
    
    update_api_token(api_token) {
        localStorage.setItem(this.storage_keys.api_token, api_token);
    }
    
    set_user_info(user_info) {
        localStorage.setItem(this.storage_keys.user_info, JSON.stringify(user_info));
    }
    
    get_user_info() {
        const info = localStorage.getItem(this.storage_keys.user_info);
        return info ? JSON.parse(info) : null;
    }
    
    clear_tokens() {
        Object.values(this.storage_keys).forEach(key => {
            localStorage.removeItem(key);
        });
    }
    
    has_tokens() {
        const tokens = this.get_tokens();
        return !!(tokens.api_token && tokens.refresh_token && tokens.user_uuid);
    }
}

// Connection Monitor Class
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
            if (tokens.api_token || tokens.user_uuid) {
                await fetch(this.options.logout_url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrf_token
                    },
                    body: JSON.stringify({
                        access_token: tokens.api_token,
                        user_uuid: tokens.user_uuid
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

class DynamicDataTable {
    constructor(container_id, model_name, api_url, options = {}) {
        this.container_id = container_id;
        this.model_name = model_name;
        this.options = {
            page_length: 25,
            show_search: true,
            show_column_search: false,  // New option for column filtering
            show_create_button: true,
            columns: {},  // Changed from custom_columns
            excluded_columns: ['password_hash', 'created_by', 'updated_by', 'deleted_at'],
            column_order: [],  // Deprecated - kept for backward compatibility
            actions: ['edit', 'delete'],
            table_title: null,
            table_description: null,
            create_url: null,
            edit_url: null,
            api_url: api_url, 
            ...options
        };
        this.table = null;
        this.metadata = null;
        
        // Handle backward compatibility
        this._handle_backward_compatibility();
    }
    
    _handle_backward_compatibility() {
        // If column_order is provided but columns isn't fully configured
        if (this.options.column_order.length > 0 && Object.keys(this.options.columns).length === 0) {
            // Convert old format to new format
            this.options.column_order.forEach((col, index) => {
                this.options.columns[col] = {
                    order: index + 1,
                    searchable: true  // Default to searchable for backward compatibility
                };
            });
        }
    }
    
    _get_ordered_columns() {
        // Get columns sorted by order attribute
        return Object.entries(this.options.columns)
            .sort(([a, conf_a], [b, conf_b]) => {
                return (conf_a.order || 999) - (conf_b.order || 999);
            })
            .map(([name, config]) => ({ name, ...config }));
    }
    
    _get_searchable_columns() {
        // Get only columns marked as searchable
        return Object.entries(this.options.columns)
            .filter(([name, config]) => config.searchable === true)
            .map(([name]) => name);
    }
    
    
    api_request(data, callback) {
        $.ajax({
            url: this.options.api_url,
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'Authorization': 'Bearer ' + token_manager.get_tokens().api_token,
                'X-CSRF-Token': csrf_token
            },
            data: JSON.stringify(data),
            success: callback,
            error: (xhr, status, error) => {
                // Handle token expiration
                if (xhr.status === 401 && window.auth_manager) {
                    console.log('API request: Token expired, attempting refresh...');
                    window.auth_manager.handle_401_error().then(() => {
                        // Retry the request with new token
                        $.ajax({
                            url: this.options.api_url,
                            type: 'POST',
                            contentType: 'application/json',
                            headers: {
                                'Authorization': 'Bearer ' + token_manager.get_tokens().api_token,
                                'X-CSRF-Token': csrf_token
                            },
                            data: JSON.stringify(data),
                            success: callback,
                            error: (xhr, status, error) => {
                                console.error('API Error after retry:', error);
                                let message = 'API request failed';
                                if (xhr.responseJSON && xhr.responseJSON.message) {
                                    message = xhr.responseJSON.message;
                                }
                                this.show_notification(message, 'error');
                            }
                        });
                    }).catch(() => {
                        // Token refresh failed, user will be redirected to login
                        console.error('Token refresh failed');
                    });
                } else {
                    console.error('API Error:', error);
                    let message = 'API request failed';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        message = xhr.responseJSON.message;
                    }
                    this.show_notification(message, 'error');
                }
            }
        });
    }
 
    // Notification helper method
    show_notification(message, type) {
        const toast = $(`
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);
        
        if (!$('.toast-container').length) {
            $('body').append('<div class="toast-container position-fixed top-0 end-0 p-3"></div>');
        }
        
        $('.toast-container').append(toast);
        toast.toast('show');
        
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    init() {
        // Build the HTML structure
        this.build_html();
        
        // Get metadata and initialize table
        this.get_metadata_and_init();
    }
    
    get_metadata_and_init() {
        this.api_request({
            model: this.model_name,
            operation: 'metadata'
        }, (response) => {
            if (response.success && response.metadata) {
                this.metadata = response.metadata;
                this._process_metadata();
                this.init_datatable();
            }
        });
    }
    
    _process_metadata() {
        // If no columns specified, auto-generate from metadata
        if (Object.keys(this.options.columns).length === 0) {
            let order = 1;
            this.metadata.columns.forEach(col => {
                if (!this.options.excluded_columns.includes(col.name)) {
                    this.options.columns[col.name] = {
                        order: order++,
                        searchable: col.type !== 'boolean',  // Auto-disable search for booleans
                        type: col.type,
                        label: col.label || col.name
                    };
                }
            });
        } else {
            // Enrich configured columns with metadata
            this.metadata.columns.forEach(col => {
                if (this.options.columns[col.name]) {
                    this.options.columns[col.name].type = col.type;
                    this.options.columns[col.name].label = this.options.columns[col.name].label || col.label || col.name;
                }
            });
        }
    }
    
    build_html() {
        const container = $(`#${this.container_id}`);
        const title = this.options.table_title || `${this.model_name} Management`;
        const description = this.options.table_description || `Manage ${this.model_name.toLowerCase()} records`;
        
        let html = `
            <!-- Header -->
            <div class="row header-bar text-white mb-4">
                <div class="col">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h4 class="mb-0 fw-bold">
                                <i class="fas fa-table me-2"></i>${title}
                            </h4>
                            <small style="opacity: 0.9;">${description}</small>
                        </div>
        `;
        
        if (this.options.show_create_button) {
            html += `
                        <div>
                            <button class="btn btn-light text-dark fw-medium" id="${this.model_name.toLowerCase()}_create_btn">
                                <i class="fas fa-plus me-2"></i>New ${this.model_name}
                            </button>
                        </div>
            `;
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
        
        if (this.options.show_search) {
            html += `
            <!-- Search Bar -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <input type="text" id="${this.model_name.toLowerCase()}_search" 
                        class="form-control" placeholder="Search ${this.model_name.toLowerCase()}s...">
                </div>
            </div>
            `;
        }
        
        html += `
            <!-- Table -->
            <div class="row">
                <div class="col">
                    <div class="card">
                        <div class="card-body">
                            <table id="${this.model_name.toLowerCase()}_table" 
                                class="table table-hover" style="width:100%">`;
        
        if (this.options.show_column_search) {
            html += `
                                <tfoot>
                                    <tr>
                                        ${/* Footers will be added by DataTable init */''}
                                    </tr>
                                </tfoot>`;
        }
        
        html += `
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.html(html);
        
        const style = `
            <style>
                /* Table container styling */
                #${this.container_id} .dataTables_wrapper {
                    min-height: 400px;
                }
                
                /* Empty row styling */
                #${this.container_id} tr.empty-row {
                    height: 53px; /* Match your normal row height */
                }
                
                #${this.container_id} tr.empty-row:hover {
                    background-color: transparent !important;
                    cursor: default;
                }
                
                #${this.container_id} tr.empty-row td {
                    border-bottom: 1px solid var(--theme-border-color);
                    padding: 12px;
                }
                
                /* DataTables v2 Pagination Styling */
                #${this.container_id} .dt-paging {
                    margin: 15px 0;
                }
                
                #${this.container_id} .dt-paging nav {
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 2px;
                }
                
                #${this.container_id} .dt-paging-button {
                    color: var(--theme-text);
                    background-color: var(--theme-background);
                    border: 1px solid var(--theme-border-color);
                    padding: 0.375rem 0.75rem;
                    margin: 0 1px;
                    border-radius: var(--theme-button-border-radius);
                    transition: all var(--theme-transition-duration) var(--theme-animation-easing);
                    font-size: 0.875rem;
                    line-height: 1.5;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                }
                
                #${this.container_id} .dt-paging-button:hover:not(.disabled) {
                    color: var(--theme-primary);
                    background-color: var(--theme-surface);
                    border-color: var(--theme-primary);
                    text-decoration: none;
                }
                
                #${this.container_id} .dt-paging-button.current {
                    background-color: var(--theme-primary);
                    border-color: var(--theme-primary);
                    color: white;
                }
                
                #${this.container_id} .dt-paging-button.disabled {
                    color: var(--theme-text-muted);
                    background-color: var(--theme-background);
                    border-color: var(--theme-border-color);
                    cursor: not-allowed;
                    opacity: 0.65;
                }
                
                /* Ellipsis styling */
                #${this.container_id} .dt-paging .ellipsis {
                    padding: 0 5px;
                    color: var(--theme-text-muted);
                }
                
                /* Empty table message styling */
                #${this.container_id} .dataTables_empty {
                    padding: 80px 20px;
                    text-align: center;
                    color: var(--theme-text-muted);
                    font-size: 1.2rem;
                    background-color: var(--theme-surface);
                    border-radius: var(--theme-border-radius);
                }
                
                /* Table styling */
                #${this.container_id} .table {
                    margin-bottom: 0;
                }
                
                /* Top controls row styling */
                #${this.container_id} .dt-container > .row:first-child {
                    margin-bottom: 15px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid var(--theme-border-color);
                    align-items: center;
                }
                
                /* Bottom info and pagination row */
                #${this.container_id} .dt-info {
                    padding-top: 8px;
                    color: var(--theme-text-muted);
                    margin-bottom: 10px;
                }
                
                /* Length select styling */
                #${this.container_id} .dt-length {
                    display: flex;
                    align-items: center;
                }
                
                #${this.container_id} .dt-length select {
                    width: auto;
                    display: inline-block;
                    margin: 0 5px;
                    padding: 0.25rem 0.5rem;
                    font-size: 0.875rem;
                    line-height: 1.5;
                    color: var(--theme-text);
                    background-color: var(--theme-background);
                    border: 1px solid var(--theme-border-color);
                    border-radius: var(--theme-input-border-radius);
                }
                
                #${this.container_id} .dt-length label {
                    margin-bottom: 0;
                    display: flex;
                    align-items: center;
                    font-size: 0.875rem;
                    color: var(--theme-text);
                }
                
                /* Fix the NaN button issue */
                #${this.container_id} .dt-paging-button[data-dt-idx="NaN"] {
                    display: none !important;
                }
                
                /* Processing indicator */
                #${this.container_id} .dt-processing {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 200px;
                    margin-left: -100px;
                    margin-top: -26px;
                    text-align: center;
                    padding: var(--theme-spacing-unit);
                    background-color: var(--theme-background);
                    border: var(--theme-border-width) solid var(--theme-border-color);
                    border-radius: var(--theme-border-radius);
                    box-shadow: var(--theme-shadow-lg);
                    z-index: 1000;
                }
                
                /* Table row hover */
                #${this.container_id} .table-hover tbody tr:hover:not(.empty-row) {
                    background-color: var(--theme-surface);
                }
                
                /* Focus states */
                #${this.container_id} .dt-paging-button:focus {
                    outline: none;
                    box-shadow: 0 0 0 var(--theme-focus-ring-width) var(--theme-focus-ring-color);
                }
                
                #${this.container_id} .dt-length select:focus {
                    outline: none;
                    border-color: var(--theme-primary);
                    box-shadow: 0 0 0 var(--theme-focus-ring-width) var(--theme-focus-ring-color);
                }
            </style>
        `;
        
        if (!$(`#${this.container_id}_styles`).length) {
            $('head').append(`<div id="${this.container_id}_styles">${style}</div>`);
        }
        
        // Bind create button if exists
        if (this.options.show_create_button) {
            $(`#${this.model_name.toLowerCase()}_create_btn`).on('click', () => {
                if (this.options.create_url) {
                    window.location.href = this.options.create_url;
                }
            });
        }
    }
    
    init_datatable() {
        const ordered_columns = this._get_ordered_columns();
        const searchable_columns = this._get_searchable_columns();
        
        // Build column definitions for DataTable
        const column_defs = ordered_columns.map(col => ({
            data: col.name,
            name: col.name,
            title: col.label || col.name,
            searchable: col.searchable || false,
            orderable: col.orderable !== false,  // Default to true
            render: this._get_column_renderer(col)
        }));
        
        // Add actions column if needed
        if (this.options.actions.length > 0) {
            column_defs.push({
                data: null,
                title: 'Actions',
                searchable: false,
                orderable: false,
                className: 'text-center',
                render: (data, type, row) => this._render_actions(row)
            });
        }
        
        // Initialize DataTable
        this.table = $(`#${this.model_name.toLowerCase()}_table`).DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                url: this.options.api_url,
                type: 'POST',
                contentType: 'application/json',
                beforeSend: function(xhr) {
                    // Set headers dynamically before each request
                    xhr.setRequestHeader('Authorization', 'Bearer ' + token_manager.get_tokens().api_token);
                    xhr.setRequestHeader('X-CSRF-Token', csrf_token);
                },
                data: (d) => {
                    const all_columns = ordered_columns.map((col, index) => ({
                        data: col.name,
                        name: col.name,
                        searchable: col.searchable || false,
                        orderable: col.orderable !== false,
                        search: {
                            value: '',
                            regex: false
                        }
                    }));
                    
                    // Add actions column if present
                    if (this.options.actions.length > 0) {
                        all_columns.push({
                            data: null,
                            name: 'actions',
                            searchable: false,
                            orderable: false,
                            search: {
                                value: '',
                                regex: false
                            }
                        });
                    }
                    
                    // Extract just the column names to return
                    const return_columns = ordered_columns.map(col => col.name);
                    
                    // Only send searchable column names for search operations
                    const request_data = {
                        model: this.model_name,
                        operation: 'list',
                        draw: d.draw,
                        start: d.start,
                        length: d.length,
                        search: d.search.value,
                        order: d.order,
                        columns: all_columns,  // Send ALL columns info
                        return_columns: return_columns,  // Which columns to return in the data
                        searchable_columns: searchable_columns  // Which columns to search on
                    };
                    
                    // Debug logging
                    if (d.search.value) {
                        console.log('Search request:', d.search.value, 'on columns:', searchable_columns);
                    }
                    
                    return JSON.stringify(request_data);
                },
                dataSrc: (response) => {
                    // Fix the recordsTotal and recordsFiltered if they're missing
                    if (response.recordsTotal === undefined) {
                        response.recordsTotal = response.data ? response.data.length : 0;
                    }
                    if (response.recordsFiltered === undefined) {
                        response.recordsFiltered = response.recordsTotal;
                    }
                    return response.data || [];
                },
                error: (xhr, error, thrown) => {
                    // Handle token expiration
                    if (xhr.status === 401) {
                        console.log('DataTable: Token expired, attempting refresh...');
                        if (window.auth_manager) {
                            window.auth_manager.handle_401_error().then(() => {
                                // Reload the table after token refresh
                                this.table.ajax.reload();
                            });
                        }
                    }
                }
            },
            columns: column_defs,
            pageLength: this.options.page_length,
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"p>>rtip',  // Pagination at top and bottom
            language: {
                emptyTable: `No ${this.model_name.toLowerCase()} records found`,
                zeroRecords: `No matching ${this.model_name.toLowerCase()} records found`,
                processing: `<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Loading ${this.model_name.toLowerCase()} data...`,
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "Showing 0 to 0 of 0 entries",
                infoFiltered: "(filtered from _MAX_ total entries)"
            },
            paging: true,
            deferRender: true,
            initComplete: () => {
                this._setup_search();
                this._setup_column_search();
                // Add small delay to ensure table is fully rendered
                setTimeout(() => {
                    this._ensure_min_rows();
                }, 100);
            },
            drawCallback: () => {
                // Always ensure minimum rows after each draw
                setTimeout(() => {
                    this._ensure_min_rows();
                }, 50);
            }
        });
    }

    _ensure_min_rows() {
        const MIN_ROWS = 5;  // Always show at least 5 rows
        const tbody = $(`#${this.model_name.toLowerCase()}_table tbody`);
        const current_rows = tbody.find('tr').not('.empty-row').length;  // Don't count existing empty rows
        
        // Remove any existing empty rows first
        tbody.find('tr.empty-row').remove();
        
        // Calculate how many empty rows we need
        const empty_rows_needed = Math.max(0, MIN_ROWS - current_rows);
        
        // Add empty rows if needed
        if (empty_rows_needed > 0) {
            const col_count = this.table.columns().count();
            for (let i = 0; i < empty_rows_needed; i++) {
                const empty_row = $('<tr class="empty-row"></tr>');
                for (let j = 0; j < col_count; j++) {
                    empty_row.append('<td>&nbsp;</td>');
                }
                tbody.append(empty_row);
            }
        }
    }
    
    _get_column_renderer(col) {
        // Return custom renderer based on column type or format
        if (col.format === 'date' || col.type === 'datetime') {
            return (data) => {
                if (!data) return '';
                const date = new Date(data);
                return date.toLocaleDateString();
            };
        }
        
        if (col.format === 'boolean' || col.type === 'boolean') {
            return (data) => {
                return data ? 
                    '<span class="badge bg-success">Yes</span>' : 
                    '<span class="badge bg-secondary">No</span>';
            };
        }
        
        // Custom renderer if provided
        if (col.render) {
            return col.render;
        }
        
        // Default renderer
        return (data) => data || '';
    }
    
    _render_actions(row) {
        let actions_html = '<div class="btn-group btn-group-sm">';
        
        this.options.actions.forEach(action => {
            if (typeof action === 'string') {
                // Standard actions
                switch (action) {
                    case 'edit':
                        actions_html += `
                            <button class="btn btn-primary" onclick="window.${this.model_name.toLowerCase()}_table.handle_action('edit', '${row.uuid}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>`;
                        break;
                    case 'delete':
                        actions_html += `
                            <button class="btn btn-danger" onclick="window.${this.model_name.toLowerCase()}_table.handle_action('delete', '${row.uuid}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>`;
                        break;
                    case 'copy':
                        actions_html += `
                            <button class="btn btn-secondary" onclick="window.${this.model_name.toLowerCase()}_table.handle_action('copy', '${row.uuid}')" title="Copy">
                                <i class="fas fa-copy"></i>
                            </button>`;
                        break;
                }
            } else if (typeof action === 'object') {
                // Custom actions
                actions_html += `
                    <button class="btn btn-${action.color || 'secondary'}" 
                        onclick="window.${this.model_name.toLowerCase()}_table.handle_action('${action.name}', '${row.uuid}')" 
                        title="${action.title || action.name}">
                        <i class="${action.icon}"></i>
                    </button>`;
            }
        });
        
        actions_html += '</div>';
        return actions_html;
    }
    
    _setup_search() {
        // Setup custom search box if exists
        const search_input = $(`#${this.model_name.toLowerCase()}_search`);
        if (search_input.length) {
            // Remove any existing event handlers
            search_input.off('keypress');
            
            // Only search on Enter key
            search_input.on('keypress', (e) => {
                if (e.which === 13) { // Enter key
                    e.preventDefault();
                    this.table.search(search_input.val()).draw();
                }
            });
            
            // Optional: Add a clear button or handle Escape key
            search_input.on('keydown', (e) => {
                if (e.which === 27) { // Escape key
                    e.preventDefault();
                    search_input.val('');
                    this.table.search('').draw();
                }
            });
        }
    }
    
    _setup_column_search() {
        if (!this.options.show_column_search) return;
        
        // Add footer inputs for searchable columns
        const footer = $(`#${this.model_name.toLowerCase()}_table tfoot tr`);
        footer.empty();
        
        this.table.columns().every(function() {
            const column = this;
            const is_searchable = column.settings()[0].aoColumns[column.index()].bSearchable;
            
            if (is_searchable) {
                const input = $('<input type="text" class="form-control form-control-sm" placeholder="Search...">')
                    .on('keyup change clear', function() {
                        if (column.search() !== this.value) {
                            column.search(this.value).draw();
                        }
                    });
                $('<th>').append(input).appendTo(footer);
            } else {
                $('<th>').appendTo(footer);
            }
        });
    }
    
    handle_action(action, uuid) {
        // Check for custom handlers first
        if (this.options.custom_handlers && this.options.custom_handlers[action]) {
            this.options.custom_handlers[action](uuid);
            return;
        }
        
        // Default handlers
        switch (action) {
            case 'edit':
                if (this.options.edit_url) {
                    window.location.href = this.options.edit_url.replace('{uuid}', uuid);
                }
                break;
                
            case 'delete':
                if (confirm(`Are you sure you want to delete this ${this.model_name}?`)) {
                    this.api_request({
                        model: this.model_name,
                        operation: 'delete',
                        uuid: uuid
                    }, (response) => {
                        if (response.success) {
                            this.show_notification(`${this.model_name} deleted successfully`, 'success');
                            this.table.ajax.reload();
                        }
                    });
                }
                break;
                
            case 'copy':
                this.api_request({
                    model: this.model_name,
                    operation: 'copy',
                    uuid: uuid
                }, (response) => {
                    if (response.success) {
                        this.show_notification(`${this.model_name} copied successfully`, 'success');
                        this.table.ajax.reload();
                    }
                });
                break;
        }
    }
}