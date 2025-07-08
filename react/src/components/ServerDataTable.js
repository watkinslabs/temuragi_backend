import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigation } from '../App';
import { useSite } from '../contexts/SiteContext';
import config from '../config';


const ServerDataTable = ({
    // Simple mode - just pass report_id
    report_id,
    model_name,
    api_url,
    options = {},

    // Additional props
    on_config_loaded = null,
    overrides = {}
}) => {
    // State
    const [loading, set_loading] = useState(false);
    const [initial_loading, set_initial_loading] = useState(true);
    const [config_loading, set_config_loading] = useState(true);
    const [table_config, set_table_config] = useState(null);
    const [data, set_data] = useState([]);
    const [total_records, set_total_records] = useState(0);
    const [filtered_records, set_filtered_records] = useState(0);
    const [current_page, set_current_page] = useState(1);
    const [page_size, set_page_size] = useState(25);
    const [search_term, set_search_term] = useState('');
    const [sort_config, set_sort_config] = useState({ column: null, direction: null });
    const [error, set_error] = useState(null);

    // Refs
    const search_input_ref = useRef(null);

    // Hooks
    const { navigate_to } = useNavigation();
    const { current_context } = useSite();

    // Load table configuration from server
    const load_table_config = async () => {
        if (!report_id) {
            // If no report_id, we're in manual mode
            set_table_config({
                model_name: model_name,
                report_name: report_id || model_name?.toLowerCase(),
                api_url: api_url || '/v2/api/data',
                page_length: 25,
                show_search: true,
                show_column_search: false,
                columns: {},
                excluded_columns: ['password_hash', 'created_by', 'updated_by', 'deleted_at'],
                actions: [],
                table_title: null,
                table_description: null,
                report_id: null,
                is_model: true,
                custom_options: {
                    cache_enabled: false,
                    refresh_interval: 0,
                    row_limit: 10000
                },
                ...options,
                ...overrides
            });
            set_config_loading(false);
            return;
        }

        try {
            set_config_loading(true);

            // Fetch report configuration
            const response = await config.apiCall('/v2/api/reports/config', {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({
                    report_id: report_id,
                    context: current_context
                })
            });

            if (!response.ok) {
                throw new Error('Failed to load report configuration');
            }

            const response_data = await response.json();

            // Handle nested data structure
            const config_data = response_data.data && response_data.data.config
                ? response_data.data
                : response_data;

            if (config_data.success || (response_data.data && response_data.data.success)) {
                // Extract config from proper location
                const server_config = config_data.config || response_data.data.config;

                // Merge server config with any overrides
                const merged_config = {
                    ...server_config,
                    ...overrides,
                    columns: {
                        ...server_config.columns,
                        ...(overrides.columns || {})
                    },
                    actions: [
                        ...(server_config.actions || []),
                        ...(overrides.extra_actions || [])
                    ]
                };

                set_table_config(merged_config);
                set_page_size(merged_config.page_length || 25);

                // Callback if provided
                if (on_config_loaded) {
                    on_config_loaded(merged_config);
                }
            } else {
                throw new Error(config_data.error || 'Invalid configuration received');
            }
        } catch (error) {
            console.error('Failed to load table configuration:', error);
            set_error(`Failed to load table configuration: ${error.message}`);
        } finally {
            set_config_loading(false);
        }
    };

    // Load config on mount or when report_id changes
    useEffect(() => {
        load_table_config();
    }, [report_id, current_context]);

    // API request helper
    const make_api_request = async (operation, additional_data = {}) => {
        if (!table_config) return;

        // When report_id exists, use ReportHandler as the model
        const model_to_use = table_config.report_id ? 'ReportHandler' : table_config.model_name;

        const base_data = {
            model: model_to_use,
            operation: operation
        };

        if (table_config.report_id !== null) {
            base_data.report_id = table_config.report_id;
        }
        if (table_config.is_model !== null) {
            base_data.is_model = table_config.is_model;
        }
        if (current_context) {
            base_data.context = current_context;
        }

        const request_data = {
            ...base_data,
            ...additional_data
        };

        try {
            const response = await config.apiCall(table_config.api_url || '/api/data', {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify(request_data)
            });

            if (!response.ok) {
                throw new Error(`API request failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed for operation '${operation}':`, error);
            throw error;
        }
    };

    // Get ordered columns
    const get_ordered_columns = () => {
        if (!table_config?.columns) return [];

        return Object.entries(table_config.columns)
            .sort(([a, conf_a], [b, conf_b]) => {
                return (conf_a.order_index || 999) - (conf_b.order_index || 999);
            })
            .map(([name, config]) => ({ name, ...config }));
    };

    // Get searchable columns
    const get_searchable_columns = () => {
        if (!table_config?.columns) return [];

        return Object.entries(table_config.columns)
            .filter(([name, config]) => config.searchable === true)
            .map(([name]) => name);
    };

    // Get actions by type
    const get_page_actions = () => {
        if (!table_config?.actions) return [];
        return table_config.actions.filter(action => action.mode === 'page');
    };

    const get_row_actions = () => {
        if (!table_config?.actions) return [];
        return table_config.actions.filter(action => !action.mode || action.mode === 'row');
    };

    // Load data
    const load_data = useCallback(async () => {
        if (!table_config) return;

        set_loading(true);
        set_error(null);

        try {
            const ordered_columns = get_ordered_columns();
            const searchable_columns = get_searchable_columns();
            const row_actions = get_row_actions();

            // Build columns for API (matching DataTables format)
            const all_columns = ordered_columns.map((col, index) => ({
                data: col.name,
                name: col.name,
                searchable: col.searchable || false,
                orderable: col.orderable !== false,
                search: { value: '', regex: false }
            }));

            // Add actions column if needed
            if (row_actions.length > 0) {
                all_columns.push({
                    data: null,
                    name: 'actions',
                    searchable: false,
                    orderable: false,
                    search: { value: '', regex: false }
                });
            }

            // DataTables-style order array
            const order = sort_config.column ? [{
                column: ordered_columns.findIndex(col => col.name === sort_config.column),
                dir: sort_config.direction || 'asc'
            }] : [];

            // Apply row limit from custom_options if present
            const row_limit = table_config.custom_options?.row_limit || 10000;
            const effective_page_size = Math.min(page_size, row_limit);

            const response = await make_api_request('list', {
                draw: 1,
                start: (current_page - 1) * effective_page_size,
                length: effective_page_size,
                search: search_term,
                order: order,
                columns: all_columns,
                return_columns: ordered_columns.map(col => col.name),
                searchable_columns: searchable_columns
            });

            if (response.success) {
                set_data(response.data || []);
                set_total_records(response.recordsTotal || 0);
                set_filtered_records(response.recordsFiltered || response.recordsTotal || 0);
                set_initial_loading(false);
            } else {
                throw new Error(response.error || 'Failed to load data');
            }
        } catch (error) {
            console.error('Failed to load table data:', error);
            set_error(error.message);
            set_data([]);
        } finally {
            set_loading(false);
        }
    }, [current_page, page_size, search_term, sort_config, table_config]);

    // Load data when config is ready and dependencies change
    useEffect(() => {
        if (table_config && !config_loading) {
            load_data();
        }
    }, [load_data, table_config, config_loading]);

    // Handle sorting
    const handle_sort = (column_name) => {
        set_sort_config(prev => {
            if (prev.column === column_name) {
                return {
                    column: column_name,
                    direction: prev.direction === 'asc' ? 'desc' : 'asc'
                };
            } else {
                return { column: column_name, direction: 'asc' };
            }
        });
        set_current_page(1);
    };

    // Handle search
    const handle_search = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            set_search_term(e.target.value);
            set_current_page(1);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.target.value = '';
            set_search_term('');
            set_current_page(1);
        }
    };

    // Handle pagination
    const total_pages = Math.ceil(filtered_records / page_size) || 1;

    const go_to_page = (page) => {
        if (page >= 1 && page <= total_pages) {
            set_current_page(page);
        }
    };

    // Handle actions
    const handle_action = async (action, row_id = null) => {
        console.log('handle_action called:', { action, row_id, action_type: action.action_type });
        
        if (action.confirm && !window.confirm(action.confirm_message || action.confirm)) {
            return;
        }

        const action_type = action.action_type || 'api';

        switch (action_type) {
            case 'javascript':
                handle_javascript_action(action, row_id);
                break;

            case 'navigate':
                handle_navigate_action(action, row_id);
                break;

            case 'htmx':
                handle_htmx_action(action, row_id);
                break;

            case 'api':
            default:
                await handle_api_action(action, row_id);
                break;
        }
    };

    const handle_javascript_action = (action, row_id) => {
        if (action.javascript) {
            try {
                const func = new Function('id', 'row_data', 'table', 'action', action.javascript);
                const row_data = row_id ? data.find(row => row.id === row_id) : null;
                func.call(this, row_id, row_data, { reload: load_data }, action);
            } catch (error) {
                console.error('Error executing JavaScript action:', error);
                window.showToast?.('Error executing action', 'error');
            }
        }
    };

    const handle_navigate_action = (action, row_id) => {
        console.log('handle_navigate_action called:', { action, row_id });
        
        const view = action.view || action.url?.replace(/^\//, '') || 'home';
        const params = { ...action.params };

        if (row_id) {
            params.id = row_id;
        }

        console.log('Navigating to:', { view, params });
        navigate_to(view, params);
    };

    const handle_htmx_action = (action, row_id) => {
        // Create a form and submit it for HTMX-style navigation
        const form = document.createElement('form');
        form.method = action.method || 'POST';
        form.action = action.url;

        // Add row_id if present
        if (row_id) {
            const id_input = document.createElement('input');
            id_input.type = 'hidden';
            id_input.name = 'id';
            id_input.value = row_id;
            form.appendChild(id_input);
        }

        // Add any payload data
        if (action.payload) {
            Object.entries(action.payload).forEach(([key, value]) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = key;
                input.value = value;
                form.appendChild(input);
            });
        }

        // Add custom headers as hidden fields if needed
        if (action.headers) {
            Object.entries(action.headers).forEach(([key, value]) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = `_header_${key}`;
                input.value = value;
                form.appendChild(input);
            });
        }

        document.body.appendChild(form);
        form.submit();
    };

    const handle_api_action = async (action, row_id) => {
        try {
            // When report_id exists, use ReportHandler as the model
            const model_to_use = table_config.report_id ? 'ReportHandler' : table_config.model_name;

            const request_data = {
                id: row_id,
                model: model_to_use,
                ...(action.payload || {})
            };

            if (table_config.report_id !== null) {
                request_data.report_id = table_config.report_id;
            }

            const method = (action.method || 'POST').toLowerCase();
            const response = await config.apiCall(action.url || table_config.api_url, {
                method: method.toUpperCase(),
                headers: {
                    ...config.getAuthHeaders(),
                    ...(action.headers || {})
                },
                body: JSON.stringify(request_data)
            });

            const result = await response.json();

            if (result.success) {
                window.showToast?.(result.message || `${action.title || action.name} completed`, 'success');

                if (result.reload_table !== false) {
                    load_data();
                }
            } else {
                window.showToast?.(result.error || `${action.title || action.name} failed`, 'error');
            }
        } catch (error) {
            console.error('API action failed:', error);
            window.showToast?.(`Failed to execute ${action.title || action.name}`, 'error');
        }
    };

    // Format date based on format string
    const format_date = (value, format_string) => {
        if (!value) return '';

        const date = new Date(value);

        // Handle common date format patterns
        if (format_string) {
            // Simple replacement for common patterns
            let formatted = format_string;

            // Year
            formatted = formatted.replace('%Y', date.getFullYear());
            formatted = formatted.replace('%y', String(date.getFullYear()).slice(-2));

            // Month
            formatted = formatted.replace('%m', String(date.getMonth() + 1).padStart(2, '0'));
            formatted = formatted.replace('%B', date.toLocaleDateString('en-US', { month: 'long' }));
            formatted = formatted.replace('%b', date.toLocaleDateString('en-US', { month: 'short' }));

            // Day
            formatted = formatted.replace('%d', String(date.getDate()).padStart(2, '0'));

            // Hour
            formatted = formatted.replace('%H', String(date.getHours()).padStart(2, '0'));
            formatted = formatted.replace('%I', String(date.getHours() % 12 || 12).padStart(2, '0'));

            // Minute
            formatted = formatted.replace('%M', String(date.getMinutes()).padStart(2, '0'));

            // Second
            formatted = formatted.replace('%S', String(date.getSeconds()).padStart(2, '0'));

            // AM/PM
            formatted = formatted.replace('%p', date.getHours() >= 12 ? 'PM' : 'AM');

            return formatted;
        }

        // Default formatting
        return date.toLocaleDateString();
    };

    // Render column value
    const render_column_value = (column, value, row) => {
        // Custom renderer
        if (column.render) {
            // If render is a string, it might be a function name or template
            if (typeof column.render === 'string') {
                // Handle template syntax like "{{value}}" or function references
                return value || '';
            }
            return column.render(value, row);
        }

        // Handle date formatting with format string
        if (column.type === 'datetime' || (column.format && column.format.includes('%'))) {
            return format_date(value, column.format);
        }

        // Type-based rendering
        if (column.format === 'boolean' || column.type === 'boolean') {
            return value ?
                <span className="badge bg-success">Yes</span> :
                <span className="badge bg-secondary">No</span>;
        }

        if (column.format === 'currency') {
            return `$${new Intl.NumberFormat().format(value || 0)}`;
        }

        if (column.format === 'number') {
            return new Intl.NumberFormat().format(value || 0);
        }

        if (column.format === 'percent') {
            return `${(value * 100).toFixed(1)}%`;
        }

        // Default
        return value || '';
    };

    // Get alignment class
    const get_alignment_class = (alignment) => {
        switch (alignment) {
            case 'center':
                return 'text-center';
            case 'right':
                return 'text-end';
            case 'left':
            default:
                return 'text-start';
        }
    };

    // Loading state
    if (config_loading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                <div className="text-center">
                    <div className="spinner-border text-primary mb-3" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p>Loading table configuration...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (!table_config && !config_loading) {
        return (
            <div className="alert alert-danger">
                Failed to load table configuration
            </div>
        );
    }

    // Calculate pagination range
    const get_pagination_range = () => {
        const delta = 2;
        const range = [];
        const range_with_dots = [];
        let l;

        for (let i = 1; i <= total_pages; i++) {
            if (i === 1 || i === total_pages || (i >= current_page - delta && i <= current_page + delta)) {
                range.push(i);
            }
        }

        range.forEach((i) => {
            if (l) {
                if (i - l === 2) {
                    range_with_dots.push(l + 1);
                } else if (i - l !== 1) {
                    range_with_dots.push('...');
                }
            }
            range_with_dots.push(i);
            l = i;
        });

        return range_with_dots;
    };

    // Main render
    const ordered_columns = get_ordered_columns();
    const page_actions = get_page_actions();
    const row_actions = get_row_actions();
    const title = table_config.table_title || `${table_config.model_name} Management`;
    const description = table_config.table_description || `Manage ${table_config.model_name?.toLowerCase()} records`;

    return (
        <div id={table_config.container_id || `${table_config.report_name}_table`} className={table_config.is_wide ? 'container-fluid' : ''}>
            <style>{`
                .table-wrapper {
                    position: relative;
                }

                .table-loading th .fas.fa-sort-up,
                .table-loading th .fas.fa-sort-down {
                    animation: pulse 1s infinite;
                }

                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
            `}</style>

            {/* Header */}
            <div className="row mb-4">
                <div className="col">
                    <div className="d-flex justify-content-between align-items-center">
                        <div>
                            <h4 className="mb-0 fw-bold">
                                <i className="fas fa-table me-2"></i>{title}
                            </h4>
                            <small className="text-body-secondary">{description}</small>
                        </div>

                        {page_actions.length > 0 && (
                            <div className="btn-group">
                                {page_actions.map(action => (
                                    <button
                                        key={action.name}
                                        className={`btn btn-${action.color || 'secondary'}`}
                                        onClick={() => handle_action(action)}
                                    >
                                        <i className={`${action.icon} me-2`}></i>
                                        {action.title || action.name}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Search Bar */}
            {table_config.show_search && (
                <div className="row mb-4">
                    <div className="col-md-4">
                        <input
                            ref={search_input_ref}
                            type="text"
                            className="form-control"
                            placeholder={`Search ${table_config.model_name?.toLowerCase()}s...`}
                            onKeyDown={handle_search}
                        />
                    </div>
                </div>
            )}

            {/* Table */}
            <div className="row">
                <div className="col">
                    <div className="card">
                        <div className="card-body">
                            {error && (
                                <div className="alert alert-danger">{error}</div>
                            )}

                            <div className="table-responsive table-wrapper">
                                <table className={`table table-hover ${loading && !initial_loading ? 'table-loading' : ''}`}>
                                    <thead>
                                        <tr>
                                            {ordered_columns.map(column => (
                                                <th
                                                    key={column.name}
                                                    className={get_alignment_class(column.alignment)}
                                                    style={{
                                                        cursor: column.orderable !== false ? 'pointer' : 'default',
                                                        width: column.width || 'auto'
                                                    }}
                                                    onClick={() => column.orderable !== false && handle_sort(column.name)}
                                                >
                                                    {column.label || column.name}
                                                    {column.orderable !== false && (
                                                        <span className="ms-1">
                                                            {sort_config.column === column.name ? (
                                                                <i className={`fas fa-sort-${sort_config.direction === 'asc' ? 'up' : 'down'}`}></i>
                                                            ) : (
                                                                <i className="fas fa-sort text-muted"></i>
                                                            )}
                                                        </span>
                                                    )}
                                                </th>
                                            ))}
                                            {row_actions.length > 0 && <th className="text-center">Actions</th>}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {initial_loading ? (
                                            <tr>
                                                <td colSpan={ordered_columns.length + (row_actions.length > 0 ? 1 : 0)} className="text-center py-4">
                                                    <div className="spinner-border spinner-border-sm me-2" role="status">
                                                        <span className="visually-hidden">Loading...</span>
                                                    </div>
                                                    Loading data...
                                                </td>
                                            </tr>
                                        ) : data.length === 0 ? (
                                            <tr>
                                                <td colSpan={ordered_columns.length + (row_actions.length > 0 ? 1 : 0)} className="text-center py-4">
                                                    No records found
                                                </td>
                                            </tr>
                                        ) : (
                                            data.map((row, row_index) => (
                                                <tr key={row.id || row_index}>
                                                    {ordered_columns.map(column => (
                                                        <td key={column.name} className={get_alignment_class(column.alignment)}>
                                                            {render_column_value(column, row[column.name], row)}
                                                        </td>
                                                    ))}
                                                    {row_actions.length > 0 && (
                                                        <td className="text-center">
                                                            <div className="btn-group btn-group-sm">
                                                                {row_actions.map(action => (
                                                                    <button
                                                                        key={action.name}
                                                                        className={`btn btn-${action.color || 'secondary'}`}
                                                                        onClick={() => handle_action(action, row.id)}
                                                                        title={action.title || action.name}
                                                                    >
                                                                        <i className={action.icon}></i>
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </td>
                                                    )}
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination and Info */}
                            {table_config.show_pagination !== false && (
                                <div className="d-flex justify-content-between align-items-center mt-3">
                                    <div className="text-muted">
                                        Showing {((current_page - 1) * page_size) + 1} to{' '}
                                        {Math.min(current_page * page_size, filtered_records)} of{' '}
                                        {filtered_records} entries
                                        {filtered_records !== total_records && ` (filtered from ${total_records} total entries)`}
                                    </div>

                                    {total_pages > 1 && (
                                        <nav>
                                            <ul className="pagination mb-0">
                                                <li className={`page-item ${current_page === 1 ? 'disabled' : ''}`}>
                                                    <button
                                                        className="page-link"
                                                        onClick={() => go_to_page(current_page - 1)}
                                                        disabled={current_page === 1}
                                                    >
                                                        Previous
                                                    </button>
                                                </li>

                                                {get_pagination_range().map((page, index) => (
                                                    <li
                                                        key={index}
                                                        className={`page-item ${page === current_page ? 'active' : ''} ${page === '...' ? 'disabled' : ''}`}
                                                    >
                                                        {page === '...' ? (
                                                            <span className="page-link">...</span>
                                                        ) : (
                                                            <button
                                                                className="page-link"
                                                                onClick={() => go_to_page(page)}
                                                            >
                                                                {page}
                                                            </button>
                                                        )}
                                                    </li>
                                                ))}

                                                <li className={`page-item ${current_page === total_pages ? 'disabled' : ''}`}>
                                                    <button
                                                        className="page-link"
                                                        onClick={() => go_to_page(current_page + 1)}
                                                        disabled={current_page === total_pages}
                                                    >
                                                        Next
                                                    </button>
                                                </li>
                                            </ul>
                                        </nav>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ServerDataTable;