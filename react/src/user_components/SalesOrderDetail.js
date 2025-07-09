/**
 * @routes ["SalesOrderDetail"]
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
    Search, Plus, MessageSquare, Trash2, Save, X, Copy, 
    Package, User, Truck, CreditCard, FileText, AlertCircle,
    Check, Edit2, ArrowLeft, Printer
} from 'lucide-react';

// Main Sales Order Component
const SalesOrderDetail = () => {
    // Get config from props or window
    const config = window.config || {};
    
    // Get navigation hook at the top level
    const navigation = window.useNavigation ? window.useNavigation() : null;
    const view_params = navigation?.view_params || {};
    
    // Merge config with view_params
    const merged_config = {
        ...config,
        ...view_params,
        company: config.company || 'PACIFIC',
        data_api: config.data_api || '/v2/api/data'
    };

    // Determine mode
    const is_view_mode = merged_config.mode === 'view';
    const is_edit_mode = merged_config.mode === 'edit';
    const so_number_param = merged_config.so_number || null;
    const is_new_so = !so_number_param || so_number_param === 'NEW';

    // Core state
    const [loading, setLoading] = useState(false);
    const [loading_message, setLoadingMessage] = useState('');
    const [mode, setMode] = useState(is_view_mode ? 'view' : (is_edit_mode ? 'edit' : 'create'));
    const [toast, setToast] = useState(null);

    // SO Data state
    const [so_number, setSoNumber] = useState(is_new_so ? null : so_number_param);
    const [customer, setCustomer] = useState(null);
    const [header, setHeader] = useState(get_default_header(merged_config));
    const [lines, setLines] = useState([]);
    const [order_status, setOrderStatus] = useState('OPEN');

    // API configuration
    const api_call = async (operation, model, params = {}) => {
        const request_data = {
            operation: operation,
            model: model,
            company: merged_config.company,
            ...params
        };

        if (window.app?.api?.post) {
            return await window.app.api.post(merged_config.data_api, request_data);
        } else {
            try {
                const response = await fetch(merged_config.data_api, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...config.getAuthHeaders?.()
                    },
                    body: JSON.stringify(request_data)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API call failed:', error);
                return { success: false, error: error.message };
            }
        }
    };

    // Initialize component
    useEffect(() => {
        const init = async () => {
            if (!is_new_so) {
                await load_existing_so();
            }
        };
        init();
    }, []);

    // Load existing SO
    const load_existing_so = async () => {
        if (!so_number) return;
        
        setLoading(true);
        setLoadingMessage('Loading sales order...');

        try {
            const result = await api_call('get', 'SalesOrder', {
                so_number: so_number,
                company: merged_config.company
            });

            if (result.success) {
                // Map the data with human-readable values
                const mapped_header = map_header_data(result.header || {});
                setHeader(mapped_header);
                setLines(result.lines || []);
                
                // Set order status
                setOrderStatus(result.header?.order_status || 'OPEN');
                
                // Load customer info - prioritize customer_info in header
                if (result.header?.customer_info) {
                    setCustomer(result.header.customer_info);
                } else if (result.header?.customer_code) {
                    await load_customer_details(result.header.customer_code);
                }
            } else {
                show_error('Failed to load sales order: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading SO:', error);
            show_error('Failed to load sales order');
        } finally {
            setLoading(false);
        }
    };

    // Customer handling
    const load_customer_details = async (customer_code) => {
        if (!customer_code) return;
        
        try {
            const model = customer_code >= 7000000 ? 'GCANADA_dbo_BKARCUST' : 'GPACIFIC_dbo_BKARCUST';
            const result = await api_call('list', model, {
                filters: {
                    code: {
                        operator: "eq",
                        value: customer_code
                    }
                },
                start: 0,
                length: 1
            });

            if (result.success && result.data && result.data.length > 0) {
                setCustomer(result.data[0]);
                return result.data[0];
            }
        } catch (error) {
            console.error('Error loading customer details:', error);
        }
        return null;
    };

    // Save SO
    const save_so = async () => {
        if (!validate_so()) return;

        setLoading(true);
        setLoadingMessage('Saving sales order...');

        try {
            const save_data = {
                customer_id: header.customer_code,
                location: header.location,
                admin_id: header.admin_id || 1, // Would need to get actual admin ID
                shipping: {
                    address: header.shipping,
                    attention: header.shipping.attention,
                    via_id: header.ship_via_id || 0
                },
                billing: {
                    address: header.billing
                },
                payment: {
                    terms: header.terms,
                    cod: header.cod || 'N'
                },
                lines: lines.filter(line => line.type !== 'X').map(line => ({
                    part: line.part,
                    quantity: line.quantity,
                    price: line.price,
                    list_price: line.list_price || 0,
                    discount: line.discount || 0,
                    vendor: line.vendor || '',
                    freight: line.freight || 0,
                    taxable: line.taxable ? 'Y' : 'N'
                })),
                notes: lines.filter(line => line.type === 'X').map(line => line.message),
                custom_po: header.custom_po || '',
                taxable: header.taxable ? 'Y' : 'N',
                freight: header.freight || 0
            };

            const result = await api_call('create', 'SalesOrder', save_data);

            if (result.success) {
                show_toast('Sales order saved successfully!', 'success');
                setSoNumber(result.so_number);
                setMode('view');
                
                // Reload to get the saved data
                await load_existing_so();
            } else {
                show_toast(result.error || 'Failed to save sales order', 'error');
            }
        } catch (error) {
            console.error('Error saving SO:', error);
            show_toast('Failed to save sales order', 'error');
        } finally {
            setLoading(false);
        }
    };

    // Validation
    const validate_so = () => {
        const errors = [];

        if (!header.customer_code) {
            errors.push('Please select a customer');
        }

        if (lines.filter(l => l.type !== 'X').length === 0) {
            errors.push('At least one line item is required');
        }

        if (errors.length > 0) {
            show_error('Please fix the following errors:\n' + errors.join('\n'));
            return false;
        }

        return true;
    };

    // Utility functions
    const show_error = (message) => {
        show_toast(message, 'error');
    };

    const show_toast = (message, type = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 5000);
    };

    // Calculations
    const totals = useMemo(() => {
        let subtotal = 0;
        let total_freight = 0;

        lines.forEach(line => {
            if (line.type !== 'X') {
                subtotal += line.extended || 0;
                total_freight += (line.freight || 0) * (line.quantity || 0);
            }
        });

        const order_freight = parseFloat(header.freight || 0);
        const tax_amount = parseFloat(header.tax_amount || 0);
        const total = subtotal + tax_amount + order_freight + total_freight;

        return { subtotal, order_freight, total_freight, tax_amount, total };
    }, [lines, header.freight, header.tax_amount]);

    // Mode badge component
    const ModeBadge = () => {
        const badge_config = {
            view: { color: 'secondary', text: 'VIEW ONLY', icon: FileText },
            edit: { color: 'warning', text: 'EDIT MODE', icon: Edit2 },
            create: { color: 'success', text: 'NEW ORDER', icon: Plus }
        };

        const config = badge_config[mode];
        const Icon = config.icon;

        return (
            <span className={`badge bg-${config.color} d-inline-flex align-items-center`}>
                <Icon size={14} className="me-1" />
                {config.text}
            </span>
        );
    };

    // Order Status badge component
    const OrderStatusBadge = ({ status }) => {
        const status_config = {
            OPEN: { color: 'primary', icon: Package },
            PRINTED: { color: 'warning', icon: Printer },
            POSTED: { color: 'success', icon: Check }
        };

        const config = status_config[status] || { color: 'secondary', icon: FileText };
        const Icon = config.icon;

        return (
            <span className={`badge bg-${config.color} d-inline-flex align-items-center ms-2`}>
                <Icon size={14} className="me-1" />
                {status}
            </span>
        );
    };

    // Component methods
    function add_line() {
        const new_line = {
            type: 'R',
            part: '',
            description: '',
            quantity: 1,
            price: 0,
            list_price: 0,
            discount: 0,
            extended: 0,
            freight: 0,
            taxable: false,
            message: ''
        };
        setLines(prev => [...prev, new_line]);
    }

    function add_note_line() {
        const new_note = {
            type: 'X',
            message: '',
            part: '',
            description: '',
            quantity: 0,
            price: 0,
            extended: 0
        };
        setLines(prev => [...prev, new_note]);
    }

    function remove_line(index) {
        if (confirm('Remove this line?')) {
            setLines(prev => prev.filter((_, i) => i !== index));
        }
    }

    function update_line(index, field, value) {
        setLines(prev => {
            const updated = [...prev];
            const line = { ...updated[index] };
            
            line[field] = value;
            
            // Recalculate extended if needed
            if (line.type !== 'X' && ['quantity', 'price', 'discount'].includes(field)) {
                const qty = parseFloat(line.quantity || 0);
                const price = parseFloat(line.price || 0);
                const discount = parseFloat(line.discount || 0);
                
                line.extended = qty * (price - discount);
            }
            
            updated[index] = line;
            return updated;
        });
    }

    return (
        <div className="container-fluid mt-2">
            {loading && (
                <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                     style={{ background: 'rgba(0,0,0,0.5)', zIndex: 9999 }}>
                    <div className="text-center text-white">
                        <div className="spinner-border text-light mb-2" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                        <div>{loading_message || 'Loading...'}</div>
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {toast && (
                <div 
                    className={`position-fixed top-0 start-50 translate-middle-x mt-3 alert alert-${toast.type === 'error' ? 'danger' : toast.type} alert-dismissible`}
                    style={{ zIndex: 10000, minWidth: '300px' }}
                >
                    {toast.message}
                    <button 
                        type="button" 
                        className="btn-close" 
                        onClick={() => setToast(null)}
                    ></button>
                </div>
            )}

            {/* Header with badges */}
            <div className="d-flex justify-content-between align-items-center mb-3">
                <div className="d-flex align-items-center flex-wrap">
                    <h4 className="mb-0 me-3">
                        Sales Order
                        {so_number && <span className="ms-2">#{so_number}</span>}
                    </h4>
                    <ModeBadge />
                    {so_number && <OrderStatusBadge status={order_status} />}
                </div>
                
                {/* Action buttons for view mode */}
                {mode === 'view' && !is_view_mode && (
                    <div>
                        <button 
                            className="btn btn-primary btn-sm"
                            onClick={() => setMode('edit')}
                        >
                            <Edit2 size={16} className="me-1" />
                            Edit Order
                        </button>
                    </div>
                )}
            </div>

            {/* Compact header section */}
            <div className="row g-2 mb-3">
                {/* Customer & Order Info */}
                <div className="col-lg-4">
                    <div className="card h-100">
                        <div className="card-header py-2">
                            <h6 className="mb-0 d-flex align-items-center">
                                <User size={16} className="me-2" />
                                Customer Information
                            </h6>
                        </div>
                        <div className="card-body p-2">
                            <CustomerSection
                                customer={customer}
                                customer_code={header.customer_code}
                                onCustomerChange={(cust) => {
                                    setCustomer(cust);
                                    setHeader(prev => ({
                                        ...prev,
                                        customer_code: cust?.code || '',
                                        billing: {
                                            name: cust?.name || '',
                                            address1: cust?.add1 || '',
                                            address2: cust?.add2 || '',
                                            city: cust?.city || '',
                                            state: cust?.state || '',
                                            zip: cust?.zip_ || '',
                                            country: cust?.country || 'USA'
                                        }
                                    }));
                                }}
                                api_call={api_call}
                                readonly={mode === 'view'}
                            />
                            
                            {customer && (
                                <div className="mt-2 pt-2 border-top">
                                    <div className="small">
                                        <div className="mb-1">
                                            <span className="text-muted">Terms:</span>
                                            <strong className="ms-1">{header.terms_desc || 'N/A'}</strong>
                                        </div>
                                        <div className="mb-1">
                                            <span className="text-muted">Phone:</span>
                                            <strong className="ms-1">{format_phone(customer.phone || customer.telephone)}</strong>
                                        </div>
                                        <div>
                                            <span className="text-muted">Sales Person:</span>
                                            <strong className="ms-1">{header.sales_person_name || 'N/A'}</strong>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Order Details */}
                <div className="col-lg-4">
                    <div className="card h-100">
                        <div className="card-header py-2">
                            <h6 className="mb-0 d-flex align-items-center">
                                <Package size={16} className="me-2" />
                                Order Details
                            </h6>
                        </div>
                        <div className="card-body p-2">
                            <div className="row g-2">
                                <div className="col-6">
                                    <label className="form-label small mb-1">Order Date</label>
                                    <input
                                        type="date"
                                        className="form-control form-control-sm"
                                        value={header.order_date}
                                        readOnly
                                    />
                                </div>
                                <div className="col-6">
                                    <label className="form-label small mb-1">Ship Date</label>
                                    <input
                                        type="date"
                                        className="form-control form-control-sm"
                                        value={header.ship_date || ''}
                                        onChange={(e) => setHeader(prev => ({ ...prev, ship_date: e.target.value }))}
                                        readOnly={mode === 'view'}
                                    />
                                </div>
                                <div className="col-6">
                                    <label className="form-label small mb-1">Location</label>
                                    <LocationSelect
                                        value={header.location}
                                        onChange={(value) => setHeader(prev => ({ ...prev, location: value }))}
                                        api_call={api_call}
                                        company={merged_config.company}
                                        disabled={mode === 'view'}
                                        size="sm"
                                    />
                                </div>
                                <div className="col-6">
                                    <label className="form-label small mb-1">Customer PO</label>
                                    <input
                                        type="text"
                                        className="form-control form-control-sm"
                                        value={header.custom_po || ''}
                                        onChange={(e) => setHeader(prev => ({ ...prev, custom_po: e.target.value }))}
                                        readOnly={mode === 'view'}
                                        placeholder="Customer PO#"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Shipping Info */}
                <div className="col-lg-4">
                    <div className="card h-100">
                        <div className="card-header py-2">
                            <h6 className="mb-0 d-flex align-items-center">
                                <Truck size={16} className="me-2" />
                                Shipping & Payment
                            </h6>
                        </div>
                        <div className="card-body p-2">
                            <div className="row g-2">
                                {mode === 'view' && header.ship_via ? (
                                    <div className="col-6">
                                        <label className="form-label small mb-1">Ship Via</label>
                                        <input
                                            type="text"
                                            className="form-control form-control-sm"
                                            value={header.ship_via}
                                            readOnly
                                        />
                                    </div>
                                ) : (
                                    <div className="col-6">
                                        <label className="form-label small mb-1">Ship Via</label>
                                        <ShipViaSelect
                                            value={header.ship_via}
                                            onChange={(value, id) => setHeader(prev => ({ 
                                                ...prev, 
                                                ship_via: value,
                                                ship_via_id: id 
                                            }))}
                                            api_call={api_call}
                                            disabled={mode === 'view'}
                                            size="sm"
                                        />
                                    </div>
                                )}
                                
                                {mode === 'view' && header.terms_desc ? (
                                    <div className="col-6">
                                        <label className="form-label small mb-1">Terms</label>
                                        <input
                                            type="text"
                                            className="form-control form-control-sm"
                                            value={header.terms_desc}
                                            readOnly
                                        />
                                    </div>
                                ) : (
                                    <div className="col-6">
                                        <label className="form-label small mb-1">Terms</label>
                                        <TermsSelect
                                            value={header.terms}
                                            onChange={(value) => setHeader(prev => ({ ...prev, terms: value }))}
                                            api_call={api_call}
                                            disabled={mode === 'view'}
                                            size="sm"
                                        />
                                    </div>
                                )}
                                
                                <div className="col-6">
                                    <label className="form-label small mb-1">Freight</label>
                                    <input
                                        type="number"
                                        className="form-control form-control-sm"
                                        value={header.freight || 0}
                                        onChange={(e) => setHeader(prev => ({ ...prev, freight: parseFloat(e.target.value) || 0 }))}
                                        readOnly={mode === 'view'}
                                        step="0.01"
                                        min="0"
                                    />
                                </div>
                                <div className="col-6">
                                    <label className="form-label small mb-1">Taxable</label>
                                    <div className="form-check form-switch mt-1">
                                        <input
                                            className="form-check-input"
                                            type="checkbox"
                                            checked={header.taxable}
                                            onChange={(e) => setHeader(prev => ({ ...prev, taxable: e.target.checked }))}
                                            disabled={mode === 'view'}
                                        />
                                        <label className="form-check-label small">
                                            {header.taxable ? 'Yes' : 'No'}
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Addresses - Collapsible in view mode */}
            <AddressSection
                billing={header.billing}
                shipping={header.shipping}
                onBillingChange={(billing) => setHeader(prev => ({ ...prev, billing }))}
                onShippingChange={(shipping) => setHeader(prev => ({ ...prev, shipping }))}
                readonly={mode === 'view'}
                collapsed={mode === 'view'}
            />

            {/* Line Items */}
            <div className="card mb-3">
                <div className="card-header py-2 d-flex justify-content-between align-items-center">
                    <h6 className="mb-0">Line Items</h6>
                    {mode !== 'view' && (
                        <div>
                            <button
                                className="btn btn-primary btn-sm me-2"
                                onClick={() => add_line()}
                            >
                                <Plus size={16} className="me-1" />
                                Add Line
                            </button>
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => add_note_line()}
                            >
                                <MessageSquare size={16} className="me-1" />
                                Add Note
                            </button>
                        </div>
                    )}
                </div>
                <div className="card-body p-0">
                    <LineItemsTable
                        lines={lines}
                        onUpdate={update_line}
                        onRemove={remove_line}
                        api_call={api_call}
                        readonly={mode === 'view'}
                    />
                </div>
            </div>

            {/* Totals */}
            <div className="row mb-3">
                <div className="col-md-4 offset-md-8">
                    <TotalsCard totals={totals} />
                </div>
            </div>

            {/* Action Buttons */}
            <div className="mb-4">
                {mode === 'create' && (
                    <>
                        <button
                            className="btn btn-success me-2"
                            onClick={save_so}
                            disabled={loading}
                        >
                            <Save size={16} className="me-1" />
                            Create Order
                        </button>
                        <CancelButton navigation={navigation} />
                    </>
                )}
                
                {mode === 'edit' && (
                    <>
                        <button
                            className="btn btn-success me-2"
                            onClick={save_so}
                            disabled={loading}
                        >
                            <Save size={16} className="me-1" />
                            Save Changes
                        </button>
                        <button
                            className="btn btn-secondary me-2"
                            onClick={() => {
                                setMode('view');
                                load_existing_so(); // Reload to discard changes
                            }}
                        >
                            <X size={16} className="me-1" />
                            Cancel
                        </button>
                    </>
                )}
                
                {mode === 'view' && (
                    <button
                        className="btn btn-secondary"
                        onClick={() => {
                            console.log('Back button clicked');
                            console.log('merged_config:', merged_config);
                            console.log('from info:', merged_config.from);
                            
                            if (navigation && navigation.navigate_to) {
                                // Check if we have 'from' information in the merged_config
                                if (merged_config.from && merged_config.from.view) {
                                    console.log('Navigating to:', merged_config.from.view, 'with params:', merged_config.from.parameters);
                                    // Navigate back to the view that sent us here
                                    navigation.navigate_to(merged_config.from.view, merged_config.from.parameters || {});
                                } else {
                                    console.log('No from info, defaulting to SalesOrders');
                                    // Default fallback to SalesOrders list
                                    navigation.navigate_to('SalesOrders', {});
                                }
                            } else {
                                console.log('No navigation available');
                            }
                        }}
                    >
                        <ArrowLeft size={16} className="me-1" />
                        Back
                    </button>
                )}
            </div>
        </div>
    );
};

// Sub-components

const CustomerSection = ({ customer, customer_code, onCustomerChange, api_call, readonly }) => {
    const [search_term, setSearchTerm] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [show_dropdown, setShowDropdown] = useState(false);

    useEffect(() => {
        if (customer) {
            setSearchTerm(`${customer.code} - ${customer.name}`);
        }
    }, [customer]);

    const search_customers = async (term) => {
        if (term.length < 2) {
            setSuggestions([]);
            return;
        }

        setLoading(true);
        try {
            // Determine which table to search based on term
            const model = term >= '7000000' ? 'GCANADA_dbo_BKARCUST' : 'GPACIFIC_dbo_BKARCUST';
            
            const result = await api_call('list', model, {
                filters: {
                    name: { operator: "ilike", value: `%${term}%` },
                    active: { operator: "eq", value: "Y" }
                },
                start: 0,
                length: 10
            });

            if (result.success && result.data) {
                setSuggestions(result.data);
            }
        } catch (error) {
            console.error('Error searching customers:', error);
            setSuggestions([]);
        }
        setLoading(false);
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            if (search_term && !customer) {
                search_customers(search_term);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [search_term, customer]);

    if (readonly && customer) {
        return (
            <div>
                <div className="fw-bold">{customer.name}</div>
                <div className="text-muted small">Customer #{customer.code}</div>
                {customer.contact && (
                    <div className="text-muted small">Contact: {customer.contact}</div>
                )}
            </div>
        );
    }

    return (
        <div className="position-relative">
            <input
                type="text"
                className="form-control form-control-sm"
                value={search_term}
                onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowDropdown(true);
                    if (!e.target.value) {
                        onCustomerChange(null);
                    }
                }}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Search customer by code or name..."
                disabled={readonly}
            />

            {show_dropdown && (suggestions.length > 0 || loading) && (
                <div className="dropdown-menu d-block position-absolute mt-1 w-100" 
                     style={{ maxHeight: '200px', overflowY: 'auto', zIndex: 1050 }}>
                    {loading && (
                        <div className="dropdown-item-text text-center">
                            <small className="text-muted">Loading...</small>
                        </div>
                    )}
                    {!loading && suggestions.map(cust => (
                        <button
                            key={cust.code}
                            className="dropdown-item text-truncate"
                            type="button"
                            onClick={() => {
                                onCustomerChange(cust);
                                setSearchTerm(`${cust.code} - ${cust.name}`);
                                setShowDropdown(false);
                            }}
                        >
                            <strong>{cust.code}</strong> - {cust.name}
                            {cust.city && <small className="text-muted d-block">{cust.city}, {cust.state}</small>}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

const AddressSection = ({ billing, shipping, onBillingChange, onShippingChange, readonly, collapsed }) => {
    const [is_collapsed, setIsCollapsed] = useState(collapsed);

    return (
        <div className="card mb-3">
            <div className="card-header py-2">
                <button
                    className="btn btn-link btn-sm text-decoration-none w-100 text-start p-0"
                    onClick={() => setIsCollapsed(!is_collapsed)}
                    type="button"
                >
                    <h6 className="mb-0">
                        {is_collapsed ? '▶' : '▼'} Billing & Shipping Addresses
                    </h6>
                </button>
            </div>
            {!is_collapsed && (
                <div className="card-body">
                    <div className="row g-2">
                        <div className="col-lg-6">
                            <AddressCard
                                title="Billing Address"
                                address={billing}
                                onChange={onBillingChange}
                                readonly={readonly}
                                compact
                            />
                        </div>
                        <div className="col-lg-6">
                            <AddressCard
                                title="Shipping Address"
                                address={shipping}
                                onChange={onShippingChange}
                                showCopyButton
                                onCopy={() => onShippingChange({ ...billing, attention: shipping.attention })}
                                readonly={readonly}
                                compact
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const AddressCard = ({ title, address, onChange, readonly, showCopyButton, onCopy, compact }) => {
    return (
        <div className={compact ? "" : "card h-100"}>
            <div className={compact ? "d-flex justify-content-between align-items-center mb-2" : "card-header py-2 d-flex justify-content-between align-items-center"}>
                <h6 className="mb-0 small">{title}</h6>
                {showCopyButton && !readonly && (
                    <button
                        type="button"
                        className="btn btn-sm btn-link p-0"
                        onClick={onCopy}
                    >
                        <Copy size={14} />
                    </button>
                )}
            </div>
            <div className={compact ? "" : "card-body p-2"}>
                <div className="row g-1">
                    <div className="col-12">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            value={address.name || ''}
                            onChange={(e) => onChange({ ...address, name: e.target.value })}
                            placeholder="Name"
                            readOnly={readonly}
                        />
                    </div>
                    {title === "Shipping Address" && (
                        <div className="col-12">
                            <input
                                type="text"
                                className="form-control form-control-sm"
                                value={address.attention || ''}
                                onChange={(e) => onChange({ ...address, attention: e.target.value })}
                                placeholder="Attention"
                                readOnly={readonly}
                            />
                        </div>
                    )}
                    <div className="col-12">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            value={address.address1 || ''}
                            onChange={(e) => onChange({ ...address, address1: e.target.value })}
                            placeholder="Address 1"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-12">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            value={address.address2 || ''}
                            onChange={(e) => onChange({ ...address, address2: e.target.value })}
                            placeholder="Address 2"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-5">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            value={address.city || ''}
                            onChange={(e) => onChange({ ...address, city: e.target.value })}
                            placeholder="City"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-2">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            value={address.state || ''}
                            onChange={(e) => onChange({ ...address, state: e.target.value.toUpperCase() })}
                            placeholder="ST"
                            maxLength="2"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-5">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            value={address.zip || ''}
                            onChange={(e) => onChange({ ...address, zip: e.target.value })}
                            placeholder="ZIP"
                            readOnly={readonly}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

const LineItemsTable = ({ lines, onUpdate, onRemove, api_call, readonly }) => {
    if (lines.length === 0) {
        return (
            <div className="text-center text-muted p-4">
                No line items. Click "Add Line" to start.
            </div>
        );
    }

    return (
        <div className="table-responsive">
            <table className="table table-sm table-hover mb-0">
                <thead>
                    <tr>
                        <th width="40">#</th>
                        <th width="120">Part</th>
                        <th>Description</th>
                        <th width="80">Qty</th>
                        <th width="100">Price</th>
                        <th width="100">Discount</th>
                        <th width="100">Extended</th>
                        {!readonly && <th width="50"></th>}
                    </tr>
                </thead>
                <tbody>
                    {lines.map((line, index) => (
                        <LineItemRow
                            key={index}
                            line={line}
                            index={index}
                            onUpdate={onUpdate}
                            onRemove={onRemove}
                            api_call={api_call}
                            readonly={readonly}
                        />
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const LineItemRow = ({ line, index, onUpdate, onRemove, api_call, readonly }) => {
    const is_note = line.type === 'X';
    
    if (is_note) {
        return (
            <tr>
                <td>{index + 1}</td>
                <td colSpan={readonly ? 6 : 5}>
                    <div className="d-flex align-items-center">
                        <span className="badge bg-info me-2">NOTE</span>
                        {readonly ? (
                            <span>{line.message}</span>
                        ) : (
                            <input
                                type="text"
                                className="form-control form-control-sm flex-grow-1"
                                value={line.message || ''}
                                onChange={(e) => onUpdate(index, 'message', e.target.value)}
                                placeholder="Note text..."
                                maxLength="75"
                            />
                        )}
                    </div>
                </td>
                {!readonly && (
                    <td className="text-center">
                        <button
                            className="btn btn-sm btn-link text-danger p-0"
                            onClick={() => onRemove(index)}
                        >
                            <Trash2 size={16} />
                        </button>
                    </td>
                )}
            </tr>
        );
    }

    return (
        <tr>
            <td>{index + 1}</td>
            <td>
                {readonly ? (
                    <span>{line.part}</span>
                ) : (
                    <PartInput
                        value={line.part}
                        onChange={(value) => onUpdate(index, 'part', value)}
                        onPartSelect={async (part) => {
                            onUpdate(index, 'part', part.part);
                            onUpdate(index, 'description', part.inventory_description);
                            
                            // Could fetch pricing here
                        }}
                        api_call={api_call}
                    />
                )}
            </td>
            <td>
                {readonly ? (
                    <span>{line.description}</span>
                ) : (
                    <input
                        type="text"
                        className="form-control form-control-sm"
                        value={line.description || ''}
                        onChange={(e) => onUpdate(index, 'description', e.target.value)}
                        placeholder="Description"
                    />
                )}
            </td>
            <td>
                {readonly ? (
                    <span>{line.quantity}</span>
                ) : (
                    <input
                        type="number"
                        className="form-control form-control-sm"
                        value={line.quantity}
                        onChange={(e) => onUpdate(index, 'quantity', parseFloat(e.target.value) || 0)}
                        min="0"
                        step="1"
                    />
                )}
            </td>
            <td>
                {readonly ? (
                    <span>${(line.price || 0).toFixed(2)}</span>
                ) : (
                    <input
                        type="number"
                        className="form-control form-control-sm"
                        value={line.price}
                        onChange={(e) => onUpdate(index, 'price', parseFloat(e.target.value) || 0)}
                        min="0"
                        step="0.01"
                    />
                )}
            </td>
            <td>
                {readonly ? (
                    <span>${(line.discount || 0).toFixed(2)}</span>
                ) : (
                    <input
                        type="number"
                        className="form-control form-control-sm"
                        value={line.discount}
                        onChange={(e) => onUpdate(index, 'discount', parseFloat(e.target.value) || 0)}
                        min="0"
                        step="0.01"
                    />
                )}
            </td>
            <td className="text-end">
                <strong>${(line.extended || 0).toFixed(2)}</strong>
            </td>
            {!readonly && (
                <td className="text-center">
                    <button
                        className="btn btn-sm btn-link text-danger p-0"
                        onClick={() => onRemove(index)}
                    >
                        <Trash2 size={16} />
                    </button>
                </td>
            )}
        </tr>
    );
};

const PartInput = ({ value, onChange, onPartSelect, api_call }) => {
    const [search_term, setSearchTerm] = useState(value || '');
    const [suggestions, setSuggestions] = useState([]);
    const [show_dropdown, setShowDropdown] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setSearchTerm(value || '');
    }, [value]);

    const search_parts = async (term) => {
        if (term.length < 2) {
            setSuggestions([]);
            return;
        }

        setLoading(true);
        try {
            const result = await api_call('list', 'JADVDATA_dbo_part_meta', {
                return_columns: ["part", "inventory_description"],
                filters: {
                    part: { operator: "ilike", value: `${term}%` }
                },
                start: 0,
                length: 10
            });

            if (result.success && result.data) {
                setSuggestions(result.data);
            }
        } catch (error) {
            console.error('Error searching parts:', error);
            setSuggestions([]);
        }
        setLoading(false);
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            if (search_term && search_term !== value) {
                search_parts(search_term);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [search_term]);

    return (
        <div className="position-relative">
            <input
                type="text"
                className="form-control form-control-sm"
                value={search_term}
                onChange={(e) => {
                    setSearchTerm(e.target.value);
                    onChange(e.target.value);
                    setShowDropdown(true);
                }}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Part #"
            />

            {show_dropdown && (suggestions.length > 0 || loading) && (
                <div className="dropdown-menu d-block position-absolute mt-1" 
                     style={{ maxHeight: '200px', overflowY: 'auto', minWidth: '300px', zIndex: 1050 }}>
                    {loading && (
                        <div className="dropdown-item-text text-center">
                            <small className="text-muted">Searching...</small>
                        </div>
                    )}
                    {!loading && suggestions.map(part => (
                        <button
                            key={part.part}
                            className="dropdown-item"
                            type="button"
                            onClick={() => {
                                onPartSelect(part);
                                setShowDropdown(false);
                            }}
                        >
                            <strong>{part.part}</strong>
                            {part.inventory_description && (
                                <small className="text-muted ms-2">{part.inventory_description}</small>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

const TotalsCard = ({ totals }) => {
    return (
        <div className="card">
            <div className="card-body p-2">
                <div className="d-flex justify-content-between mb-1">
                    <span className="small">Subtotal:</span>
                    <strong className="small">${totals.subtotal.toFixed(2)}</strong>
                </div>
                {totals.total_freight > 0 && (
                    <div className="d-flex justify-content-between mb-1">
                        <span className="small">Part Freight:</span>
                        <strong className="small">${totals.total_freight.toFixed(2)}</strong>
                    </div>
                )}
                <div className="d-flex justify-content-between mb-1">
                    <span className="small">Order Freight:</span>
                    <strong className="small">${totals.order_freight.toFixed(2)}</strong>
                </div>
                <div className="d-flex justify-content-between mb-1">
                    <span className="small">Tax:</span>
                    <strong className="small">${totals.tax_amount.toFixed(2)}</strong>
                </div>
                <hr className="my-2" />
                <div className="d-flex justify-content-between">
                    <span>Total:</span>
                    <strong className="h5 mb-0">${totals.total.toFixed(2)}</strong>
                </div>
            </div>
        </div>
    );
};

const LocationSelect = ({ value, onChange, api_call, company, disabled, size = "md" }) => {
    const [locations, setLocations] = useState([]);

    useEffect(() => {
        const load_locations = async () => {
            const result = await api_call('list', 'JADVDATA_dbo_locations', {
                filters: {
                    company: { operator: "eq", value: company },
                    active: { operator: "eq", value: "1" }
                },
                start: 0,
                length: 50
            });

            if (result.success && result.data) {
                setLocations(result.data);
            }
        };
        load_locations();
    }, [company]);

    return (
        <select
            className={`form-select form-select-${size}`}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
        >
            <option value="">Select...</option>
            {locations.map(loc => (
                <option key={loc.location} value={loc.location}>
                    {loc.location} - {loc.location_name}
                </option>
            ))}
        </select>
    );
};

const ShipViaSelect = ({ value, onChange, api_call, disabled, size = "md" }) => {
    const [options, setOptions] = useState([]);

    useEffect(() => {
        const load_options = async () => {
            const model = 'GPACIFIC_dbo_BKSHPVIA';  // Would need to handle CANADA too
            const result = await api_call('list', model, {
                start: 0,
                length: 50
            });

            if (result.success && result.data) {
                setOptions(result.data);
            }
        };
        load_options();
    }, []);

    return (
        <select
            className={`form-select form-select-${size}`}
            value={value || ''}
            onChange={(e) => {
                const selected = options.find(o => o.text === e.target.value);
                onChange(e.target.value, selected?.num || 0);
            }}
            disabled={disabled}
        >
            <option value="">Select...</option>
            {options.map(opt => (
                <option key={opt.num} value={opt.text}>
                    {opt.text}
                </option>
            ))}
        </select>
    );
};

const TermsSelect = ({ value, onChange, api_call, disabled, size = "md" }) => {
    const [terms, setTerms] = useState([]);

    useEffect(() => {
        const load_terms = async () => {
            const result = await api_call('list', 'GPACIFIC_dbo_BKSYTERM', {
                start: 0,
                length: 50
            });

            if (result.success && result.data) {
                setTerms(result.data);
            }
        };
        load_terms();
    }, []);

    return (
        <select
            className={`form-select form-select-${size}`}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
        >
            <option value="">Select...</option>
            {terms.map(term => (
                <option key={term.num} value={term.num}>
                    {term.desc}
                </option>
            ))}
        </select>
    );
};

const CancelButton = ({ navigation }) => {
    return (
        <button
            className="btn btn-secondary"
            onClick={() => {
                if (navigation) {
                    navigation.navigate_to('SalesOrders');
                }
            }}
        >
            <X size={16} className="me-1" />
            Cancel
        </button>
    );
};

// Helper functions
function format_phone(phone) {
    if (!phone) return 'N/A';
    // Remove all non-numeric characters
    const cleaned = phone.toString().replace(/\D/g, '');
    // Format as (XXX) XXX-XXXX if 10 digits
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    // Return as-is if not 10 digits
    return phone;
}

function get_default_header(config) {
    const today = new Date().toISOString().split('T')[0];
    
    return {
        customer_code: '',
        order_date: today,
        invoice_date: today,
        ship_date: '',
        location: config.location || 'TAC',
        entered_by: '',
        sales_person: '',
        sales_person_name: '',
        custom_po: '',
        terms: '',
        terms_desc: '',
        ship_via: '',
        ship_via_id: 0,
        freight: 0,
        tax_amount: 0,
        taxable: false,
        tax_rate: 0,
        tax_key: '',
        admin_id: null,
        cod: 'N',
        billing: {
            name: '',
            address1: '',
            address2: '',
            city: '',
            state: '',
            zip: '',
            country: 'USA'
        },
        shipping: {
            name: '',
            attention: '',
            address1: '',
            address2: '',
            city: '',
            state: '',
            zip: '',
            country: 'USA'
        }
    };
}

function map_header_data(header) {
    return {
        customer_code: header.customer_code || '',
        order_date: format_date(header.order_date),
        invoice_date: format_date(header.invoice_date),
        ship_date: format_date(header.ship_date),
        location: header.location || 'TAC',
        entered_by: header.entered_by || '',
        sales_person: header.sales_person || '',
        sales_person_name: header.sales_person_info?.full_name || '',
        custom_po: header.custom_po || '',
        terms: header.terms || '',
        terms_desc: header.payment?.terms_desc || '',
        ship_via: header.shipping?.via || '',
        ship_via_id: header.shipping?.via_id || 0,
        freight: parseFloat(header.freight || 0),
        tax_amount: parseFloat(header.tax_amount || 0),
        taxable: header.taxable === 'Y',
        tax_rate: parseFloat(header.tax_rate || 0),
        tax_key: header.tax_key || '',
        cod: header.payment?.cod || 'N',
        billing: header.billing || get_default_header().billing,
        shipping: header.shipping || get_default_header().shipping
    };
}

function format_date(date) {
    if (!date) return '';
    if (typeof date === 'string') return date.split('T')[0];
    return '';
}

export default SalesOrderDetail;