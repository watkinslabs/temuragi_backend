class ReportBuilder {
    constructor(config) {
        this.actions = [];
        this.javascript_editor = null;
        
        // Map all URLs from config using snake_case
        this.urls = {
            data_api:                 config.data_api,
            execute_report:           config.execute_report,
            test_report:              config.test_report,
            preview_report:           config.preview_report,
            export_report:            config.export_report,
            get_report_permissions:   config.get_report_permissions,
            assign_report:            config.assign_report,
            validate_query:           config.validate_query,
            detect_variables:         config.detect_variables,
            list_report_templates:    config.list_report_templates,
            create_report_template:   config.create_report_template,
            update_report_template:   config.update_report_template,
            delete_report_template:   config.delete_report_template,
            test_connection:          config.test_connection,
            get_stats:                config.get_stats,
            export_report_definition: config.export_report_definition,
            import_report:            config.import_report,
            reorder_columns:          config.reorder_columns,
            validate_variables:       config.validate_variables,
            query_metadata:           config.query_metadata,
            analyze_columns:          config.analyze_columns,
            sync_columns:             config.sync_columns,
            analyze_query:            config.analyze_query,
            detect_column_types:      config.detect_column_types,
            suggest_column_settings:  config.suggest_column_settings
        };

        // Configuration
        this.report_id = config.report_id || null;
        this.is_edit_mode = !!this.report_id;

        // State
        this.query_editor = null;
        this.report_data = {
            report: null,
            columns: [],
            variables: [],
            data_types: {},
            variable_types: {},
            connections: [],
            templates: [],
            categories: [],
            pending_column_analysis: null // Store analysis results
        };

        // Separate tracking for server ids
        this.column_ids = {}; // Map column names to their server ids
        this.variable_ids = {}; // Map variable names to their server ids

        // Register this instance globally
        window.reportBuilder = this;

        // Initialize
        this.init();

        

        this.init_actions();

    }

    async init() {
        try {
            // Show loading overlay at start
            this.show_loading(true);
            
            // Initialize CodeMirror
            this.init_query_editor();

            // Load initial data - MUST complete before loading report
            await Promise.all([
                this.load_connections(),
                this.load_report_templates(),
                this.load_data_types(),
                this.load_variable_types(),
                this.load_models()  

            ]);

            // If editing, load existing report AFTER loading connections/templates
            if (this.is_edit_mode) {
                await this.load_existing_report();
            }

            // Load categories from existing reports
            await this.load_categories();

            // Setup event handlers
            this.setup_event_handlers();

            // Update save button text
            this.update_save_button_text();

            console.log('Report Builder initialized successfully');
            
            // Hide loading overlay when done
            this.show_loading(false);
        } catch (error) {
            console.error('Failed to initialize Report Builder:', error);
            this.show_error('Failed to initialize Report Builder: ' + error.message);
            // Make sure to hide loading on error too
            this.show_loading(false);
        }
    }

    show_loading(show) {
        if (show) {
            $('#loadingOverlay').show();
            // Also check for HTMX loading indicators
            if (window.htmx) {
                // Add htmx-request class to body to show HTMX loading indicator
                document.body.classList.add('htmx-request');
            }
        } else {
            $('#loadingOverlay').hide();
            // Remove HTMX loading indicators
            if (window.htmx) {
                document.body.classList.remove('htmx-request');
            }
            // Also remove any HTMX indicator elements that might be stuck
            $('.htmx-indicator').removeClass('htmx-request');
            $('[data-hx-indicator]').removeClass('htmx-request');
        }
    }

    init_query_editor() {
        // Initialize CodeMirror with proper settings
        this.query_editor = CodeMirror(document.getElementById('queryEditor'), {
            mode: 'text/x-sql',
            theme: 'monokai',
            lineNumbers: true,
            lineWrapping: true,
            value: 'SELECT * FROM temuragi.public.users',
            // Additional settings to fix display issues
            viewportMargin: Infinity,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: true,
            autofocus: false,
            gutters: ["CodeMirror-linenumbers"]
        });

        // Force refresh after a short delay to fix rendering issues
        setTimeout(() => {
            this.query_editor.refresh();
        }, 100);

        // Also refresh when the tab is shown (if using tabs)
        $('button[data-bs-toggle="pill"]').on('shown.bs.tab', (e) => {
            const target = $(e.target).attr('data-bs-target');
            if (target === '#query') {
                this.query_editor.refresh();
            }
        });
    }

    setup_event_handlers() {
        // Auto-generate slug from name
        $('#reportName').on('input', (e) => {
            if (!this.is_edit_mode) {
                const slug = $(e.target).val()
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/^-|-$/g, '');
                $('#reportSlug').val(slug);
            }
        });

        $('#reportModel').on('change', (e) => {
            const model_id = $(e.target).val();
            if (model_id && $('#isModel').is(':checked')) {
                console.log('Model selected:', model_id);
                this.load_model_query_with_confirmation(model_id);
            }
        });

        // Button click handlers
        $('#testQueryBtn').on('click', () => this.test_query_with_metadata());
        $('#detectVariablesBtn').on('click', () => this.detect_variables());
        $('#formatQueryBtn').on('click', () => this.format_query());
        $('#addColumnBtn').on('click', () => this.add_column());
        $('#addVariableBtn').on('click', () => this.add_variable());
        $('#runPreviewBtn').on('click', () => this.run_preview());
        $('#saveReportBtn').on('click', () => this.save_report());

        // Update save button text based on mode
        this.update_save_button_text();

        // Tab change handler - refresh editor when query tab is shown
        $('button[data-bs-toggle="pill"]').on('shown.bs.tab', (e) => {
            const target = $(e.target).attr('data-bs-target');
            if (target === '#query') {
                // Refresh CodeMirror when query tab is shown
                this.query_editor.refresh();
            } else if (target === '#preview') {
                this.prepare_preview();
            } else if (target === '#columns' && this.report_data.pending_column_analysis) {
                // If we have pending column analysis, show it
                this.show_column_analysis_results();
            }
        });

        $('#isModel').on('change', (e) => {
            const is_checked = $(e.target).is(':checked');
            $('#reportModel').prop('disabled', !is_checked);
            
            if (!is_checked) {
                // Clear model selection when disabling
                $('#reportModel').val('');
            }
        });
    }


    async load_connections() {
        try {
            console.log('Loading connections...');
            
            const result = await window.app.api.post(this.urls.data_api, {
                model: 'Connection',
                operation: 'list'
            });

            if (result.success) {
                this.report_data.connections = result.data;
                const select = $('#reportConnection');
                select.empty().append('<option value="">Select a connection...</option>');

                console.log('Loaded', result.data.length, 'connections');

                result.data.forEach(conn => {
                    // Use appropriate fields - db_type might be database_type, type, or engine
                    const db_type = conn.db_type || conn.database_type || conn.type || conn.engine || '';
                    const display_text = db_type ? `${conn.name} (${db_type})` : conn.name;
                    select.append(`<option value="${conn.id}">${display_text}</option>`);
                });

                console.log('Connections dropdown populated with', $('#reportConnection option').length - 1, 'connections');
            }
        } catch (error) {
            console.error('Failed to load connections:', error);
            this.show_error('Failed to load database connections');
        }
    }


    setup_event_handlers() {
        // Auto-generate slug from name
        $('#reportName').on('input', (e) => {
            if (!this.is_edit_mode) {
                const slug = $(e.target).val()
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/^-|-$/g, '');
                $('#reportSlug').val(slug);
            }
        });

        // Button click handlers
        $('#testQueryBtn').on('click', () => this.test_query_with_metadata());
        $('#detectVariablesBtn').on('click', () => this.detect_variables());
        $('#formatQueryBtn').on('click', () => this.format_query());
        $('#addColumnBtn').on('click', () => this.add_column());
        $('#addVariableBtn').on('click', () => this.add_variable());
        $('#runPreviewBtn').on('click', () => this.run_preview());
        $('#saveReportBtn').on('click', () => this.save_report());

        // Update save button text based on mode
        this.update_save_button_text();

        // Tab change handler
        $('button[data-bs-toggle="pill"]').on('shown.bs.tab', (e) => {
            const target = $(e.target).attr('data-bs-target');
            if (target === '#preview') {
                this.prepare_preview();
            } else if (target === '#columns' && this.report_data.pending_column_analysis) {
                // If we have pending column analysis, show it
                this.show_column_analysis_results();
            }
        });
    }

    update_save_button_text() {
        const button_text = this.is_edit_mode ? 'Save Report' : 'Create Report';
        $('#saveReportBtn').text(button_text);
    }

    

    async load_report_templates() {
        try {
            const result = await window.app.api.post(this.urls.list_report_templates, {});

            if (result.success && result.data) {
                this.report_data.templates = result.data;
                const select = $('#reportTemplate');
                select.empty().append('<option value="">Default template</option>');

                result.data.forEach(template => {
                    select.append(`<option value="${template.id}">${template.display_name}</option>`);
                });

                // Check for pending template
                if (this._pending_template_id) {
                    $('#reportTemplate').val(this._pending_template_id);
                    delete this._pending_template_id;
                }
            }
        } catch (error) {
            console.error('Failed to load report templates:', error);
        }
    }

    async load_data_types() {
        try {
            const result = await window.app.api.post(this.urls.data_api, {
                model: 'DataType',
                operation: 'list'
            });

            if (result.success) {
                result.data.forEach(dt => {
                    this.report_data.data_types[dt.id] = dt;
                });
            }
        } catch (error) {
            console.error('Failed to load data types:', error);
        }
    }

    async load_variable_types() {
        try {
            const result = await window.app.api.post(this.urls.data_api, {
                model: 'VariableType',
                operation: 'list'
            });

            if (result.success) {
                result.data.forEach(vt => {
                    this.report_data.variable_types[vt.id] = vt;
                });
            }
        } catch (error) {
            console.error('Failed to load variable types:', error);
        }
    }

    async load_categories() {
        try {
            const result = await window.app.api.post(this.urls.get_stats, {});

            if (result.success && result.data.categories) {
                this.report_data.categories = Object.keys(result.data.categories).filter(c => c);

                const datalist = $('#categoryList');
                datalist.empty();
                this.report_data.categories.forEach(cat => {
                    datalist.append(`<option value="${cat}">`);
                });
            }
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    async test_query_with_metadata() {
        const query = this.query_editor.getValue();
        const connection_id = $('#reportConnection').val();

        if (!query || !connection_id) {
            this.show_error('#queryTestResult', 'Please select a connection and enter a query');
            return;
        }

        this.show_loading(true);
        $('#queryTestResult').html('<div class="alert alert-info">Validating query and extracting metadata...</div>');

        try {
            // First validate the query
            const validate_result = await window.app.api.post(this.urls.validate_query, {
                query: query,
                connection_id: connection_id
            });

            if (!validate_result.success) {
                throw new Error(validate_result.error || 'Query validation failed');
            }

            // Query is valid, now extract metadata
            const metadata_result = await window.app.api.post(this.urls.query_metadata, {
                query: query,
                connection_id: connection_id,
                params: {}
            });

            if (metadata_result.success && metadata_result.data.columns) {
                const columns = metadata_result.data.columns;

                // Auto-populate columns with metadata
                this.report_data.columns = await this.create_columns_from_metadata(columns);

                this.render_columns();

                // Show success with column count
                const message = `
                    <div class="alert alert-success">
                        <strong>Query validated successfully!</strong><br>
                        Found ${columns.length} columns. Column definitions have been auto-populated.
                        <button class="btn btn-sm btn-primary ms-2" onclick="$('#columns-tab').tab('show')">
                            View Columns
                        </button>
                    </div>
                `;
                $('#queryTestResult').html(message);

                // Also detect variables
                await this.detect_variables();
            }
        } catch (error) {
            this.show_error('#queryTestResult', 'Query validation failed: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    async create_columns_from_metadata(metadata_columns) {
        const columns = [];

        for (let idx = 0; idx < metadata_columns.length; idx++) {
            const meta_col = metadata_columns[idx];

            // Get suggested settings for this column
            let suggestions = {};
            if (this.urls.suggest_column_settings) {
                try {
                    const suggest_result = await window.app.api.post(this.urls.suggest_column_settings, {
                        column_name: meta_col.name,
                        column_type: meta_col.type
                    });

                    if (suggest_result.success) {
                        suggestions = suggest_result.data;
                    }
                } catch (error) {
                    console.warn('Failed to get column suggestions:', error);
                }
            }

            // Find data type id - try multiple approaches
            let data_type_id = null;

            // First try exact match on name
            const data_type = Object.values(this.report_data.data_types).find(dt => dt.name === meta_col.type);
            if (data_type) {
                data_type_id = data_type.id;
            } else {
                // Try to get default based on SQL type
                data_type_id = this.get_default_data_type(meta_col.sql_type || meta_col.type);
            }

            // If still null, use string as ultimate fallback
            if (!data_type_id) {
                const string_type = Object.values(this.report_data.data_types).find(dt => dt.name === 'string');
                data_type_id = string_type ? string_type.id : Object.values(this.report_data.data_types)[0]?.id;
            }

            // Create clean column object with ONLY the fields we need
            columns.push({
                name: meta_col.name,
                display_name: suggestions.display_name || meta_col.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                data_type_id: data_type_id,
                order_index: idx,
                is_searchable: suggestions.is_searchable !== undefined ? suggestions.is_searchable : true,
                is_visible: suggestions.is_visible !== undefined ? suggestions.is_visible : true,
                is_sortable: suggestions.is_sortable !== undefined ? suggestions.is_sortable : true,
                alignment: suggestions.alignment || 'left',
                format_string: suggestions.format_string || null,
                search_type: suggestions.search_type || 'contains',
                width: null,
                options: {}
            });
        }

        return columns;
    }

    async analyze_columns_from_query() {
        if (!this.is_edit_mode) {
            this.show_error('Save the report first to analyze columns');
            return;
        }

        this.show_loading(true);

        try {
            const result = await window.app.api.post(this.urls.analyze_columns, {
                report_id: this.report_id,
                auto_update: false,
                dry_run: true
            });

            if (result.success && result.data) {
                this.report_data.pending_column_analysis = result.data;
                this.show_column_analysis_results();
            }
        } catch (error) {
            this.show_error('Failed to analyze columns: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    show_column_analysis_results() {
        const analysis = this.report_data.pending_column_analysis;
        if (!analysis) return;

        let html = '<div class="card"><div class="card-body">';
        html += '<h5 class="card-title">Column Analysis Results</h5>';

        // Summary
        const summary = analysis.summary;
        html += `
            <div class="row mb-3">
                <div class="col-md-3">
                    <div class="text-center">
                        <h3>${summary.total_query_columns}</h3>
                        <small class="text-muted">Query Columns</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h3>${summary.total_existing_columns}</h3>
                        <small class="text-muted">Existing Columns</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h3 class="text-success">${summary.new_columns_count}</h3>
                        <small class="text-muted">New Columns</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h3 class="text-warning">${summary.type_changes_count}</h3>
                        <small class="text-muted">Type Changes</small>
                    </div>
                </div>
            </div>
        `;

        // New columns
        if (analysis.new_columns.length > 0) {
            html += '<h6>New Columns Found:</h6><ul>';
            analysis.new_columns.forEach(col => {
                html += `<li><strong>${col.name}</strong> (suggested type: ${col.suggested_type})</li>`;
            });
            html += '</ul>';
        }

        // Type changes
        if (analysis.type_changes.length > 0) {
            html += '<h6>Type Changes Suggested:</h6><ul>';
            analysis.type_changes.forEach(change => {
                html += `<li><strong>${change.name}</strong>: ${change.current_type} → ${change.suggested_type}</li>`;
            });
            html += '</ul>';
        }

        // Missing columns
        if (analysis.missing_columns.length > 0) {
            html += '<h6 class="text-danger">Columns Not Found in Query:</h6><ul>';
            analysis.missing_columns.forEach(col => {
                html += `<li>${col}</li>`;
            });
            html += '</ul>';
        }

        // Actions
        if (summary.new_columns_count > 0 || summary.type_changes_count > 0) {
            html += `
                <div class="mt-3">
                    <button class="btn btn-primary" onclick="window.reportBuilder.apply_column_analysis()">
                        Apply Changes
                    </button>
                    <button class="btn btn-secondary ms-2" onclick="window.reportBuilder.dismiss_column_analysis()">
                        Dismiss
                    </button>
                </div>
            `;
        }

        html += '</div></div>';

        // Show in a dedicated area or modal
        $('#columnAnalysisResults').html(html);

        // Show alert in columns tab
        const alert_html = `
            <div class="alert alert-info alert-dismissible">
                Found ${summary.new_columns_count} new columns and ${summary.type_changes_count} type changes.
                <a href="#" onclick="$('#columnAnalysisResults').toggle(); return false;">View Details</a>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('#columnsTabAlerts').html(alert_html);
    }

    async apply_column_analysis() {
        if (!this.report_data.pending_column_analysis) return;

        this.show_loading(true);

        try {
            const result = await window.app.api.post(this.urls.analyze_columns, {
                report_id: this.report_id,
                auto_update: true,
                dry_run: false
            });

            if (result.success) {
                this.show_success('Column changes applied successfully!');

                // Reload report to get updated columns
                await this.load_existing_report();

                // Clear analysis
                this.report_data.pending_column_analysis = null;
                $('#columnAnalysisResults').empty();
                $('#columnsTabAlerts').empty();
            }
        } catch (error) {
            this.show_error('Failed to apply column changes: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    dismiss_column_analysis() {
        this.report_data.pending_column_analysis = null;
        $('#columnAnalysisResults').empty();
        $('#columnsTabAlerts').empty();
    }

    async sync_columns_from_query() {
        if (!this.is_edit_mode) {
            this.show_error('Save the report first to sync columns');
            return;
        }

        const remove_missing = confirm(
            'Sync columns with query?\n\n' +
            'This will:\n' +
            '• Add any new columns from the query\n' +
            '• Update column types based on the query\n' +
            '• Reorder columns to match the query\n\n' +
            'Remove columns not in the query?'
        );

        this.show_loading(true);

        try {
            const result = await window.app.api.post(this.urls.sync_columns, {
                report_id: this.report_id,
                remove_missing: remove_missing
            });

            if (result.success && result.data) {
                const summary = result.data.summary;
                let message = 'Sync completed:\n';

                if (summary.added_count > 0) {
                    message += `• Added ${summary.added_count} columns\n`;
                }
                if (summary.updated_count > 0) {
                    message += `• Updated ${summary.updated_count} columns\n`;
                }
                if (summary.removed_count > 0) {
                    message += `• Removed ${summary.removed_count} columns\n`;
                }
                if (summary.columns_reordered) {
                    message += '• Reordered columns to match query\n';
                }

                this.show_success(message);

                // Reload columns
                await this.load_existing_report();
            }
        } catch (error) {
            this.show_error('Failed to sync columns: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    async auto_detect_column_types() {
        if (!this.is_edit_mode) {
            this.show_error('Save the report first to detect column types');
            return;
        }

        this.show_loading(true);

        try {
            const result = await window.app.api.post(this.urls.detect_column_types, {
                report_id: this.report_id,
                sample_size: 100
            });

            if (result.success && result.data.columns) {
                // Show type detection results
                this.show_type_detection_results(result.data);
            }
        } catch (error) {
            this.show_error('Failed to detect column types: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    show_type_detection_results(data) {
        let html = '<div class="modal fade" id="typeDetectionModal" tabindex="-1">';
        html += '<div class="modal-dialog modal-lg"><div class="modal-content">';
        html += '<div class="modal-header"><h5 class="modal-title">Column Type Detection Results</h5>';
        html += '<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>';
        html += '<div class="modal-body">';

        html += '<table class="table table-sm">';
        html += '<thead><tr><th>Column</th><th>Current Type</th><th>Detected Type</th><th>Confidence</th></tr></thead>';
        html += '<tbody>';

        data.columns.forEach(col => {
            const current_col = this.report_data.columns.find(c => c.name === col.name);
            const current_type = current_col ? this.report_data.data_types[current_col.data_type_id]?.name : 'unknown';

            html += '<tr>';
            html += `<td>${col.name}</td>`;
            html += `<td>${current_type}</td>`;
            html += `<td>${col.detected_type}</td>`;
            html += `<td><span class="badge bg-${col.confidence === 'high' ? 'success' : 'warning'}">${col.confidence}</span></td>`;
            html += '</tr>';
        });

        html += '</tbody></table>';
        html += `<p class="text-muted">Detection method: ${data.detection_method}, Sample size: ${data.sample_size}</p>`;
        html += '</div></div></div></div>';

        // Add modal to body and show it
        $('body').append(html);
        const modal = new bootstrap.Modal(document.getElementById('typeDetectionModal'));
        modal.show();

        // Remove modal after hidden
        $('#typeDetectionModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }

    async detect_variables() {
        const query = this.query_editor.getValue();

        try {
            const result = await window.app.api.post(this.urls.detect_variables, {
                query: query
            });

            if (result.success && result.data.variables) {
                const variables = result.data.variables;

                this.report_data.variables = variables.map((var_name, idx) => ({
                    name: var_name,
                    display_name: var_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    variable_type_id: this.get_default_variable_type('text'),
                    order_index: idx,
                    is_required: true
                }));

                this.render_variables();

                if (variables.length > 0) {
                    this.show_success('#queryTestResult', `Found ${variables.length} variables`);
                    $('#variables-tab').tab('show');
                } else {
                    this.show_info('#queryTestResult', 'No variables found in query');
                }
            }
        } catch (error) {
            this.show_error('#queryTestResult', 'Failed to detect variables: ' + error.message);
        }
    }

    async test_connection() {
        const connection_id = $('#reportConnection').val();
        if (!connection_id) {
            this.show_error('#connectionTestResult', 'Please select a connection');
            return;
        }

        try {
            const result = await window.app.api.post(this.urls.test_connection, {
                connection_id: connection_id
            });

            if (result.success && result.data.success) {
                this.show_success('#connectionTestResult', result.data.message);
            } else {
                this.show_error('#connectionTestResult', result.data?.message || 'Connection test failed');
            }
        } catch (error) {
            this.show_error('#connectionTestResult', 'Connection test failed: ' + error.message);
        }
    }

    format_query() {
        const query = this.query_editor.getValue();
        const formatted = query
            .replace(/SELECT/gi, 'SELECT')
            .replace(/FROM/gi, '\nFROM')
            .replace(/WHERE/gi, '\nWHERE')
            .replace(/GROUP BY/gi, '\nGROUP BY')
            .replace(/ORDER BY/gi, '\nORDER BY')
            .replace(/HAVING/gi, '\nHAVING')
            .replace(/JOIN/gi, '\nJOIN')
            .replace(/LEFT JOIN/gi, '\nLEFT JOIN')
            .replace(/RIGHT JOIN/gi, '\nRIGHT JOIN')
            .replace(/INNER JOIN/gi, '\nINNER JOIN');

        this.query_editor.setValue(formatted);
    }

    render_columns() {
        const container = $('#columnsList');
        container.empty();

        // Add analysis results area if not exists
        if (!$('#columnsTabAlerts').length) {
            container.before('<div id="columnsTabAlerts"></div>');
        }
        if (!$('#columnAnalysisResults').length) {
            container.before('<div id="columnAnalysisResults" style="display:none;"></div>');
        }

        // Remove any existing management buttons before adding new ones
        $('#columnManagementButtons').remove();

        if (this.report_data.columns.length === 0) {
            container.html(`
                <div class="text-muted">
                    No columns defined.
                    <button class="btn btn-sm btn-primary" onclick="$('#testQueryBtn').click()">
                        Test Query to Auto-Detect Columns
                    </button>
                </div>
            `);
            return;
        }

        // Add column management buttons only if in edit mode
        if (this.is_edit_mode) {
            container.before(`
                <div class="mb-3" id="columnManagementButtons">
                    <button class="btn btn-sm btn-secondary" id="analyzeColumnsBtn">
                        <i class="fas fa-search"></i> Analyze Columns
                    </button>
                    <button class="btn btn-sm btn-warning" id="syncColumnsBtn">
                        <i class="fas fa-sync"></i> Sync with Query
                    </button>
                    <button class="btn btn-sm btn-info" id="autoDetectTypesBtn">
                        <i class="fas fa-magic"></i> Auto-Detect Types
                    </button>
                </div>
            `);

            $('#analyzeColumnsBtn').on('click', () => this.analyze_columns_from_query());
            $('#syncColumnsBtn').on('click', () => this.sync_columns_from_query());
            $('#autoDetectTypesBtn').on('click', () => this.auto_detect_column_types());
        }

        this.report_data.columns.forEach((col, idx) => {
            const html = this.create_column_html(col, idx);
            container.append(html);
        });

        // Use jQuery UI Sortable
        if ($.fn.sortable) {
            // destroy existing sortable if any
            if (container.hasClass('ui-sortable')) {
                container.sortable('destroy');
            }
            let start_index;
            container.sortable({
                handle: '.drag-handle',
                placeholder: 'sortable-placeholder',
                start: (event, ui) => {
                    start_index = ui.item.index();
                },
                update: (event, ui) => {
                    const new_index = ui.item.index();
                    this.reorder_columns(start_index, new_index);
                }
            });
        }
    }

    create_column_html(col, idx) {
        const data_type_options = Object.values(this.report_data.data_types)
            .map(dt => `<option value="${dt.id}" ${col.data_type_id === dt.id ? 'selected' : ''}>${dt.display}</option>`)
            .join('');

        return `
            <div class="column-item card mb-2" data-index="${idx}">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-auto">
                            <span class="drag-handle" style="cursor: move;">≡</span>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Column Name</label>
                            <input type="text" class="form-control form-control-sm" value="${col.name}"
                                   data-field="name" data-index="${idx}" readonly>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Display Name</label>
                            <input type="text" class="form-control form-control-sm" value="${col.display_name}"
                                   data-field="display_name" data-index="${idx}"
                                   placeholder="Display name">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Data Type</label>
                            <select class="form-select form-select-sm" data-field="data_type_id" data-index="${idx}">
                                ${data_type_options}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Alignment</label>
                            <select class="form-select form-select-sm" data-field="alignment" data-index="${idx}">
                                <option value="left" ${col.alignment === 'left' ? 'selected' : ''}>Left</option>
                                <option value="center" ${col.alignment === 'center' ? 'selected' : ''}>Center</option>
                                <option value="right" ${col.alignment === 'right' ? 'selected' : ''}>Right</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Options</label>
                            <div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" ${col.is_searchable ? 'checked' : ''}
                                           data-field="is_searchable" data-index="${idx}" id="search_${idx}">
                                    <label class="form-check-label" for="search_${idx}">Search</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" ${col.is_sortable ? 'checked' : ''}
                                           data-field="is_sortable" data-index="${idx}" id="sort_${idx}">
                                    <label class="form-check-label" for="sort_${idx}">Sort</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" ${col.is_visible ? 'checked' : ''}
                                           data-field="is_visible" data-index="${idx}" id="visible_${idx}">
                                    <label class="form-check-label" for="visible_${idx}">Visible</label>
                                </div>
                            </div>
                        </div>
                        <div class="col-auto">
                            <button class="btn btn-sm btn-danger remove-column-btn" data-index="${idx}">×</button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-3">
                            <input type="text" class="form-control form-control-sm"
                                   placeholder="Format string (e.g., {:.2f} for currency)"
                                   value="${col.format_string || ''}"
                                   data-field="format_string" data-index="${idx}">
                        </div>
                        <div class="col-md-3">
                            <select class="form-select form-select-sm" data-field="search_type" data-index="${idx}">
                                <option value="contains" ${col.search_type === 'contains' ? 'selected' : ''}>Contains</option>
                                <option value="exact" ${col.search_type === 'exact' ? 'selected' : ''}>Exact Match</option>
                                <option value="range" ${col.search_type === 'range' ? 'selected' : ''}>Range</option>
                                <option value="date_range" ${col.search_type === 'date_range' ? 'selected' : ''}>Date Range</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <input type="number" class="form-control form-control-sm"
                                   placeholder="Width (pixels)"
                                   value="${col.width || ''}"
                                   data-field="width" data-index="${idx}">
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    update_column(index, field, value) {
        if (field === 'is_searchable' || field === 'is_sortable' || field === 'is_visible') {
            value = value === 'true' || value === true;
        }
        this.report_data.columns[index][field] = value;
    }

    remove_column(index) {
        if (confirm('Remove this column?')) {
            this.report_data.columns.splice(index, 1);
            this.render_columns();
        }
    }

    add_column() {
        const name = prompt('Column name:');
        if (name) {
            // Ensure we have a valid data_type_id
            let default_data_type_id = this.get_default_data_type('string');
            if (!default_data_type_id && Object.values(this.report_data.data_types).length > 0) {
                default_data_type_id = Object.values(this.report_data.data_types)[0].id;
            }

            this.report_data.columns.push({
                name: name,
                display_name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                data_type_id: default_data_type_id,
                order_index: this.report_data.columns.length,
                is_searchable: true,
                is_visible: true,
                is_sortable: true,
                alignment: 'left',
                search_type: 'contains'
            });
            this.render_columns();
        }
    }

    reorder_columns(old_index, new_index) {
        const [moved_column] = this.report_data.columns.splice(old_index, 1);
        this.report_data.columns.splice(new_index, 0, moved_column);

        // Update order indices
        this.report_data.columns.forEach((col, idx) => {
            col.order_index = idx;
        });

        // Note: The actual reorder API call will happen when saving
    }

    // Variable Management
    render_variables() {
        const container = $('#variablesList');
        container.empty();

        if (this.report_data.variables.length === 0) {
            container.html('<div class="text-muted">No variables defined. Use :variable_name in your query.</div>');
            return;
        }

        this.report_data.variables.forEach((variable, idx) => {
            const html = this.create_variable_html(variable, idx);
            container.append(html);
        });
    }

    create_variable_html(variable, idx) {
        const variable_type_options = Object.values(this.report_data.variable_types)
            .map(vt => `<option value="${vt.id}" ${variable.variable_type_id === vt.id ? 'selected' : ''}>${vt.display}</option>`)
            .join('');

        return `
            <div class="variable-item card mb-3" data-index="${idx}">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <label class="form-label">Variable Name</label>
                            <input type="text" class="form-control" value="${variable.name}"
                                   data-field="name" data-index="${idx}" readonly>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Display Name</label>
                            <input type="text" class="form-control" value="${variable.display_name}"
                                   data-field="display_name" data-index="${idx}">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Variable Type</label>
                            <select class="form-select" data-field="variable_type_id" data-index="${idx}">
                                ${variable_type_options}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Default Value</label>
                            <input type="text" class="form-control" value="${variable.default_value || ''}"
                                   data-field="default_value" data-index="${idx}">
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-4">
                            <label class="form-label">Placeholder</label>
                            <input type="text" class="form-control" value="${variable.placeholder || ''}"
                                   data-field="placeholder" data-index="${idx}">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Options</label>
                            <div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" ${variable.is_required ? 'checked' : ''}
                                           data-field="is_required" data-index="${idx}" id="req_${idx}">
                                    <label class="form-check-label" for="req_${idx}">Required</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" ${variable.is_hidden ? 'checked' : ''}
                                           data-field="is_hidden" data-index="${idx}" id="hidden_${idx}">
                                    <label class="form-check-label" for="hidden_${idx}">Hidden</label>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-sm btn-danger float-end remove-variable-btn" data-index="${idx}">Remove</button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col">
                            <label class="form-label">Help Text</label>
                            <input type="text" class="form-control" value="${variable.help_text || ''}"
                                   data-field="help_text" data-index="${idx}"
                                   placeholder="Help text for users">
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    update_variable(index, field, value) {
        if (field === 'is_required' || field === 'is_hidden') {
            value = value === 'true' || value === true;
        }
        this.report_data.variables[index][field] = value;
    }

    remove_variable(index) {
        if (confirm('Remove this variable?')) {
            this.report_data.variables.splice(index, 1);
            this.render_variables();
        }
    }

    add_variable() {
        const name = prompt('Variable name (without colon):');
        if (name) {
            this.report_data.variables.push({
                name: name,
                display_name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                variable_type_id: this.get_default_variable_type('text'),
                order_index: this.report_data.variables.length,
                is_required: true
            });
            this.render_variables();
        }
    }

    // Preview
    prepare_preview() {
        // Build variable inputs
        const variable_inputs_html = this.report_data.variables
            .filter(v => !v.is_hidden)
            .map(v => {
                const var_type = this.report_data.variable_types[v.variable_type_id];
                let input_html = '';

                switch (var_type?.name) {
                    case 'date':
                        input_html = `<input type="date" class="form-control preview-variable"
                                           data-name="${v.name}"
                                           value="${v.default_value || ''}"
                                           ${v.is_required ? 'required' : ''}>`;
                        break;
                    case 'datetime':
                        input_html = `<input type="datetime-local" class="form-control preview-variable"
                                           data-name="${v.name}"
                                           value="${v.default_value || ''}"
                                           ${v.is_required ? 'required' : ''}>`;
                        break;
                    case 'number':
                        input_html = `<input type="number" class="form-control preview-variable"
                                           data-name="${v.name}"
                                           value="${v.default_value || ''}"
                                           ${v.is_required ? 'required' : ''}>`;
                        break;
                    case 'select':
                        // TODO: Handle select options
                        input_html = `<select class="form-control preview-variable"
                                            data-name="${v.name}"
                                            ${v.is_required ? 'required' : ''}>
                                        <option value="">Select...</option>
                                      </select>`;
                        break;
                    default:
                        input_html = `<input type="text" class="form-control preview-variable"
                                           data-name="${v.name}"
                                           value="${v.default_value || ''}"
                                           placeholder="${v.placeholder || ''}"
                                           ${v.is_required ? 'required' : ''}>`;
                }

                return `
                    <div class="mb-3">
                        <label class="form-label">${v.display_name}${v.is_required ? ' *' : ''}</label>
                        ${input_html}
                        ${v.help_text ? `<small class="text-muted">${v.help_text}</small>` : ''}
                    </div>
                `;
            }).join('');

        $('#variableInputs').html(variable_inputs_html || '<p class="text-muted">No variables required for this report.</p>');
    }

    async run_preview() {
        if (!this.is_edit_mode) {
            this.show_info('#previewResults', 'Save the report first to preview it');
            return;
        }

        // Collect variable values
        const vars = {};
        $('.preview-variable').each(function() {
            vars[$(this).data('name')] = $(this).val();
        });

        this.show_loading(true);

        try {
            const result = await window.app.api.post(this.urls.preview_report, {
                report_id: this.report_id,
                limit: 10,
                vars: vars
            });

            if (result.success && result.data) {
                this.display_preview_results(result.data);
            }
        } catch (error) {
            this.show_error('#previewResults', 'Preview failed: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    display_preview_results(data) {
        if (!data.data || data.data.length === 0) {
            $('#previewResults').html('<div class="alert alert-info">No results found</div>');
            return;
        }

        // Build table
        const headers = Object.keys(data.data[0]);
        const table_html = `
            <div class="table-responsive">
                <table class="table table-striped table-bordered">
                    <thead class="table-dark">
                        <tr>
                            ${headers.map(h => `<th>${h}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.data.map(row => `
                            <tr>
                                ${headers.map(h => `<td>${row[h] !== null ? row[h] : '<em class="text-muted">null</em>'}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <p class="text-muted mt-2">Showing ${data.data.length} of ${data.recordsTotal || data.data.length} total records</p>
        `;

        $('#previewResults').html(table_html);
    }

    // Save Operations
    async save_report() {
        if (!this.validate_report()) return;

        this.show_loading(true);

        try {
            const report_data = this.get_report_data();

            let result;

            if (this.is_edit_mode) {
                // Update existing report
                result = await window.app.api.post(this.urls.data_api, {
                    model: 'Report',
                    operation: 'update',
                    id: this.report_id,
                    data: report_data
                });
            } else {
                // Create new report
                result = await window.app.api.post(this.urls.data_api, {
                    model: 'Report',
                    operation: 'create',
                    data: report_data
                });
            }

            if (!result.success) {
                throw new Error(result.error || 'Failed to save report');
            }

            const report_id = this.is_edit_mode ? this.report_id : result.data.id;

            // Save columns and variables
            if (result.success && this.report_id) {
                await this.save_columns(report_id);
                await this.save_variables(report_id);
                await this.save_all_actions();
            }
    

            // Success!
            this.show_success('Report saved successfully!');

            // If it was a create, switch to edit mode
            if (!this.is_edit_mode) {
                this.report_id = report_id;
                this.is_edit_mode = true;
                window.history.replaceState({}, '', `/reports/builder/${report_id}`);
                this.update_save_button_text();
            }

            

        } catch (error) {
            this.show_error('Error saving report: ' + error.message);
        } finally {
            this.show_loading(false);
        }
    }

    async load_existing_report() {
        try {
            console.log('Starting to load existing report...');
            
            // Load the report using data_api
            const result = await window.app.api.post(this.urls.data_api, {
                model: 'Report',
                operation: 'read',
                id: this.report_id
            });

            if (result.success && result.data) {
                const report = result.data;
                this.report_data.report = report;

                console.log('Report loaded, connection_id:', report.connection_id);
                console.log('Available connections:', $('#reportConnection option').length - 1); // -1 for placeholder

                // Populate basic fields
                $('#reportName').val(report.name);
                $('#reportSlug').val(report.slug);
                $('#reportDisplay').val(report.display || '');
                $('#reportDescription').val(report.description || '');
                $('#reportCategory').val(report.category || '');
                
                let tags_value = '';

                if (report.tags) {
                    if (Array.isArray(report.tags)) {
                        tags_value = report.tags.join(', ');
                    } else if (typeof report.tags === 'string') {
                        tags_value = report.tags;
                    } else if (typeof report.tags === 'object') {
                        tags_value = JSON.stringify(report.tags);
                    } else {
                        tags_value = String(report.tags);
                    }
                }

                $('#reportTags').val(tags_value);

                // Set query and refresh editor
                this.query_editor.setValue(report.query);
                // Force refresh after setting value
                setTimeout(() => {
                    this.query_editor.refresh();
                }, 50);

                // Set flags - directly from report object
                $('#isWide').prop('checked', report.is_wide || false);
                $('#isAjax').prop('checked', report.is_ajax || false);
                $('#isAutoRun').prop('checked', report.is_auto_run || false);
                $('#isSearchable').prop('checked', report.is_searchable || false);
                $('#isPublic').prop('checked', report.is_public || false);
                $('#isModel').prop('checked', report.is_model || false);
                $('#isDownloadCsv').prop('checked', report.is_download_csv || false);
                $('#isDownloadXlsx').prop('checked', report.is_download_xlsx || false);
                $('#isPublished').prop('checked', report.is_published !== false);
                
                // Set options
                const options = report.options || {};
                $('#resultsLimit').val(options.results_limit || 0);
                $('#cacheMinutes').val(options.cache_duration_minutes || 60);

                // Set connection - with detailed debugging
                const connection_id = report.connection_id;
                const template_id = report.report_template_id;
                const model_id = report.model_id;

                if (connection_id) {
                    // Force a small delay to ensure DOM is ready
                    await new Promise(resolve => setTimeout(resolve, 50));
                    
                    const connection_exists = $(`#reportConnection option[value="${connection_id}"]`).length > 0;
                    console.log('Checking for connection_id:', connection_id, 'Exists:', connection_exists);
                    
                    if (connection_exists) {
                        $('#reportConnection').val(connection_id);
                        // Force change event to ensure it's registered
                        $('#reportConnection').trigger('change');
                        console.log('Connection set to:', $('#reportConnection').val());
                    } else {
                        console.error('Connection ID not found in dropdown:', connection_id);
                        console.log('Available connection IDs:', 
                            $('#reportConnection option').map(function() { 
                                return $(this).val(); 
                            }).get().filter(v => v)
                        );
                    }
                }

                // Set template
                if (template_id) {
                    await new Promise(resolve => setTimeout(resolve, 50));
                    
                    const template_exists = $(`#reportTemplate option[value="${template_id}"]`).length > 0;
                    console.log('Checking for template_id:', template_id, 'Exists:', template_exists);
                    
                    if (template_exists) {
                        $('#reportTemplate').val(template_id);
                        $('#reportTemplate').trigger('change');
                        console.log('Template set to:', $('#reportTemplate').val());
                    } else {
                        console.error('Template ID not found in dropdown:', template_id);
                    }
                }
                if (model_id) {
                    await new Promise(resolve => setTimeout(resolve, 50));
                    
                    const model_exists = $(`#reportModel option[value="${model_id}"]`).length > 0;
                    console.log('Checking for model_id:', model_id, 'Exists:', model_exists);
                    
                    if (model_exists) {
                        $('#reportModel').val(model_id);
                        $('#reportModel').trigger('change');
                        console.log('Model set to:', $('#reportModel').val());
                    } else {
                        console.error('Model ID not found in dropdown:', model_id);
                    }
                    // Set the isModel checkbox based on whether a model is selected
                    $('#isModel').prop('checked', true);
                    $('#reportModel').prop('disabled', false);
                } else {
                    $('#isModel').prop('checked', false);
                    $('#reportModel').prop('disabled', true);
                }

                // Now load columns and variables separately
                const [columns, variables] = await Promise.all([
                    this.get_existing_columns(this.report_id),
                    this.get_existing_variables(this.report_id)
                ]);

                // Store columns with their IDs
                this.report_data.columns = columns;
                this.column_ids = {};
                columns.forEach(col => {
                    this.column_ids[col.name] = col.id;
                });

                // Store variables with their IDs
                this.report_data.variables = variables;
                this.variable_ids = {};
                variables.forEach(variable => {
                    this.variable_ids[variable.name] = variable.id;
                });

                // Render the UI
                this.render_columns();
                this.render_variables();
            }
        } catch (error) {
            console.error('Failed to load existing report:', error);
            this.show_error('Failed to load report data: ' + error.message);
        }
    }

    async load_model_default_query(model_id) {
        if (!model_id) return;
        
        try {
            const model_result = await window.app.api.post(this.urls.data_api, {
                model: 'Model',
                operation: 'read',
                id: model_id
            });
            
            if (model_result.success && model_result.data) {
                const model = model_result.data;
                
                // If the model has a default query, you could set it
                // This depends on your Model structure
                if (model.default_query) {
                    if (confirm('Load the default query for this model?')) {
                        this.query_editor.setValue(model.default_query);
                    }
                } else if (model.table_name) {
                    // Generate a simple SELECT * query
                    const default_query = `SELECT * FROM ${model.table_name}`;
                    if (confirm(`Load default query: ${default_query}?`)) {
                        this.query_editor.setValue(default_query);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load model details:', error);
        }
    }

    get_report_data() {
        const tags_value = $('#reportTags').val();
        const tags = tags_value ? tags_value.split(',').map(t => t.trim()).filter(t => t) : [];

        // Return flat structure with flags as direct properties
        return {
            slug: $('#reportSlug').val(),
            name: $('#reportName').val(),
            display: $('#reportDisplay').val() || null,
            description: $('#reportDescription').val() || null,
            query: this.query_editor.getValue(),
            connection_id: $('#reportConnection').val(),
            category: $('#reportCategory').val() || null,
            tags: tags,
            model_id: $('#reportModel').val() || null,  
            report_template_id: $('#reportTemplate').val() || null,
            // Flags as direct properties
            is_wide: $('#isWide').is(':checked'),
            is_ajax: $('#isAjax').is(':checked'),
            is_auto_run: $('#isAutoRun').is(':checked'),
            is_searchable: $('#isSearchable').is(':checked'),
            is_public: $('#isPublic').is(':checked'),
            is_model: $('#isModel').is(':checked') && $('#reportModel').val() !== '',
            is_download_csv: $('#isDownloadCsv').is(':checked'),
            is_download_xlsx: $('#isDownloadXlsx').is(':checked'),
            is_published: $('#isPublished').is(':checked'),
            // Options remain nested
            options: {
                results_limit: parseInt($('#resultsLimit').val()) || 0,
                cache_duration_minutes: parseInt($('#cacheMinutes').val()) || 60
            }
        };
    }

    async save_columns(report_id) {
        if (this.report_data.columns.length === 0) {
            return;
        }

        // VALIDATION: ensure every column has a data_type_id
        const invalid_columns = this.report_data.columns.filter(col => !col.data_type_id);

        if (invalid_columns.length > 0) {
            // pick a default string type
            const default_type = Object.values(this.report_data.data_types)
                .find(dt => dt.name === 'string')
                || Object.values(this.report_data.data_types)[0];

            if (!default_type) {
                throw new Error('No data types available. Please refresh and try again.');
            }

            invalid_columns.forEach(col => {
                col.data_type_id = default_type.id;
            });
        }

        // Fetch existing columns map if in edit mode
        let existing_columns_map = {};
        if (this.is_edit_mode) {
            const existing_columns = await this.get_existing_columns(report_id);
            existing_columns.forEach(col => {
                existing_columns_map[col.name] = col;
            });
        }

        // Process create/update
        const column_ids = [];
        for (let i = 0; i < this.report_data.columns.length; i++) {
            const column = this.report_data.columns[i];
            const existing_col = existing_columns_map[column.name];

            // payload build
            const column_data = {
                report_id: report_id,
                name: column.name,
                display_name: column.display_name,
                data_type_id: column.data_type_id,
                order_index: i,
                is_searchable: column.is_searchable ?? true,
                is_visible: column.is_visible ?? true,
                is_sortable: column.is_sortable ?? true,
                alignment: column.alignment || 'left',
                format_string: column.format_string || null,
                search_type: column.search_type || 'contains',
                width: column.width || null,
                options: column.options || {},
            };

            console.log(`Column[${i}] payload:`, column_data);

            if (existing_col) {
                try {
                    const update_result = await window.app.api.post(this.urls.data_api, {
                        model: 'ReportColumn',
                        operation: 'update',
                        id: existing_col.id,
                        data: column_data,
                    });
                    if (update_result.success) {
                        this.column_ids[column.name] = existing_col.id;
                        column_ids.push(existing_col.id);
                    }
                } catch (err) {
                    console.error('Exception during update:', err);
                }
                delete existing_columns_map[column.name];
            } else {
                try {
                    const create_result = await window.app.api.post(this.urls.data_api, {
                        model: 'ReportColumn',
                        operation: 'create',
                        data: column_data,
                    });
                    if (create_result.success && create_result.data?.id) {
                        this.column_ids[column.name] = create_result.data.id;
                        column_ids.push(create_result.data.id);
                    }
                } catch (err) {
                    console.error('Exception during create:', err);
                }
            }
        }
    }

    async save_variables(report_id) {
        // Skip if no variables defined yet
        if (this.report_data.variables.length === 0) {
            console.log('No variables to save yet');
            return;
        }

        // Get existing variables if editing
        let existing_variables_map = {};
        if (this.is_edit_mode) {
            const existing_variables = await this.get_existing_variables(report_id);
            existing_variables.forEach(variable => {
                existing_variables_map[variable.name] = variable;
            });
        }

        // Process each variable
        for (let i = 0; i < this.report_data.variables.length; i++) {
            const variable = this.report_data.variables[i];
            const existing_var = existing_variables_map[variable.name];

            // Build ONLY the fields we want to send - NO spreading!
            const variable_data = {};
            variable_data.report_id = report_id;
            variable_data.name = variable.name;
            variable_data.display_name = variable.display_name;
            variable_data.variable_type_id = variable.variable_type_id;
            variable_data.default_value = variable.default_value || null;
            variable_data.placeholder = variable.placeholder || null;
            variable_data.help_text = variable.help_text || null;
            variable_data.is_required = variable.is_required;
            variable_data.is_hidden = variable.is_hidden || false;
            variable_data.limits = variable.limits || null;
            variable_data.depends_on = variable.depends_on || null;
            variable_data.dependency_condition = variable.dependency_condition || null;
            variable_data.order_index = i;

            if (existing_var) {
                // Update existing variable
                const update_result = await window.app.api.post(this.urls.data_api, {
                    model: 'ReportVariable',
                    operation: 'update',
                    id: existing_var.id,
                    data: variable_data
                });

                if (!update_result.success) {
                    console.error('Failed to update variable:', update_result.error);
                } else {
                    // Track the id separately - DO NOT modify variable object
                    this.variable_ids[variable.name] = existing_var.id;
                }

                // Remove from map so we know which ones to delete later
                delete existing_variables_map[variable.name];
            } else {
                // Create new variable
                const create_result = await window.app.api.post(this.urls.data_api, {
                    model: 'ReportVariable',
                    operation: 'create',
                    data: variable_data
                });

                if (!create_result.success) {
                    console.error('Failed to create variable:', create_result.error);
                } else if (create_result.data && create_result.data.id) {
                    // Track the id separately - DO NOT modify variable object
                    this.variable_ids[variable.name] = create_result.data.id;
                }
            }
        }

        // Delete any variables that no longer exist
        for (const var_name in existing_variables_map) {
            const variable = existing_variables_map[var_name];
            await window.app.api.post(this.urls.data_api, {
                model: 'ReportVariable',
                operation: 'delete',
                id: variable.id
            });
            // Remove from our tracking
            delete this.variable_ids[var_name];
        }

        // Validate variables if API available and we have variables
        if (this.urls.validate_variables && this.report_data.variables.length > 0) {
            try {
                await window.app.api.post(this.urls.validate_variables, {
                    report_id: report_id
                });
            } catch (error) {
                // Non-critical error
                console.warn('Failed to validate variables:', error);
            }
        }
    }

    async get_existing_columns(report_id) {
        const result = await window.app.api.post(this.urls.data_api, {
            model: 'ReportColumn',
            operation: 'list',
            filters: { report_id: report_id },
            length: 100
        });

        return result.success ? result.data : [];
    }

    async get_existing_variables(report_id) {
        const result = await window.app.api.post(this.urls.data_api, {
            model: 'ReportVariable',
            operation: 'list',
            filters: { report_id: report_id }
        });
        return result.success ? result.data : [];
    }

    validate_report() {
        const errors = [];

        if (!$('#reportName').val()) errors.push('Report name is required');
        if (!$('#reportSlug').val()) errors.push('Report slug is required');
        if (!$('#reportConnection').val()) errors.push('Database connection is required');
        if (!this.query_editor.getValue()) errors.push('SQL query is required');

        // Validate slug format
       const slug = $('#reportSlug').val();
       /*if (slug && !/^[a-z0-9-\/]+$/.test(slug)) {
           errors.push('Slug can only contain lowercase letters, numbers, hyphens, and slashes');
       }*/

        if (errors.length > 0) {
            alert('Please fix the following errors:\n\n' + errors.join('\n'));
            return false;
        }

        return true;
    }

    // Helper Methods
    get_default_data_type(sql_type) {
        const type_map = {
            'VARCHAR': 'string',
            'TEXT': 'string',
            'CHAR': 'string',
            'INT': 'integer',
            'INTEGER': 'integer',
            'BIGINT': 'integer',
            'SMALLINT': 'integer',
            'DECIMAL': 'decimal',
            'NUMERIC': 'decimal',
            'FLOAT': 'decimal',
            'DOUBLE': 'decimal',
            'REAL': 'decimal',
            'DATE': 'date',
            'DATETIME': 'datetime',
            'TIMESTAMP': 'datetime',
            'TIME': 'time',
            'BOOLEAN': 'boolean',
            'BOOL': 'boolean'
        };

        const upper_type = (sql_type || '').toUpperCase();
        for (const [key, value] of Object.entries(type_map)) {
            if (upper_type.includes(key)) {
                const data_type = Object.values(this.report_data.data_types).find(dt => dt.name === value);
                if (data_type) return data_type.id;
            }
        }

        // Default to string
        const string_type = Object.values(this.report_data.data_types).find(dt => dt.name === 'string');
        if (string_type) return string_type.id;

        // Ultimate fallback - return first available data type
        const first_type = Object.values(this.report_data.data_types)[0];
        if (first_type) return first_type.id;

        // This should never happen if data types are loaded properly
        console.error('No data types available!');
        return null;
    }

    get_default_variable_type(type) {
        const var_type = Object.values(this.report_data.variable_types).find(vt => vt.name === type);
        return var_type ? var_type.id : null;
    }


    show_error(message, selector = null) {
        if (selector) {
            // Show inline alert in specific element
            const html = `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
            $(selector).html(html);
        } else {
            // Use the real toast system
            if (window.showToast) {
                window.showToast(message, 'error');
            } else {
                console.error('Toast system not available:', message);
            }
        }
    }

    show_success(message, selector = null) {
        if (selector) {
            // Show inline alert in specific element
            const html = `<div class="alert alert-success alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
            $(selector).html(html);
        } else {
            // Use the real toast system
            if (window.showToast) {
                window.showToast(message, 'success');
            } else {
                console.log('Toast system not available:', message);
            }
        }
    }

    show_info(selector, message) {
        if (selector) {
            // Show inline alert in specific element
            $(selector).html(`<div class="alert alert-info alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`);
        } else {
            // Use the real toast system for general info
            if (window.showToast) {
                window.showToast(message, 'info');
            } else {
                console.log('Toast system not available:', message);
            }
        }
    }

    handle_action(action, id) {
        // First check for custom handlers (for backward compatibility)
        if (this.options.custom_handlers && this.options.custom_handlers[action]) {
            this.options.custom_handlers[action](id);
            return;
        }
        
        // Get action configuration
        const action_config = this.action_configs[action];
        if (!action_config) {
            console.error(`No configuration found for action: ${action}`);
            return;
        }
        
        // Handle confirmation if needed
        if (action_config.needs_confirmation) {
            const message = (action_config.confirmation_message || 'Are you sure?')
                .replace('{model}', this.model_name);
            if (!confirm(message)) {
                return;
            }
        }
        
        // Get URL from options or use pattern
        const url = this._get_action_url(action, action_config);
        if (!url) {
            console.error(`No URL configured for action: ${action}`);
            return;
        }
        
        // Prepare data
        const data = {};
        data[action_config.data_key || 'id'] = id;
        
        // Add any additional data from config
        if (action_config.additional_data) {
            Object.assign(data, action_config.additional_data);
        }
        
        // ALL actions use HTMX wrapper
        this.trigger_htmx_request({
            url: url,
            data: data,
            method: action_config.method || 'post',
            target: action_config.target || '#main-content',
            swap: action_config.swap || 'innerHTML',
            indicator: action_config.indicator || '.htmx-indicator',
            on_success: action_config.on_success,
            on_error: action_config.on_error
        });
    }
    
    _get_action_url(action, action_config) {
        // Priority order for URL resolution:
        // 1. Specific URL in options (e.g., edit_url, delete_url)
        // 2. URL in action_configs
        // 3. URL pattern in action_configs
        
        const option_url_key = `${action}_url`;
        if (this.options[option_url_key]) {
            return this.options[option_url_key];
        }
        
        if (action_config.url) {
            return action_config.url;
        }
        
        if (action_config.url_pattern && this.options.base_url) {
            return this.options.base_url + action_config.url_pattern
                .replace('{model}', this.model_name.toLowerCase());
        }
        
        return null;
    }
    
    // Helper method to reload the table
    reload() {
        if (this.table) {
            this.table.ajax.reload();
        }
    }
    
    // Allow adding custom actions dynamically
    register_action(name, config) {
        this.action_configs[name] = config;
    }

     // ===== ACTIONS MANAGEMENT =====
    
     init_actions() {
        // Initialize JavaScript editor for actions using CodeMirror
        this.javascript_editor = CodeMirror(document.getElementById('javascriptEditor'), {
            mode: 'javascript',
            theme: 'monokai',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: false,
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "Ctrl-Enter": () => this.save_action()
            }
        });
        
        // Event listeners for actions
        $('#addActionBtn').on('click', () => this.show_add_action());
        $('#saveActionBtn').on('click', () => this.save_action());
        $('#actionType').on('change', () => this.toggle_action_fields());
        $('#actionConfirm').on('change', () => this.toggle_confirm_message());
        
        // Load existing actions if editing
        if (this.report_id) {
            this.load_actions();
        }
    }
    
    async load_actions() {
        if (!this.report_id) return;
        
        try {
            const result = await window.app.api.post(this.urls.data_api, {
                model: 'PageAction',
                operation: 'list',
                filters: {
                    report_id: this.report_id
                },
                order_by: 'order_index'
            });
            
            if (result.success) {
                this.actions = result.data || [];
                this.render_actions();
            } else {
                console.error('Failed to load actions:', result.message);
            }
        } catch (error) {
            console.error('Failed to load actions:', error);
        }
    }
    
    render_actions() {
        const container = $('#actionsList');
        
        if (this.actions.length === 0) {
            container.html('<div class="text-muted">No actions defined.</div>');
            return;
        }
        
        const actions_html = this.actions
            .sort((a, b) => a.order_index - b.order_index)
            .map((action, index) => this.render_action_item(action, index))
            .join('');
            
        container.html(`<div class="action-items">${actions_html}</div>`);
        
        // Make sortable
        this.init_actions_sortable();
    }
    
    render_action_item(action, index) {
        const icon_html = action.icon ? `<i class="${action.icon}"></i> ` : '';
        const color_class = action.color ? `btn-${action.color}` : 'btn-secondary';
        const mode_badge = `<span class="badge bg-info">${action.mode}</span>`;
        const type_badge = `<span class="badge bg-secondary">${action.action_type}</span>`;
        
        return `
            <div class="action-item card mb-2" data-action-id="${action.id}" data-index="${index}">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-grip-vertical text-muted me-3 drag-handle" style="cursor: move;"></i>
                        <div>
                            <strong>${icon_html}${action.display}</strong>
                            <div class="small text-muted">
                                ${action.name} ${mode_badge} ${type_badge}
                                ${action.action_type !== 'javascript' ? `- ${action.method} ${action.url}` : '- JavaScript'}
                            </div>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary" onclick="window.reportBuilder.edit_action(${index})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="window.reportBuilder.delete_action(${index})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    init_actions_sortable() {
        $('.action-items').sortable({
            handle: '.drag-handle',
            update: (event, ui) => {
                this.update_action_order();
            }
        });
    }
    
    async update_action_order() {
        const items = $('.action-item');
        const order_updates = [];
        
        items.each((index, item) => {
            const action_index = $(item).data('index');
            this.actions[action_index].order_index = index;
            order_updates.push({
                id: this.actions[action_index].id,
                order_index: index
            });
        });
        
        // Save order to backend using batch update
        if (this.report_id && order_updates.length > 0) {
            try {
                for (const update of order_updates) {
                    await window.app.api.post(this.urls.data_api, {
                        model: 'PageAction',
                        operation: 'update',
                        id: update.id,
                        data: {
                            order_index: update.order_index
                        }
                    });
                }
            } catch (error) {
                console.error('Failed to update action order:', error);
            }
        }
    }
    
    show_add_action() {
        $('#actionModalTitle').text('Add Action');
        $('#actionForm')[0].reset();
        $('#actionId').val('');
        this.javascript_editor.setValue('');
        this.javascript_editor.clearHistory();
        this.toggle_action_fields();
        $('#actionModal').modal('show');
    }
    
    edit_action(index) {
        const action = this.actions[index];
        $('#actionModalTitle').text('Edit Action');
        $('#actionId').val(action.id || index);
        
        // Populate form
        $('#actionName').val(action.name);
        $('#actionDisplay').val(action.display);
        $('#actionMode').val(action.mode || 'row');
        $('#actionType').val(action.action_type);
        $('#actionIcon').val(action.icon || '');
        $('#actionColor').val(action.color || '');
        
        // URL fields
        $('#actionUrl').val(action.url || '');
        $('#actionUrlFor').val(action.url_for || '');
        $('#actionMethod').val(action.method || 'GET');
        $('#actionTarget').val(action.target || '_self');
        $('#actionHeaders').val(JSON.stringify(action.headers || {}, null, 2));
        $('#actionPayload').val(JSON.stringify(action.payload || {}, null, 2));
        
        // JavaScript
        this.javascript_editor.setValue(action.javascript_code || '');
        this.javascript_editor.clearHistory();
        
        // Confirmation
        $('#actionConfirm').prop('checked', action.confirm);
        $('#actionConfirmMessage').val(action.confirm_message || 'Are you sure you want to perform this action?');
        
        this.toggle_action_fields();
        this.toggle_confirm_message();
        $('#actionModal').modal('show');
    }
    
    save_action() {
        const action_id = $('#actionId').val();
        const is_edit = action_id !== '';
        
        // Validate form
        if (!$('#actionName').val() || !$('#actionDisplay').val()) {
            this.show_error('Name and Display Text are required');
            return;
        }
        
        // Validate based on type
        const action_type = $('#actionType').val();
        if (action_type !== 'javascript' && !$('#actionUrl').val()) {
            this.show_error('URL is required for HTMX and API actions');
            return;
        }
        
        if (action_type === 'javascript' && !this.javascript_editor.getValue().trim()) {
            this.show_error('JavaScript code is required for JavaScript actions');
            return;
        }
        
        // Validate JSON fields
        try {
            JSON.parse($('#actionHeaders').val());
            JSON.parse($('#actionPayload').val());
        } catch (e) {
            this.show_error('Invalid JSON in Headers or Payload fields');
            return;
        }
        
        // Build action object
        const action = {
            name: $('#actionName').val(),
            display: $('#actionDisplay').val(),
            mode: $('#actionMode').val(),
            action_type: action_type,
            icon: $('#actionIcon').val(),
            color: $('#actionColor').val(),
            url: $('#actionUrl').val(),
            url_for: $('#actionUrlFor').val(),
            method: $('#actionMethod').val(),
            target: $('#actionTarget').val(),
            headers: JSON.parse($('#actionHeaders').val()),
            payload: JSON.parse($('#actionPayload').val()),
            javascript_code: action_type === 'javascript' ? this.javascript_editor.getValue() : null,
            confirm: $('#actionConfirm').is(':checked'),
            confirm_message: $('#actionConfirmMessage').val()
        };
        
        if (is_edit) {
            // Update existing
            const index = this.actions.findIndex(a => (a.id || this.actions.indexOf(a)) == action_id);
            if (index !== -1) {
                action.id = this.actions[index].id;
                action.order_index = this.actions[index].order_index;
                this.actions[index] = action;
            }
        } else {
            // Add new
            action.order_index = this.actions.length;
            this.actions.push(action);
        }
        
        this.render_actions();
        $('#actionModal').modal('hide');
        this.mark_unsaved();
    }
    
    delete_action(index) {
        if (confirm('Are you sure you want to delete this action?')) {
            this.actions.splice(index, 1);
            this.render_actions();
            this.mark_unsaved();
        }
    }
    
    toggle_action_fields() {
        const action_type = $('#actionType').val();
        
        if (action_type === 'javascript') {
            $('#urlSection').hide();
            $('#javascriptSection').show();
            $('#actionUrl').prop('required', false);
        } else {
            $('#urlSection').show();
            $('#javascriptSection').hide();
            $('#actionUrl').prop('required', true);
        }
    }
    
    toggle_confirm_message() {
        if ($('#actionConfirm').is(':checked')) {
            $('#confirmMessageSection').show();
        } else {
            $('#confirmMessageSection').hide();
        }
    }
    
    // ===== END ACTIONS MANAGEMENT =====
    
   
    
    async save_all_actions() {
        try {
            // Delete existing actions first (to handle removals)
            if (this.report_id) {
                const existing = await window.app.api.post(this.urls.data_api, {
                    model: 'PageAction',
                    operation: 'list',
                    filters: { report_id: this.report_id }
                });
                
                if (existing.success && existing.data) {
                    for (const action of existing.data) {
                        await window.app.api.post(this.urls.data_api, {
                            model: 'PageAction',
                            operation: 'delete',
                            id: action.id
                        });
                    }
                }
            }
            
            // Create all current actions
            for (const action of this.actions) {
                const action_data = {
                    report_id: this.report_id,
                    name: action.name,
                    display: action.display,
                    mode: action.mode,
                    action_type: action.action_type,
                    icon: action.icon,
                    color: action.color,
                    url: action.url,
                    url_for: action.url_for,
                    method: action.method,
                    target: action.target,
                    headers: action.headers,
                    payload: action.payload,
                    javascript_code: action.javascript_code,
                    confirm: action.confirm,
                    confirm_message: action.confirm_message,
                    order_index: action.order_index
                };
                
                await window.app.api.post(this.urls.data_api, {
                    model: 'PageAction',
                    operation: 'create',
                    data: action_data
                });
            }
        } catch (error) {
            console.error('Failed to save actions:', error);
            throw error;
        }
    }
        
    mark_unsaved() {
        $('#saveReportBtn').removeClass('btn-success').addClass('btn-warning');
        $('#saveReportBtn').html('<i class="fas fa-save"></i> Save Changes');
    }

    async load_models() {
        try {
            console.log('Loading models...');
            
            const result = await window.app.api.post(this.urls.data_api, {
                model: 'Model',
                operation: 'list',
                order_by: 'name',
                length:0
            });

            if (result.success) {
                this.report_data.models = result.data;
                const select = $('#reportModel');
                select.empty().append('<option value="">None - Custom Query</option>');

                console.log('Loaded', result.data.length, 'models');

                result.data.forEach(model => {
                    // Display model name and optionally table name
                    const display_text = model.table_name ? `${model.name} (${model.table_name})` : model.name;
                    select.append(`<option value="${model.id}">${display_text}</option>`);
                });

                console.log('Models dropdown populated with', $('#reportModel option').length - 1, 'models');
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            this.show_error('Failed to load models');
        }
    }
    async load_model_query_with_confirmation(model_id) {
        if (!model_id) return;
        
        try {
            const model_result = await window.app.api.post(this.urls.data_api, {
                model: 'Model',
                operation: 'read',
                id: model_id
            });
            
            if (model_result.success && model_result.data) {
                const model = model_result.data;
                let new_query = '';
                
                // Build query based on model data
                if (model.default_query) {
                    new_query = model.default_query;
                } else if (model.table_name) {
                    // Generate a SELECT * query
                    new_query = `SELECT * FROM ${model.table_name}`;
                } else {
                    this.show_error('No query information available for this model');
                    return;
                }
                
                // Check if there's existing query content
                const current_query = this.query_editor.getValue().trim();
                
                if (current_query && current_query !== 'SELECT * FROM temuragi.public.users') {
                    // Has meaningful content, ask for confirmation
                    const message = `Replace current query with model query?\n\nCurrent:\n${current_query.substring(0, 100)}${current_query.length > 100 ? '...' : ''}\n\nNew:\n${new_query.substring(0, 100)}${new_query.length > 100 ? '...' : ''}`;
                    
                    if (confirm(message)) {
                        this.query_editor.setValue(new_query);
                        this.query_editor.refresh();
                        
                        // Auto-detect columns for the new query
                        if (confirm('Auto-detect columns for this model query?')) {
                            await this.test_query_with_metadata();
                        }
                    } else {
                        // User cancelled, revert model selection
                        $('#reportModel').val('');
                    }
                } else {
                    // No meaningful content, just set the query
                    this.query_editor.setValue(new_query);
                    this.query_editor.refresh();
                    
                    // Auto-detect columns
                    await this.test_query_with_metadata();
                }
            }
        } catch (error) {
            console.error('Failed to load model details:', error);
            this.show_error('Failed to load model query: ' + error.message);
        }
    }

    
}

// Event delegation for dynamically created elements
$(document).on('change', '.column-item input, .column-item select', function() {
    const field = $(this).data('field');
    const index = $(this).data('index');
    const value = $(this).is(':checkbox') ? $(this).is(':checked') : $(this).val();

    if (window.reportBuilder) {
        window.reportBuilder.update_column(index, field, value);
    }
});

$(document).on('click', '.remove-column-btn', function() {
    const index = $(this).data('index');
    if (window.reportBuilder) {
        window.reportBuilder.remove_column(index);
    }
});

$(document).on('change', '.variable-item input, .variable-item select', function() {
    const field = $(this).data('field');
    const index = $(this).data('index');
    const value = $(this).is(':checkbox') ? $(this).is(':checked') : $(this).val();

    if (window.reportBuilder) {
        window.reportBuilder.update_variable(index, field, value);
    }
});

$(document).on('click', '.remove-variable-btn', function() {
    const index = $(this).data('index');
    if (window.reportBuilder) {
        window.reportBuilder.remove_variable(index);
    }
});

// Delegate new metadata button clicks
$(document).on('click', '#analyzeColumnsBtn', function() {
    if (window.reportBuilder) {
        window.reportBuilder.analyze_columns_from_query();
    }
});

$(document).on('click', '#syncColumnsBtn', function() {
    if (window.reportBuilder) {
        window.reportBuilder.sync_columns_from_query();
    }
});

$(document).on('click', '#autoDetectTypesBtn', function() {
    if (window.reportBuilder) {
        window.reportBuilder.auto_detect_column_types();
    }
});