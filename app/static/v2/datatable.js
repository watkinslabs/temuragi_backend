class DynamicDataTable {
    constructor(container_id, model_name, report_name, api_url, options = {}) {
        this.container_id = container_id;
        this.model_name = model_name;
        this.report_name = report_name;
        this.options = {
            page_length: 25,
            show_search: true,
            show_column_search: false,  // New option for column filtering
            columns: {},  // Changed from custom_columns
            excluded_columns: ['password_hash', 'created_by', 'updated_by', 'deleted_at'],
            actions: [],  // No default actions
            table_title: null,
            table_description: null,
            api_url: api_url,
            report_id: null,  // Now properly in options
            is_model: true,   // Default to true
            ...options
        };
        
        // Store these at instance level for easy access
        this.report_id = this.options.report_id;
        this.is_model = this.options.is_model;
        this.api_url = this.options.api_url;
        if ( this.is_model==false) this.model_name="ReportHandler";
        
        this.table = null;
        this.metadata = null;
    }
    
    // Centralized API request method
    async make_api_request(operation, additional_data = {}) {
        const base_data = {
            model: this.model_name,
            operation: operation
        };
        
        // Always include report_id and is_model if they exist
        if (this.report_id !== null) {
            base_data.report_id = this.report_id;
        }
        if (this.is_model !== null) {
            base_data.is_model = this.is_model;
        }
        
        // Merge with any additional data
        const request_data = {
            ...base_data,
            ...additional_data
        };
        
        try {
            const response = await window.app.api.post(this.api_url, request_data);
            return response;
        } catch (error) {
            console.error(`API request failed for operation '${operation}':`, error);
            throw error;
        }
    }
    
    _get_ordered_columns() {
        // Get columns sorted by order attribute
        return Object.entries(this.options.columns)
            .sort(([a, conf_a], [b, conf_b]) => {
                return (conf_a.order_index || 999) - (conf_b.order_index || 999);
            })
            .map(([name, config]) => ({ name, ...config }));
    }
    
    _get_searchable_columns() {
        // Get only columns marked as searchable
        return Object.entries(this.options.columns)
            .filter(([name, config]) => config.searchable === true)
            .map(([name]) => name);
    }
    
    _get_page_actions() {
        // Get actions with mode='page' (default to 'row' if not specified)
        return this.options.actions.filter(action => action.mode === 'page');
    }
    
    _get_row_actions() {
        // Get actions with mode='row' or no mode specified (default)
        return this.options.actions.filter(action => !action.mode || action.mode === 'row');
    }

    show_notification(message, type) {
        // Use the real toast system
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // Fallback to console if toast system not available
            console[type === 'error' ? 'error' : 'log'](`[${type}] ${message}`);
        }
    }

    init() {
        // Build the HTML structure
        this.build_html();
        
        // Get metadata and initialize table
        //this.get_metadata_and_init();
        this.init_datatable();
    }
    
    async get_metadata_and_init() {
        try {
            const response = await this.make_api_request('metadata');

            if (response.success && response.metadata) {
                this.metadata = response.metadata;
                this._process_metadata();
                this.init_datatable();
            } else {
                throw new Error(response.error || 'No metadata received');
            }
        } catch (error) {
            console.error('Failed to get metadata:', error);
            this.show_notification('Failed to load table metadata', 'error');
        }
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
        const page_actions = this._get_page_actions();
    
        let html = `
            <!-- Header -->
            <div class="row mb-4">
                <div class="col">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h4 class="mb-0 fw-bold">
                                <i class="fas fa-table me-2"></i>${title}
                            </h4>
                            <small class="text-body-secondary">${description}</small>
                        </div>
        `;
    
        // Add page actions if any exist
        if (page_actions.length > 0) {
            html += '<div class="btn-group">';
            page_actions.forEach(action => {
                const action_type = action.action_type || 'htmx';
                
                // Different rendering based on action type
                if (action_type === 'htmx') {
                    // Original HTMX button
                    html += `
                        <a class="btn btn-${action.color || 'secondary'}"
                            id="${this.model_name.toLowerCase()}_${action.name}_btn"
                            hx-post="${action.url}"
                            hx-target="#main-content"
                            hx-swap="innerHTML"
                            hx-indicator=".htmx-indicator">
                            <i class="${action.icon} me-2"></i>${action.title || action.name}
                        </a>
                    `;
                } else {
                    // API or JavaScript button - use onclick
                    html += `
                        <button class="btn btn-${action.color || 'secondary'}"
                            id="${this.model_name.toLowerCase()}_${action.name}_btn"
                            onclick="window.${this.report_name.toLowerCase()}.handle_action('${action.name}', null)">
                            <i class="${action.icon} me-2"></i>${action.title || action.name}
                        </button>
                    `;
                }
            });
            html += '</div>';
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
    
        // Minimal DataTables-specific styles only
        const style = `
            <style>
                /* DataTables minimum height */
                #${this.container_id} .dataTables_wrapper {
                    min-height: 400px;
                }
                
                /* Empty row styling */
                #${this.container_id} tr.empty-row {
                    height: 53px;
                }
    
                #${this.container_id} tr.empty-row:hover {
                    background-color: transparent !important;
                    cursor: default;
                }
    
                /* DataTables pagination */
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
                
                /* Style DataTables buttons like Bootstrap pagination */
                #${this.container_id} .dt-paging-button {
                    position: relative;
                    display: block;
                    padding: 0.375rem 0.75rem;
                    margin-left: -1px;
                    line-height: 1.25;
                    color: var(--bs-link-color);
                    text-decoration: none;
                    background-color: var(--bs-body-bg);
                    border: 1px solid var(--bs-border-color);
                }
                
                #${this.container_id} .dt-paging-button:hover {
                    z-index: 2;
                    color: var(--bs-link-hover-color);
                    background-color: var(--bs-secondary-bg);
                    border-color: var(--bs-border-color);
                }
                
                #${this.container_id} .dt-paging-button:first-child {
                    border-top-left-radius: var(--bs-border-radius);
                    border-bottom-left-radius: var(--bs-border-radius);
                }
                
                #${this.container_id} .dt-paging-button:last-child {
                    border-top-right-radius: var(--bs-border-radius);
                    border-bottom-right-radius: var(--bs-border-radius);
                }
                
                #${this.container_id} .dt-paging-button.current {
                    z-index: 3;
                    color: var(--bs-pagination-active-color);
                    background-color: var(--bs-pagination-active-bg);
                    border-color: var(--bs-pagination-active-border-color);
                }
                
                #${this.container_id} .dt-paging-button.disabled {
                    color: var(--bs-pagination-disabled-color);
                    pointer-events: none;
                    background-color: var(--bs-pagination-disabled-bg);
                    border-color: var(--bs-pagination-disabled-border-color);
                }
    
                /* Fix the NaN button issue */
                #${this.container_id} .dt-paging-button[data-dt-idx="NaN"] {
                    display: none !important;
                }
                
                /* DataTables info text */
                #${this.container_id} .dt-info {
                    padding-top: 8px;
                }
            </style>
        `;
    
        if (!$(`#${this.container_id}_styles`).length) {
            $('head').append(`<div id="${this.container_id}_styles">${style}</div>`);
        }
    
        // Only process HTMX for HTMX actions
        if (page_actions.some(action => (action.action_type || 'htmx') === 'htmx')) {
            if (typeof htmx !== 'undefined') {
                // Small delay to ensure DOM is ready
                setTimeout(() => {
                    console.log('Processing HTMX for table:', this.container_id);
                    htmx.process(container[0]);
                }, 10);
            }
        }
    }
    
    init_datatable() {
        const ordered_columns = this._get_ordered_columns();
        const searchable_columns = this._get_searchable_columns();
        const row_actions = this._get_row_actions();

        // Build column definitions for DataTable
        const column_defs = ordered_columns.map(col => ({
            data: col.name,
            name: col.name,
            title: col.label || col.name,
            searchable: col.searchable || false,
            orderable: col.orderable !== false,  // Default to true
            render: this._get_column_renderer(col)
        }));

        // Add actions column if row actions exist
        if (row_actions.length > 0) {
            column_defs.push({
                data: null,
                title: 'Actions',
                searchable: false,
                orderable: false,
                className: 'text-center',
                render: (data, type, row) => this._render_actions(row)
            });
        }

        // Initialize DataTable with custom ajax function
        this.table = $(`#${this.model_name.toLowerCase()}_table`).DataTable({
            processing: true,
            serverSide: true,
            ajax: async (data, callback, settings) => {
                try {
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
                    if (row_actions.length > 0) {
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

                    // Build request data using our centralized method
                    const response = await this.make_api_request('list', {
                        draw: data.draw,
                        start: data.start,
                        length: data.length,
                        search: data.search.value,
                        order: data.order,
                        columns: all_columns,
                        return_columns: return_columns,
                        searchable_columns: searchable_columns
                    });

                    // Debug logging
                    if (data.search.value) {
                        console.log('Search request:', data.search.value, 'on columns:', searchable_columns);
                    }

                    // Process the response
                    if (response.success) {
                        // Fix the recordsTotal and recordsFiltered if they're missing
                        if (response.recordsTotal === undefined) {
                            response.recordsTotal = response.data ? response.data.length : 0;
                        }
                        if (response.recordsFiltered === undefined) {
                            response.recordsFiltered = response.recordsTotal;
                        }

                        // Call the DataTable callback with the data
                        callback({
                            draw: response.draw || data.draw,
                            recordsTotal: response.recordsTotal,
                            recordsFiltered: response.recordsFiltered,
                            data: response.data || []
                        });
                    } else {
                        // Handle error response
                        console.error('DataTable API error:', response.error);
                        callback({
                            draw: data.draw,
                            recordsTotal: 0,
                            recordsFiltered: 0,
                            data: [],
                            error: response.error || 'Failed to load data'
                        });
                    }
                } catch (error) {
                    console.error('DataTable request failed:', error);
                    
                    // Check if it's a 401 error that needs token refresh
                    if (error.response?.status === 401) {
                        console.log('DataTable: Token expired, reloading...');
                        // The ApiManager should handle 401s automatically
                        // Just reload the table after a short delay
                        setTimeout(() => {
                            if (this.table) {
                                this.table.ajax.reload();
                            }
                        }, 1000);
                    }

                    // Return empty data to DataTable
                    callback({
                        draw: data.draw,
                        recordsTotal: 0,
                        recordsFiltered: 0,
                        data: [],
                        error: error.message || 'Failed to load data'
                    });
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
        const row_actions = this._get_row_actions();
        if (row_actions.length === 0) return '';
        
        let actions_html = '<div class="btn-group btn-group-sm">';
        
        row_actions.forEach(action => {
            actions_html += `
                <button class="btn btn-${action.color || 'secondary'}" 
                    onclick="window.${this.report_name.toLowerCase()}.handle_action('${action.name}', '${row.id}')" 
                    title="${action.title || action.name}">
                    <i class="${action.icon}"></i>
                </button>`;
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
    

    trigger_htmx_request(config) {
        const {
            url,
            data = {},
            target = '#main-content',
            swap = 'innerHTML',
            method = 'post',
            indicator = '.htmx-indicator',
            on_success = null,
            on_error = null
        } = config;

        // Create temporary element
        const temp_link = document.createElement('a');
        temp_link.setAttribute('hx-ext', 'json-enc');
        temp_link.setAttribute(`hx-${method}`, url);
        
        // Build the hx-vals string exactly like your code does
        const data_parts = [];
        for (const [key, value] of Object.entries(data)) {
            data_parts.push(`"${key}": "${value}"`);
        }
        temp_link.setAttribute('hx-vals', `{${data_parts.join(', ')}}`);
        
        temp_link.setAttribute('hx-target', target);
        temp_link.setAttribute('hx-swap', swap);
        temp_link.setAttribute('hx-indicator', indicator);
        
        // Add to DOM temporarily
        document.body.appendChild(temp_link);
        
        // Add event listeners to handle loading state
        temp_link.addEventListener('htmx:beforeRequest', function() {
            console.log(`${method.toUpperCase()} request starting:`, url);
            document.body.classList.add('htmx-loading');
        });
        
        temp_link.addEventListener('htmx:afterRequest', function() {
            console.log(`${method.toUpperCase()} request completed:`, url);
            document.body.classList.remove('htmx-loading');
            // Clean up the temporary element after request completes
            if (temp_link.parentNode) {
                document.body.removeChild(temp_link);
            }
            if (on_success) {
                on_success();
            }
        });
        
        temp_link.addEventListener('htmx:afterOnLoad', function() {
            console.log('Content loaded');
            document.body.classList.remove('htmx-loading');
            // Force cleanup of any loading indicators
            document.querySelectorAll('.htmx-loading').forEach(el => {
                el.classList.remove('htmx-loading');
            });
        });
        
        temp_link.addEventListener('htmx:responseError', function() {
            console.log(`${method.toUpperCase()} request error:`, url);
            document.body.classList.remove('htmx-loading');
            // Clean up on error
            if (temp_link.parentNode) {
                document.body.removeChild(temp_link);
            }
            if (on_error) {
                on_error();
            }
        });
        
        // Process with HTMX
        htmx.process(temp_link);
        
        // Trigger the request
        htmx.trigger(temp_link, 'click');
    }

    handle_action(action_name, id) {
        // Find the action configuration
        const action = this.options.actions.find(a => a.name === action_name);
    
        if (!action) {
            console.error(`Action '${action_name}' not found in configuration`);
            return;
        }
    
        // Add confirmation for any action type if needed
        if (action.confirm) {
            if (!confirm(action.confirm)) {
                return;
            }
        }
    
        // Route based on action type
        const action_type = action.action_type || 'htmx';  // Default to htmx
    
        switch (action_type) {
            case 'javascript':
                this.handle_javascript_action(action, id);
                break;
            
            case 'api':
                this.handle_api_action(action, id);
                break;
            
            case 'htmx':
            default:
                this.handle_htmx_action(action, id);
                break;
        }
    }
    
    handle_javascript_action(action, id) {
        // Execute custom JavaScript code
        if (action.javascript) {
            try {
                // Create a function with the code and execute it with context
                const func = new Function('id', 'row_data', 'table', 'action', action.javascript);
                
                // Get the row data if id exists
                let row_data = null;
                if (id) {
                    row_data = this.table.row(`#${id}`).data();
                }
                
                // Execute the function
                func.call(this, id, row_data, this.table, action);
            } catch (error) {
                console.error('Error executing JavaScript action:', error);
                this.show_notification('Error executing action', 'error');
            }
        } else {
            console.error('JavaScript action has no code defined');
        }
    }
    
    async handle_api_action(action, id) {
        if (!action.url) {
            console.error(`API action '${action.name}' has no URL defined`);
            return;
        }
    
        try {
            // For API actions, use a different endpoint - don't use make_api_request
            // as the action URL might be completely different
            const request_data = {
                id: id,
                model: this.model_name,  // Still include model info
                ...(action.payload || {})
            };
            
            // Include report_id if it exists
            if (this.report_id !== null) {
                request_data.report_id = this.report_id;
            }
    
            // Make the API call
            const method = (action.method || 'POST').toLowerCase();
            
            const response = await window.app.api[method](action.url, request_data, {
                headers: action.headers || {}
            });
            
            // Handle successful response
            if (response.success) {
                // Show success message
                const message = response.message || `${action.title || action.name} completed successfully`;
                this.show_notification(message, 'success');
                
                // Reload table data if needed
                if (response.reload_table !== false) {  // Default to reload
                    this.table.ajax.reload();
                }
                
                // Execute any callback in the response
                if (response.callback && typeof window[response.callback] === 'function') {
                    window[response.callback](response);
                }
            } else {
                // Show error message
                const error_message = response.error || response.message || `${action.title || action.name} failed`;
                this.show_notification(error_message, 'error');
            }
        } catch (error) {
            console.error('API action failed:', error);
            this.show_notification(`Failed to execute ${action.title || action.name}`, 'error');
        }
    }
    
    handle_htmx_action(action, id) {
        // Original HTMX handling
        if (!action.url) {
            console.error(`HTMX action '${action.name}' has no URL defined`);
            return;
        }
    
        // Build data object including report_id if it exists
        const htmx_data = { id: id };
        if (this.report_id !== null) {
            htmx_data.report_id = this.report_id;
        }
    
        this.trigger_htmx_request({
            url: action.url,
            data: htmx_data,
            method: action.method || 'post',
            on_success: () => {
                if (action.on_success) {
                    if (typeof action.on_success === 'function') {
                        action.on_success();
                    } else if (action.on_success === 'reload') {
                        this.table.ajax.reload();
                    }
                }
            },
            on_error: () => {
                if (action.on_error && typeof action.on_error === 'function') {
                    action.on_error();
                }
            }
        });
    }
    
    // Public method to reload table data
    reload() {
        if (this.table) {
            this.table.ajax.reload();
        }
    }
    
    // Public method to get selected row data
    get_selected_rows() {
        return this.table.rows('.selected').data().toArray();
    }
}