/**
 * @routes ["/v2/purchase_orders", "/v2/purchase_orders/:id"]
*/

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, Plus, MessageSquare, Trash2, Save, Truck, X, Copy } from 'lucide-react';

// Main Purchase Order Builder Component
const PurchaseOrderBuilder = ({ config }) => {
    // Core state
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');
    
    // PO Data state
    const [poNumber] = useState(config.po_number || null);
    const [isEditMode] = useState(!!config.po_number && config.po_number !== 'NEW');
    const [vendor, setVendor] = useState(null);
    const [header, setHeader] = useState(get_default_header(config));
    const [lines, setLines] = useState([]);
    const [deletedLineIds, setDeletedLineIds] = useState([]);
    
    // UI State
    const [vendorComments, setVendorComments] = useState({ show: false, comments1: '', comments2: '' });
    const [showReceiveModal, setShowReceiveModal] = useState(false);
    const [selectedReceiveLines, setSelectedReceiveLines] = useState(new Set());
    
    // Virtual inventory state (part -> inventory data)
    const [virtualInventory, setVirtualInventory] = useState({});
    const [inventoryLoading, setInventoryLoading] = useState({});
    
    // Pre-population data
    const prePopulateData = config.pre_populate_data || {
        location: config.location,
        ship_via: config.ship_via,
        shipping_address: config.shipping_address,
        initial_items: config.initial_items || [],
        vendors: config.vendors || false,
        parked_order_id: config.parked_order_id || 0
    };
    
    // API configuration
    const api_call = async (operation, model, params = {}) => {
        const request_data = {
            operation: operation,
            model: model,
            company: config.company || 'PACIFIC',
            ...params
        };
    
        // Use your existing API manager
        return await window.app.api.post(config.data_api, request_data);
    };
    
    // Initialize component
    useEffect(() => {
        const init = async () => {
            if (config.po_number === 'NEW') {
                // Apply pre-population for new POs
                apply_pre_population();
                if (prePopulateData.initial_items.length === 0) {
                    add_line();
                }
            } else if (isEditMode) {
                // Load existing PO
                await load_existing_po();
            } else {
                // New PO without pre-population
                add_line();
            }
        };
        
        init();
    }, []);
    
    // Load existing PO
    const load_existing_po = async () => {
        setLoading(true);
        setLoadingMessage('Loading purchase order...');
        
        const result = await api_call('get', 'PurchaseOrder', {
            po_number: poNumber
        });
        
        if (result.success) {
            const cleaned_data = clean_po_data(result);
            setHeader(map_header_data(cleaned_data.header || {}));
            setLines(cleaned_data.lines || []);
            
            // Load vendor info if we have vendor code
            if (cleaned_data.header.vendor_code) {
                await load_vendor_details(cleaned_data.header.vendor_code);
            }
        } else {
            show_error('Failed to load purchase order');
        }
        
        setLoading(false);
    };
    
    // Apply pre-population data
    const apply_pre_population = () => {
        const data = prePopulateData;
        
        // Apply location
        if (data.location) {
            setHeader(prev => ({ ...prev, location: data.location }));
        }
        
        // Apply ship_via
        if (data.ship_via) {
            setHeader(prev => ({ ...prev, ship_via: data.ship_via }));
        }
        
        // Apply shipping address
        if (data.shipping_address) {
            setHeader(prev => ({
                ...prev,
                shipping: { ...prev.shipping, ...data.shipping_address }
            }));
        }
        
        // Add initial items
        if (data.initial_items && data.initial_items.length > 0) {
            const new_lines = data.initial_items.map(item => {
                if (item.type === 'part' && item.part) {
                    return {
                        _source: 'active',
                        part: item.part,
                        pcode: item.part,
                        description: item.description || '',
                        pdesc: item.description || '',
                        quantity: item.qty || 1,
                        pqty: item.qty || 1,
                        price: item.price || 0,
                        pprce: item.price || 0,
                        discount: 0,
                        pdisc: 0,
                        extended: (item.price || 0) * (item.qty || 1),
                        pext: (item.price || 0) * (item.qty || 1),
                        received_qty: 0,
                        rqty: 0,
                        erd: header.expected_receipt_date,
                        type: 'R',
                        taxable: false,
                        message: '',
                        msg: ''
                    };
                } else if (item.type === 'note' && item.message) {
                    return {
                        _source: 'active',
                        type: 'N',
                        message: item.message,
                        msg: item.message,
                        part: '', pcode: '',
                        description: '', pdesc: '',
                        quantity: 0, pqty: 0,
                        price: 0, pprce: 0,
                        discount: 0, pdisc: 0,
                        extended: 0, pext: 0,
                        received_qty: 0, rqty: 0,
                        erd: header.expected_receipt_date,
                        taxable: false
                    };
                }
                return null;
            }).filter(Boolean);
            
            setLines(new_lines);
            
            // Fetch virtual inventory for parts
            new_lines.forEach((line, index) => {
                if (line.part) {
                    fetch_virtual_inventory(line.part, index);
                }
            });
        }
    };
    
    // Vendor handling
    const handle_vendor_change = async (vendor_data) => {
        setVendor(vendor_data);
        
        // Update header
        setHeader(prev => ({
            ...prev,
            vendor_code: vendor_data.code,
            vendor_name: vendor_data.name,
            billing: {
                name: vendor_data.name,
                address1: vendor_data.add1 || '',
                address2: vendor_data.add2 || '',
                city: vendor_data.city || '',
                state: vendor_data.state || '',
                zip: vendor_data.zip_ || '',
                country: vendor_data.country || 'USA'
            },
            terms: vendor_data.terms_num || prev.terms
        }));
        
        // Show vendor comments if any
        if (vendor_data.comments1 || vendor_data.comments2) {
            setVendorComments({
                show: true,
                comments1: vendor_data.comments1 || '',
                comments2: vendor_data.comments2 || ''
            });
        } else {
            setVendorComments({ show: false, comments1: '', comments2: '' });
        }
    };
    
    const load_vendor_details = async (vendor_code) => {
        const result = await api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
            filters: {
                code: {
                    operator: "eq",
                    value: vendor_code
                }
            },
            start: 0,
            length: 1
        });
        
        if (result.success && result.data && result.data.length > 0) {
            await handle_vendor_change(result.data[0]);
        }
    };
    
    // Line management
    const add_line = () => {
        const new_line = {
            _source: 'active',
            part: '', pcode: '',
            description: '', pdesc: '',
            quantity: 1, pqty: 1,
            price: 0, pprce: 0,
            discount: 0, pdisc: 0,
            extended: 0, pext: 0,
            received_qty: 0, rqty: 0,
            erd: header.expected_receipt_date,
            type: 'R',
            taxable: false,
            message: '', msg: ''
        };
        
        setLines(prev => [...prev, new_line]);
    };
    
    const add_note_line = () => {
        const new_note = {
            _source: 'active',
            type: 'N',
            message: '', msg: '',
            part: '', pcode: '',
            description: '', pdesc: '',
            quantity: 0, pqty: 0,
            price: 0, pprce: 0,
            discount: 0, pdisc: 0,
            extended: 0, pext: 0,
            received_qty: 0, rqty: 0,
            erd: header.expected_receipt_date,
            taxable: false
        };
        
        setLines(prev => [...prev, new_note]);
    };
    
    const remove_line = (index) => {
        const line = lines[index];
        
        if (line.rqty > 0) {
            show_error('Cannot remove received lines');
            return;
        }
        
        if (confirm('Remove this line?')) {
            if (line.record) {
                setDeletedLineIds(prev => [...prev, line.record]);
            }
            setLines(prev => prev.filter((_, i) => i !== index));
        }
    };
    
    const update_line = (index, field, value) => {
        setLines(prev => {
            const updated = [...prev];
            const line = { ...updated[index] };
            
            // Update both field formats
            line[field] = value;
            
            // Map fields
            const field_map = {
                'part': 'pcode',
                'description': 'pdesc',
                'quantity': 'pqty',
                'price': 'pprce',
                'discount': 'pdisc',
                'message': 'msg'
            };
            
            if (field_map[field]) {
                line[field_map[field]] = value;
            }
            
            // Recalculate extended if needed
            if (line.type !== 'N' && ['quantity', 'price', 'discount'].includes(field)) {
                const qty = parseFloat(line.quantity || line.pqty || 0);
                const price = parseFloat(line.price || line.pprce || 0);
                const discount = parseFloat(line.discount || line.pdisc || 0);
                
                const extended = qty * (price - discount);
                line.extended = extended;
                line.pext = extended;
            }
            
            updated[index] = line;
            return updated;
        });
    };
    
    // Virtual inventory
    const fetch_virtual_inventory = async (part, index) => {
        if (!part) return;
        
        setInventoryLoading(prev => ({ ...prev, [index]: true }));
        
        const result = await api_call('list', 'JADVDATA_dbo_virtual_inventory', {
            filters: {
                part: {
                    operator: "eq",
                    value: part
                }
            },
            start: 0,
            length: 50
        });
        
        if (result.success && result.data && result.data.length > 0) {
            setVirtualInventory(prev => ({ ...prev, [index]: result.data }));
        } else {
            setVirtualInventory(prev => ({ ...prev, [index]: [] }));
        }
        
        setInventoryLoading(prev => ({ ...prev, [index]: false }));
    };
    
    const select_vendor_from_inventory = async (vendor_code, line_index) => {
        // Check if vendor is in static list
        if (prePopulateData.vendors && prePopulateData.vendors.length > 0) {
            const static_vendor = prePopulateData.vendors.find(v => v.code === vendor_code);
            if (static_vendor) {
                await handle_vendor_change(static_vendor);
                return;
            }
        }
        
        // Otherwise fetch vendor details
        await load_vendor_details(vendor_code);
    };
    
    // Save PO
    const save_po = async () => {
        if (!validate_po()) return;
        
        setLoading(true);
        setLoadingMessage('Saving purchase order...');
        
        const save_data = {
            header: header,
            lines: lines,
            deleted_line_ids: deletedLineIds
        };
        
        if (isEditMode) {
            save_data.po_number = poNumber;
        }
        
        const operation = isEditMode ? 'update' : 'create';
        const result = await api_call(operation, 'PurchaseOrder', {
            data: save_data
        });
        
        if (result.success) {
            show_success('Purchase order saved successfully!');
            
            if (!isEditMode && result.data.po_number) {
                // Redirect to edit mode
                window.location.href = `/purchase_orders/edit/${result.data.po_number}`;
            } else {
                // Reload to get updated data
                await load_existing_po();
            }
            
            setDeletedLineIds([]);
        } else {
            show_error(result.message || 'Failed to save purchase order');
        }
        
        setLoading(false);
    };
    
    // Calculations
    const totals = useMemo(() => {
        let subtotal = 0;
        
        lines.forEach(line => {
            const extended = parseFloat(line.extended || line.pext || 0);
            subtotal += extended;
        });
        
        const freight = parseFloat(header.freight || 0);
        const tax_amount = parseFloat(header.tax_amount || 0);
        const total = subtotal + freight + tax_amount;
        
        return { subtotal, freight, tax_amount, total };
    }, [lines, header.freight, header.tax_amount]);
    
    // Validation
    const validate_po = () => {
        const errors = [];
        
        if (!header.vendor_code) {
            errors.push('Please select a vendor');
        }
        
        if (!header.order_date) {
            errors.push('Order date is required');
        }
        
        if (!header.expected_receipt_date) {
            errors.push('Expected receipt date is required');
        }
        
        if (lines.length === 0) {
            errors.push('At least one line item is required');
        }
        
        let has_valid_line = false;
        lines.forEach(line => {
            const part = line.part || line.pcode;
            const qty = parseFloat(line.quantity || line.pqty || 0);
            
            if (part && qty > 0) {
                has_valid_line = true;
            }
        });
        
        if (!has_valid_line) {
            errors.push('At least one line must have a part and quantity');
        }
        
        if (errors.length > 0) {
            show_error('Please fix the following errors:\n' + errors.join('\n'));
            return false;
        }
        
        return true;
    };
    
    // Utility functions
    const show_error = (message) => {
        alert('Error: ' + message);
    };
    
    const show_success = (message) => {
        alert('Success: ' + message);
    };
    
    // Render helpers
    const is_partially_received = lines.some(line => line.rqty > 0);
    const can_edit_header = !is_partially_received;
    
    return (
        <div className="container-fluid mt-3">
            {loading && (
                <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                     style={{ background: 'rgba(0,0,0,0.5)', zIndex: 9999 }}>
                    <div className="text-center text-white">
                        <div className="spinner-border text-light mb-2" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                        <div>{loadingMessage || 'Loading...'}</div>
                    </div>
                </div>
            )}
            
            <h4 className="mb-3">
                Purchase Order 
                {poNumber && <span className="ms-2">#{poNumber}</span>}
                {header.printed && <span className="badge bg-success ms-2">Printed</span>}
            </h4>
            
            {/* Header Section */}
            <div className="row g-3">
                {/* Order Details Card */}
                <div className="col-lg-6 mb-3">
                    <div className="card h-100">
                        <div className="card-header">
                            <h6 className="mb-0">Order Details</h6>
                        </div>
                        <div className="card-body">
                            <div className="row g-2">
                                <div className="col-md-6">
                                    <label className="form-label">Vendor <span className="text-danger">*</span></label>
                                    <VendorSelect
                                        value={header.vendor_code}
                                        vendors={prePopulateData.vendors}
                                        onVendorChange={handle_vendor_change}
                                        api_call={api_call}
                                        disabled={!can_edit_header}
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label">Ordered By</label>
                                    <input 
                                        type="text" 
                                        className="form-control form-control-sm"
                                        value={header.orderd_by_customer || ''}
                                        onChange={(e) => setHeader(prev => ({ ...prev, orderd_by_customer: e.target.value }))}
                                        placeholder="Name..."
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label">Order Date <span className="text-danger">*</span></label>
                                    <input 
                                        type="date" 
                                        className="form-control form-control-sm"
                                        value={header.order_date}
                                        onChange={(e) => setHeader(prev => ({ ...prev, order_date: e.target.value }))}
                                        disabled={!can_edit_header}
                                        required
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label">Expected Date <span className="text-danger">*</span></label>
                                    <input 
                                        type="date" 
                                        className="form-control form-control-sm"
                                        value={header.expected_receipt_date}
                                        onChange={(e) => setHeader(prev => ({ ...prev, expected_receipt_date: e.target.value }))}
                                        required
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Shipping Details Card */}
                <div className="col-lg-6 mb-3">
                    <div className="card h-100">
                        <div className="card-header">
                            <h6 className="mb-0">Shipping Details</h6>
                        </div>
                        <div className="card-body">
                            <div className="row g-2">
                                <div className="col-md-4">
                                    <label className="form-label">Terms</label>
                                    <TermsSelect
                                        value={header.terms}
                                        onChange={(value) => setHeader(prev => ({ ...prev, terms: value }))}
                                        api_call={api_call}
                                        disabled={!can_edit_header}
                                    />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Ship Via</label>
                                    <ShipViaInput
                                        value={header.ship_via}
                                        onChange={(value) => setHeader(prev => ({ ...prev, ship_via: value }))}
                                        api_call={api_call}
                                        disabled={!can_edit_header}
                                    />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Freight</label>
                                    <input 
                                        type="number" 
                                        className="form-control form-control-sm"
                                        value={header.freight}
                                        onChange={(e) => setHeader(prev => ({ ...prev, freight: parseFloat(e.target.value) || 0 }))}
                                        min="0" 
                                        step="0.01"
                                    />
                                </div>
                                <div className="col-md-12">
                                    <label className="form-label">Location</label>
                                    <LocationSelect
                                        value={header.location}
                                        onChange={(value) => setHeader(prev => ({ ...prev, location: value }))}
                                        api_call={api_call}
                                        company={config.company}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Vendor Comments */}
            {vendorComments.show && (
                <div className="alert alert-warning">
                    <h6 className="alert-heading">Vendor Notes:</h6>
                    {vendorComments.comments1 && <p className="mb-2">{vendorComments.comments1}</p>}
                    {vendorComments.comments2 && <p className="mb-0">{vendorComments.comments2}</p>}
                </div>
            )}
            
            {/* Addresses */}
            <div className="row g-3 mb-3">
                <div className="col-lg-6">
                    <AddressCard
                        title="Billing Address"
                        address={header.billing}
                        onChange={(billing) => setHeader(prev => ({ ...prev, billing }))}
                        readonly={!can_edit_header}
                    />
                </div>
                <div className="col-lg-6">
                    <AddressCard
                        title="Shipping Address"
                        address={header.shipping}
                        onChange={(shipping) => setHeader(prev => ({ ...prev, shipping }))}
                        showCopyButton
                        onCopy={() => setHeader(prev => ({ 
                            ...prev, 
                            shipping: { ...prev.billing, attention: prev.shipping.attention }
                        }))}
                    />
                </div>
            </div>
            
            {/* Line Items */}
            <div className="card mb-3">
                <div className="card-header d-flex justify-content-between align-items-center">
                    <h6 className="mb-0">Line Items</h6>
                    <div>
                        <button 
                            className="btn btn-primary btn-sm me-2"
                            onClick={add_line}
                        >
                            <Plus size={16} className="me-1" />
                            Add Line
                        </button>
                        <button 
                            className="btn btn-secondary btn-sm"
                            onClick={add_note_line}
                        >
                            <MessageSquare size={16} className="me-1" />
                            Add Note
                        </button>
                    </div>
                </div>
                <div className="card-body">
                    {lines.length === 0 ? (
                        <div className="text-muted text-center p-4">
                            No lines added. Click "Add Line" to start.
                        </div>
                    ) : (
                        lines.map((line, index) => (
                            <LineItem
                                key={index}
                                line={line}
                                index={index}
                                onUpdate={update_line}
                                onRemove={remove_line}
                                api_call={api_call}
                                virtualInventory={virtualInventory[index]}
                                inventoryLoading={inventoryLoading[index]}
                                onFetchInventory={(part) => fetch_virtual_inventory(part, index)}
                                onSelectVendor={(vendor_code) => select_vendor_from_inventory(vendor_code, index)}
                            />
                        ))
                    )}
                </div>
            </div>
            
            {/* Totals */}
            <div className="row mb-3">
                <div className="col-md-4 offset-md-8">
                    <div className="card">
                        <div className="card-body">
                            <div className="d-flex justify-content-between mb-2">
                                <span>Subtotal:</span>
                                <strong>${totals.subtotal.toFixed(2)}</strong>
                            </div>
                            <div className="d-flex justify-content-between mb-2">
                                <span>Tax:</span>
                                <strong>${totals.tax_amount.toFixed(2)}</strong>
                            </div>
                            <div className="d-flex justify-content-between mb-2">
                                <span>Freight:</span>
                                <strong>${totals.freight.toFixed(2)}</strong>
                            </div>
                            <hr />
                            <div className="d-flex justify-content-between">
                                <span className="h5">Total:</span>
                                <strong className="h5">${totals.total.toFixed(2)}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Action Buttons */}
            <div className="mb-4">
                <button 
                    className="btn btn-success me-2"
                    onClick={save_po}
                    disabled={loading}
                >
                    <Save size={16} className="me-1" />
                    {isEditMode ? 'Update PO' : 'Create PO'}
                </button>
                
                {isEditMode && (
                    <button 
                        className="btn btn-primary me-2"
                        onClick={() => setShowReceiveModal(true)}
                    >
                        <Truck size={16} className="me-1" />
                        Receive
                    </button>
                )}
                
                <button 
                    className="btn btn-secondary"
                    onClick={() => window.location.href = '/purchase_orders'}
                >
                    <X size={16} className="me-1" />
                    Cancel
                </button>
            </div>
            
            {/* Receive Modal */}
            {showReceiveModal && (
                <ReceiveModal
                    lines={lines}
                    onClose={() => setShowReceiveModal(false)}
                    onReceive={async (selected_indices) => {
                        setLoading(true);
                        setLoadingMessage('Processing receipt...');
                        
                        const result = await api_call('update', 'PurchaseOrder', {
                            po_number: poNumber,
                            action: 'receive_lines',
                            line_indices: selected_indices
                        });
                        
                        if (result.success) {
                            show_success(`Successfully received ${selected_indices.length} line(s)`);
                            await load_existing_po();
                        } else {
                            show_error(result.message || 'Failed to process receipt');
                        }
                        
                        setLoading(false);
                        setShowReceiveModal(false);
                    }}
                />
            )}
        </div>
    );
};

// Sub-components

const VendorSelect = ({ value, vendors, onVendorChange, api_call, disabled }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    
    // Static vendors mode
    if (vendors && vendors.length > 0) {
        return (
            <select 
                className="form-select form-select-sm"
                value={value}
                onChange={async (e) => {
                    const vendor_code = e.target.value;
                    if (!vendor_code) return;
                    
                    const result = await api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
                        filters: {
                            code: { operator: "eq", value: vendor_code }
                        },
                        start: 0,
                        length: 1
                    });
                    
                    if (result.success && result.data?.[0]) {
                        onVendorChange(result.data[0]);
                    }
                }}
                disabled={disabled}
                required
            >
                <option value="">Select vendor...</option>
                {vendors.map(v => (
                    <option key={v.code} value={v.code}>
                        {v.code} - {v.company}
                    </option>
                ))}
            </select>
        );
    }
    
    // Autocomplete mode
    const search_vendors = async (term) => {
        if (term.length < 2) {
            setSuggestions([]);
            return;
        }
        
        setLoading(true);
        const result = await api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
            filters: {
                name: { operator: "ilike", value: term }
            }
        });
        
        if (result.success && result.data) {
            setSuggestions(result.data.slice(0, 10));
        }
        setLoading(false);
    };
    
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchTerm && !value) {
                search_vendors(searchTerm);
            }
        }, 300);
        
        return () => clearTimeout(timer);
    }, [searchTerm]);
    
    return (
        <div className="position-relative">
            <input
                type="text"
                className="form-control form-control-sm"
                value={value ? `${value} - ${searchTerm}` : searchTerm}
                onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowDropdown(true);
                }}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Search vendor..."
                disabled={disabled}
                required
            />
            
            {showDropdown && suggestions.length > 0 && (
                <div className="position-absolute top-100 start-0 w-100 bg-white border rounded shadow-sm mt-1"
                     style={{ maxHeight: '200px', overflowY: 'auto', zIndex: 1050 }}>
                    {suggestions.map(vendor => (
                        <div
                            key={vendor.code}
                            className="p-2 hover-bg-light cursor-pointer"
                            onClick={() => {
                                onVendorChange(vendor);
                                setSearchTerm(vendor.name);
                                setShowDropdown(false);
                            }}
                        >
                            {vendor.code} - {vendor.name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const TermsSelect = ({ value, onChange, api_call, disabled }) => {
    const [terms, setTerms] = useState([]);
    
    useEffect(() => {
        const load_terms = async () => {
            const result = await api_call('list', 'BKSYSTERM', {
                start: 0,
                length: 0,
                return_columns: ["num", "desc"],
                order: [{ column: 0, dir: 'asc' }],
                columns: [{ name: 'num' }, { name: 'desc' }]
            });
            
            if (result.success && result.data) {
                setTerms(result.data);
            }
        };
        
        load_terms();
    }, []);
    
    return (
        <select 
            className="form-select form-select-sm"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
        >
            <option value="">Select Terms...</option>
            {terms.map(term => (
                <option key={term.num} value={term.num}>
                    {term.desc}
                </option>
            ))}
        </select>
    );
};

const LocationSelect = ({ value, onChange, api_call, company }) => {
    const [locations, setLocations] = useState([]);
    
    useEffect(() => {
        const load_locations = async () => {
            const result = await api_call('list', 'JADVDATA_dbo_locations', {
                start: 0,
                length: 0,
                return_columns: ["location", "location_name"],
                order: [{ column: 1, dir: 'asc' }],
                columns: [{ name: 'location' }, { name: 'location_name' }],
                filters: {
                    company: { operator: "eq", value: company || "PACIFIC" },
                    warehouse: { operator: "eq", value: "1" },
                    active: { operator: "eq", value: "1" }
                }
            });
            
            if (result.success && result.data) {
                setLocations(result.data);
            }
        };
        
        load_locations();
    }, []);
    
    return (
        <select 
            className="form-select form-select-sm"
            value={value}
            onChange={(e) => onChange(e.target.value)}
        >
            <option value="">Select Location...</option>
            {locations.map(loc => (
                <option key={loc.location} value={loc.location}>
                    {loc.location} - {loc.location_name}
                </option>
            ))}
        </select>
    );
};

const ShipViaInput = ({ value, onChange, api_call, disabled }) => {
    const [suggestions, setSuggestions] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    
    const common_options = ['UPS', 'FEDEX', 'USPS', 'DHL', 'FREIGHT', 'PICKUP'];
    
    return (
        <div className="position-relative">
            <input
                type="text"
                className="form-control form-control-sm"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Ship via..."
                disabled={disabled}
            />
            
            {showDropdown && (
                <div className="position-absolute top-100 start-0 w-100 bg-white border rounded shadow-sm mt-1"
                     style={{ zIndex: 1050 }}>
                    {common_options
                        .filter(opt => opt.toLowerCase().includes(value.toLowerCase()))
                        .map(opt => (
                            <div
                                key={opt}
                                className="p-2 hover-bg-light cursor-pointer"
                                onClick={() => {
                                    onChange(opt);
                                    setShowDropdown(false);
                                }}
                            >
                                {opt}
                            </div>
                        ))}
                </div>
            )}
        </div>
    );
};

const AddressCard = ({ title, address, onChange, readonly, showCopyButton, onCopy }) => {
    return (
        <div className="card h-100">
            <div className="card-header d-flex justify-content-between align-items-center">
                <h6 className="mb-0">{title}</h6>
                {showCopyButton && (
                    <button 
                        type="button" 
                        className="btn btn-sm btn-secondary"
                        onClick={onCopy}
                    >
                        <Copy size={14} className="me-1" />
                        Copy from Billing
                    </button>
                )}
            </div>
            <div className="card-body">
                <div className="row g-2">
                    <div className="col-12">
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={address.name}
                            onChange={(e) => onChange({ ...address, name: e.target.value })}
                            placeholder="Company Name"
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
                            />
                        </div>
                    )}
                    <div className="col-12">
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={address.address1}
                            onChange={(e) => onChange({ ...address, address1: e.target.value })}
                            placeholder="Address Line 1"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-12">
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={address.address2}
                            onChange={(e) => onChange({ ...address, address2: e.target.value })}
                            placeholder="Address Line 2"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-6">
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={address.city}
                            onChange={(e) => onChange({ ...address, city: e.target.value })}
                            placeholder="City"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-2">
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={address.state}
                            onChange={(e) => onChange({ ...address, state: e.target.value })}
                            placeholder="ST"
                            maxLength="2"
                            readOnly={readonly}
                        />
                    </div>
                    <div className="col-4">
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={address.zip}
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

const LineItem = ({ line, index, onUpdate, onRemove, api_call, virtualInventory, inventoryLoading, onFetchInventory, onSelectVendor }) => {
    const is_received = parseFloat(line.rqty || 0) > 0;
    const is_historical = line._source === 'historical';
    const is_readonly = is_received || is_historical;
    const line_number = index + 1;
    const is_note_line = line.type === 'N' || (!line.pcode && !line.part && line.msg);
    
    if (is_note_line) {
        return (
            <div className={`card mb-2 ${is_readonly ? 'bg-light' : ''}`}>
                <div className="card-body">
                    <div className="row align-items-center">
                        <div className="col-auto">
                            <span className="fw-bold text-muted">Line {line_number}</span>
                            {is_received && <span className="badge bg-success ms-2">RECEIVED</span>}
                        </div>
                        <div className="col-auto">
                            <span className="badge bg-info">NOTE</span>
                        </div>
                        <div className="col">
                            <input 
                                type="text" 
                                className="form-control form-control-sm"
                                value={line.message || line.msg || ''}
                                onChange={(e) => onUpdate(index, 'message', e.target.value)}
                                maxLength="30"
                                placeholder="Note (max 30 characters)"
                                readOnly={is_readonly}
                            />
                        </div>
                        {!is_readonly && (
                            <div className="col-auto">
                                <button 
                                    className="btn btn-sm btn-danger"
                                    onClick={() => onRemove(index)}
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }
    
    return (
        <div className={`card mb-2 ${is_readonly ? 'bg-light' : ''}`}>
            <div className="card-body">
                <div className="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <span className="fw-bold text-muted">Line {line_number}</span>
                        {is_received && <span className="badge bg-success ms-2">RECEIVED</span>}
                    </div>
                    {!is_readonly && (
                        <button 
                            className="btn btn-sm btn-danger"
                            onClick={() => onRemove(index)}
                        >
                            <Trash2 size={16} />
                        </button>
                    )}
                </div>
                
                <div className="row g-2">
                    <div className="col-md-2">
                        <label className="form-label small mb-1">Part #</label>
                        <PartSearch
                            value={line.part || line.pcode || ''}
                            onChange={(value) => onUpdate(index, 'part', value)}
                            onPartSelect={async (part) => {
                                onUpdate(index, 'part', part.part);
                                onUpdate(index, 'description', part.inventory_description);
                                
                                // Fetch cost
                                const cost_result = await api_call('list', 'GPACIFIC_dbo_BKICMSTR', {
                                    return_columns: ["code", "lstc"],
                                    order: [{ column: 0, dir: 'asc' }],
                                    columns: [{ name: 'code' }, { name: 'lstc' }],
                                    start: 0,
                                    length: 1,
                                    filters: {
                                        code: { operator: "eq", value: part.part }
                                    }
                                });
                                
                                if (cost_result.success && cost_result.data?.[0]) {
                                    onUpdate(index, 'price', cost_result.data[0].lstc || 0);
                                }
                                
                                // Fetch virtual inventory
                                onFetchInventory(part.part);
                            }}
                            api_call={api_call}
                            readonly={is_readonly}
                        />
                    </div>
                    <div className="col-md-4">
                        <label className="form-label small mb-1">Description</label>
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={line.description || line.pdesc || ''}
                            onChange={(e) => onUpdate(index, 'description', e.target.value)}
                            placeholder="Part description"
                            readOnly={is_readonly}
                        />
                    </div>
                    <div className="col-md-1">
                        <label className="form-label small mb-1">Qty</label>
                        <input 
                            type="number" 
                            className="form-control form-control-sm"
                            value={line.quantity || line.pqty || 0}
                            onChange={(e) => onUpdate(index, 'quantity', parseFloat(e.target.value) || 0)}
                            min="0" 
                            step="1"
                            readOnly={is_readonly}
                        />
                    </div>
                    <div className="col-md-1">
                        <label className="form-label small mb-1">Price</label>
                        <input 
                            type="number" 
                            className="form-control form-control-sm"
                            value={line.price || line.pprce || 0}
                            onChange={(e) => onUpdate(index, 'price', parseFloat(e.target.value) || 0)}
                            min="0" 
                            step="0.01"
                            readOnly={is_readonly}
                        />
                    </div>
                    <div className="col-md-1">
                        <label className="form-label small mb-1">Disc</label>
                        <input 
                            type="number" 
                            className="form-control form-control-sm"
                            value={line.discount || line.pdisc || 0}
                            onChange={(e) => onUpdate(index, 'discount', parseFloat(e.target.value) || 0)}
                            min="0"
                            readOnly={is_readonly}
                        />
                    </div>
                    <div className="col-md-1">
                        <label className="form-label small mb-1">Extended</label>
                        <input 
                            type="text" 
                            className="form-control form-control-sm"
                            value={`$${(line.extended || line.pext || 0).toFixed(2)}`}
                            readOnly
                        />
                    </div>
                    <div className="col-md-2">
                        <label className="form-label small mb-1">Expected Date</label>
                        <input 
                            type="date" 
                            className="form-control form-control-sm"
                            value={line.erd || ''}
                            onChange={(e) => onUpdate(index, 'erd', e.target.value)}
                            readOnly={is_readonly}
                        />
                    </div>
                </div>
                
                {/* Virtual Inventory */}
                {virtualInventory && virtualInventory.length > 0 && (
                    <div className="mt-3">
                        <div className="card border-secondary">
                            <div className="card-header py-2">
                                <h6 className="mb-0 small">Integrated vendor inventory availability</h6>
                            </div>
                            <div className="card-body p-2">
                                {inventoryLoading ? (
                                    <div className="text-center py-2">
                                        <div className="spinner-border spinner-border-sm text-primary" role="status">
                                            <span className="visually-hidden">Loading...</span>
                                        </div>
                                        <span className="ms-2 small text-muted">Loading inventory...</span>
                                    </div>
                                ) : (
                                    <div className="table-responsive">
                                        <table className="table table-sm table-hover table-striped mb-0">
                                            <thead>
                                                <tr>
                                                    <th>Company</th>
                                                    <th>Location</th>
                                                    <th>Qty</th>
                                                    <th style={{ width: '80px' }}>Action</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {virtualInventory.map((item, idx) => (
                                                    <tr key={idx}>
                                                        <td className="fw-bold">{(item.company || '').toUpperCase()}</td>
                                                        <td>{item.loc || ''}</td>
                                                        <td>{item.qty || 0}</td>
                                                        <td>
                                                            <button 
                                                                className="btn btn-sm btn-primary"
                                                                onClick={() => onSelectVendor((item.company || '').toUpperCase())}
                                                            >
                                                                Use
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const PartSearch = ({ value, onChange, onPartSelect, api_call, readonly }) => {
    const [searchTerm, setSearchTerm] = useState(value);
    const [suggestions, setSuggestions] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [loading, setLoading] = useState(false);
    
    useEffect(() => {
        setSearchTerm(value);
    }, [value]);
    
    const search_parts = async (term) => {
        if (term.length < 2) {
            setSuggestions([]);
            return;
        }
        
        setLoading(true);
        const result = await api_call('list', 'JADVDATA_dbo_part_meta', {
            return_columns: ["part", "inventory_description"],
            order: [{ column: 0, dir: 'asc' }],
            columns: [{ name: 'part' }, { name: 'inventory_description' }],
            filters: {
                part: { operator: "ilike", value: term }
            }
        });
        
        if (result.success && result.data) {
            setSuggestions(result.data.slice(0, 20));
        }
        setLoading(false);
    };
    
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchTerm && searchTerm !== value) {
                search_parts(searchTerm);
            }
        }, 300);
        
        return () => clearTimeout(timer);
    }, [searchTerm]);
    
    return (
        <div className="position-relative">
            <input
                type="text"
                className="form-control form-control-sm"
                value={searchTerm}
                onChange={(e) => {
                    setSearchTerm(e.target.value);
                    onChange(e.target.value);
                    setShowDropdown(true);
                }}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Search..."
                readOnly={readonly}
            />
            
            {showDropdown && suggestions.length > 0 && (
                <div className="position-absolute top-100 start-0 w-100 bg-white border rounded shadow-sm mt-1"
                     style={{ maxHeight: '200px', overflowY: 'auto', zIndex: 1050 }}>
                    {suggestions.map(part => (
                        <div
                            key={part.part}
                            className="p-2 hover-bg-light cursor-pointer"
                            onClick={() => {
                                onPartSelect(part);
                                setSearchTerm(part.part);
                                setShowDropdown(false);
                            }}
                        >
                            {part.part} - {part.inventory_description}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const ReceiveModal = ({ lines, onClose, onReceive }) => {
    const [selected, setSelected] = useState(new Set());
    
    const receivable_lines = lines
        .map((line, index) => ({ line, index }))
        .filter(({ line }) => parseFloat(line.rqty || line.received_qty || 0) === 0);
    
    if (receivable_lines.length === 0) {
        return (
            <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                <div className="modal-dialog">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h5 className="modal-title">Receive Purchase Order Lines</h5>
                            <button type="button" className="btn-close" onClick={onClose}></button>
                        </div>
                        <div className="modal-body">
                            <p className="text-muted">All lines have been received.</p>
                        </div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-secondary" onClick={onClose}>
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    const toggle_all = () => {
        if (selected.size === receivable_lines.length) {
            setSelected(new Set());
        } else {
            setSelected(new Set(receivable_lines.map(({ index }) => index)));
        }
    };
    
    const toggle_line = (index) => {
        const new_selected = new Set(selected);
        if (new_selected.has(index)) {
            new_selected.delete(index);
        } else {
            new_selected.add(index);
        }
        setSelected(new_selected);
    };
    
    return (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
            <div className="modal-dialog modal-lg">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Receive Purchase Order Lines</h5>
                        <button type="button" className="btn-close" onClick={onClose}></button>
                    </div>
                    <div className="modal-body">
                        <p className="text-muted">Select which lines to receive. Each selected line will be fully received.</p>
                        <div className="table-responsive">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th width="50">
                                            <input 
                                                type="checkbox" 
                                                className="form-check-input"
                                                checked={selected.size === receivable_lines.length}
                                                onChange={toggle_all}
                                            />
                                        </th>
                                        <th>Line</th>
                                        <th>Part</th>
                                        <th>Description</th>
                                        <th>Quantity</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {receivable_lines.map(({ line, index }) => (
                                        <tr key={index}>
                                            <td>
                                                <input 
                                                    type="checkbox" 
                                                    className="form-check-input"
                                                    checked={selected.has(index)}
                                                    onChange={() => toggle_line(index)}
                                                />
                                            </td>
                                            <td>{index + 1}</td>
                                            <td>{line.pcode || line.part || ''}</td>
                                            <td>{line.pdesc || line.description || ''}</td>
                                            <td>{line.pqty || line.quantity || 0}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button 
                            type="button" 
                            className="btn btn-primary"
                            onClick={() => onReceive(Array.from(selected))}
                            disabled={selected.size === 0}
                        >
                            Receive Selected Lines ({selected.size})
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Helper functions
function get_default_header(config) {
    const today = new Date().toISOString().split('T')[0];
    const expected_date = new Date();
    expected_date.setDate(expected_date.getDate() + 2);
    
    return {
        vendor_code: '',
        vendor_name: '',
        order_date: today,
        expected_receipt_date: expected_date.toISOString().split('T')[0],
        location: config.location || 'TAC',
        entered_by: '',
        orderd_by_customer: '',
        terms: '',
        ship_via: 'UPS',
        freight: 0.0,
        subtotal: 0.0,
        tax_amount: 0.0,
        total: 0.0,
        printed: false,
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

function clean_po_data(data) {
    if (data.lines) {
        data.lines = data.lines.map(line => {
            if (line.msg) {
                const clean_msg = line.msg.split('\x00')[0].trim();
                line.msg = clean_msg;
            }
            ['gla', 'gldpta', 'tskcod', 'cat'].forEach(field => {
                if (line[field] && typeof line[field] === 'string') {
                    line[field] = line[field].replace(/\x00/g, '').trim();
                }
            });
            return line;
        });
    }
    
    return {
        header: data.header || {},
        lines: data.lines || [],
        source_info: data.source_info || {}
    };
}

function map_header_data(header) {
    return {
        vendor_code: header.vndcod || header.vendor_code || '',
        vendor_name: header.vndnme || header.vendor_name || '',
        order_date: format_date(header.orddte || header.order_date),
        expected_receipt_date: format_date(header.erd || header.expected_receipt_date),
        location: header.loc || header.location || 'TAC',
        entered_by: header.entby || header.entered_by || '',
        terms: header.termd || header.terms || '',
        ship_via: header.shpvia || header.ship_via || 'UPS',
        freight: parseFloat(header.frght || header.freight || 0),
        subtotal: parseFloat(header.subtot || header.subtotal || 0),
        tax_amount: parseFloat(header.taxamt || header.tax_amount || 0),
        total: parseFloat(header.total || 0),
        printed: header.prtd === 'Y' || header.printed || false,
        orderd_by_customer: header.obycus || '',
        billing: {
            name: header.vndnme || header.vendor_name || '',
            address1: header.vnda1 || '',
            address2: header.vnda2 || '',
            city: header.vndcty || '',
            state: header.vndst || '',
            zip: header.vndzip || '',
            country: header.vndctry || 'USA'
        },
        shipping: {
            name: header.shpnme || '',
            attention: header.shpatn || '',
            address1: header.shpa1 || '',
            address2: header.shpa2 || '',
            city: header.shpcty || '',
            state: header.shpst || '',
            zip: header.shpzip || '',
            country: header.shpctry || 'USA'
        }
    };
}

function format_date(date) {
    if (!date) return '';
    if (typeof date === 'string') return date;
    
    if (date.year && date.month && date.day) {
        const year = date.year;
        const month = String(date.month).padStart(2, '0');
        const day = String(date.day).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    return '';
}

// Add CSS styles
const styles = `
    .hover-bg-light:hover {
        background-color: #f8f9fa;
    }
    .cursor-pointer {
        cursor: pointer;
    }
`;

// Add styles to head
if (typeof document !== 'undefined') {
    const style_element = document.createElement('style');
    style_element.textContent = styles;
    document.head.appendChild(style_element);
}

export default PurchaseOrderBuilder;