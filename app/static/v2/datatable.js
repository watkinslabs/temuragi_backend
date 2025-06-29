class DynamicDataTable {
    constructor(container_id, model_name, report_name, api_url, options = {}) {
        this.container_id = container_id;
        this.model_name = model_name;
        this.options = {
            page_length: 25,
            show_search: true,
            show_column_search: false,  // New option for column filtering
            columns: {},  // Changed from custom_columns
            excluded_columns: ['password_hash', 'created_by', 'updated_by', 'deleted_at'],
            column_order: [],  // Deprecated - kept for backward compatibility
            actions: [],  // No default actions
            table_title: null,
            table_description: null,
            api_url: api_url, 
            ...options
        };
        this.table = null;
        this.metadata = null;
        this.report_name = report_name;
        
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
        this.get_metadata_and_init();
    }
    
    async get_metadata_and_init() {
        try {
            const response = await window.app.api.post(this.options.api_url, {
                model: this.model_name,
                operation: 'metadata'
            });

            if (response.success && response.metadata) {
                this.metadata = response.metadata;
                this._process_metadata();
                this.init_datatable();
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
        
        // Add page actions if any exist
        if (page_actions.length > 0) {
            html += '<div class="btn-group">';
            page_actions.forEach(action => {
                html += `
                    <a class="btn btn-${action.color || 'light'} text-${action.color === 'light' ? 'dark' : 'white'} fw-medium" 
                        id="${this.model_name.toLowerCase()}_${action.name}_btn"
                        hx-post="${action.url}"
                        hx-target="#main-content"
                        hx-swap="innerHTML"
                        hx-indicator=".htmx-indicator">
                        <i class="${action.icon} me-2"></i>${action.title || action.name}
                    </a>
                `;
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

        if (typeof htmx !== 'undefined') {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                console.log('Processing HTMX for table:', this.container_id);
                htmx.process(container[0]);
            }, 10);
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

                    // Build request data
                    const request_data = {
                        model: this.model_name,
                        operation: 'list',
                        draw: data.draw,
                        start: data.start,
                        length: data.length,
                        search: data.search.value,
                        order: data.order,
                        columns: all_columns,  // Send ALL columns info
                        return_columns: return_columns,  // Which columns to return in the data
                        searchable_columns: searchable_columns  // Which columns to search on
                    };

                    // Debug logging
                    if (data.search.value) {
                        console.log('Search request:', data.search.value, 'on columns:', searchable_columns);
                    }

                    // Use window.app.api instead of jQuery ajax
                    const response = await window.app.api.post(this.options.api_url, request_data);

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
        
        // Check for custom handler first
        if (action.handler && typeof action.handler === 'function') {
            action.handler(id);
            return;
        }
        
        // If action has a URL, use HTMX to trigger it
        if (action.url) {
            // Add confirmation for destructive actions
            if (action.confirm) {
                if (!confirm(action.confirm)) {
                    return;
                }
            }
            
            this.trigger_htmx_request({
                url: action.url,
                data: { id: id },
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
        } else {
            console.error(`Action '${action_name}' has no URL or handler defined`);
        }
    }
    
}