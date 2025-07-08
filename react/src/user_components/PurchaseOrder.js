
/**
 * @routes ["PurchaseOrder"]
*/

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, Plus, MessageSquare, Trash2, Save, Truck, X, Copy } from 'lucide-react';

// Main Purchase Order Builder Component
const PurchaseOrder = () => {
    // Get config from props or window
    const config = window.config || {};
    
    // Get navigation hook at the top level
    const navigation = window.useNavigation ? window.useNavigation() : null;
    const view_params = navigation?.view_params || {};
    
    // Merge config with view_params for flexibility
    const merged_config = {
        ...config,
        ...view_params,
        company: config.company || 'PACIFIC',
        data_api: config.data_api || '/v2/api/data'
    };

    const is_view_mode = merged_config.mode === 'view';

    // Core state
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');
    const [availableVendors, setAvailableVendors] = useState(null);

    // Determine if we're in edit mode based on po_number
    const po_number_param = merged_config.po_number || null;
    const is_new_po = !po_number_param || po_number_param === 'NEW';
    const [poNumber, setPoNumber] = useState(is_new_po ? null : po_number_param);
    const [isSaved, setIsSaved] = useState(!is_new_po || is_view_mode); 


    // Compute isEditMode based on current state
    const isEditMode = (!is_new_po || (poNumber && isSaved)) && !is_view_mode;
    const [toast, setToast] = useState(null);

    // PO Data state
    const [vendor, setVendor] = useState(null);
    const [header, setHeader] = useState(get_default_header(merged_config));
    const [lines, setLines] = useState([]);
    const [deletedLineIds, setDeletedLineIds] = useState([]);

    // UI State
    const [vendorComments, setVendorComments] = useState({ show: false, comments1: '', comments2: '' });

    // Virtual inventory state (part -> inventory data)
    const [virtualInventory, setVirtualInventory] = useState({});
    const [inventoryLoading, setInventoryLoading] = useState({});


    useEffect(() => {
        console.log('=== PO STATE DEBUG ===', {
            po_number_param,
            is_new_po,
            poNumber,
            isSaved,
            isEditMode,
            loading,
            has_po_number: !!poNumber,
            button_conditions: {
                show_save: !isSaved,
                show_receive_invoice: isSaved && poNumber,
                actual_condition: !!poNumber
            }
        });
    }, [po_number_param, is_new_po, poNumber, isSaved, isEditMode, loading]);

    // API configuration
    const api_call = async (operation, model, params = {}) => {
        const request_data = {
            operation: operation,
            model: model,
            company: merged_config.company,
            ...params
        };

        // Use existing API manager if available, otherwise use fetch
        if (window.app?.api?.post) {
            return await window.app.api.post(merged_config.data_api, request_data);
        } else {
            // Fallback to fetch
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
            if (is_new_po) {
                // Check if we're in parked order populate mode
                if (merged_config.mode === 'parked_order_populate' && merged_config.order && merged_config.line) {
                    console.log('Detected parked order populate mode', {
                        order: merged_config.order,
                        line: merged_config.line
                    });

                    try {
                        const prefill_result = await api_call('prefill', 'PurchaseOrder', {
                            order_id: merged_config.order,
                            line: merged_config.line
                        });

                        console.log('Prefill API response:', prefill_result);

                        if (prefill_result.success && prefill_result.data) {
                            const prefill_data = prefill_result.data;
                            console.log('Prefill data received:', prefill_data);

                            // Apply pre-populate data to header
                            if (prefill_data.pre_populate_data) {
                                const pre_pop = prefill_data.pre_populate_data;
                                // Set available vendors if provided
                                
                                if (prefill_data.vendors && prefill_data.vendors.length > 0) {
                                    console.log('Setting available vendors:', prefill_data.vendors);
                                    setAvailableVendors(prefill_data.vendors);
                                }

                                // Update header with location and ship_via
                                setHeader(prev => ({
                                    ...prev,
                                    location: pre_pop.location || prev.location,
                                    ship_via: pre_pop.ship_via || prev.ship_via,
                                    ordered_by_customer: pre_pop.customer_code || prev.ordered_by_customer,  
                                    shipping: pre_pop.shipping_address ? {
                                        name: pre_pop.shipping_address.name || '',
                                        attention: pre_pop.shipping_address.attention || '',
                                        address1: pre_pop.shipping_address.address1 || '',
                                        address2: pre_pop.shipping_address.address2 || '',
                                        city: pre_pop.shipping_address.city || '',
                                        state: pre_pop.shipping_address.state || '',
                                        zip: pre_pop.shipping_address.zip || '',
                                        country: 'USA'
                                    } : prev.shipping
                                }));

                                // Add initial items as lines
                                if (pre_pop.initial_items && pre_pop.initial_items.length > 0) {
                                    const new_lines = pre_pop.initial_items.map(item => {
                                        if (item.type === 'note') {
                                            return {
                                                _source: 'active',
                                                type: 'X',
                                                message: item.message || '',
                                                msg: item.message || '',
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
                                        } else {
                                            // Part line
                                            const qty = item.qty || 1;
                                            const price = item.price || 0;
                                            const extended = qty * price;

                                            return {
                                                _source: 'active',
                                                part: item.part || '', pcode: item.part || '',
                                                description: item.description || '', pdesc: item.description || '',
                                                quantity: qty, pqty: qty,
                                                price: price, pprce: price,
                                                discount: 0, pdisc: 0,
                                                extended: extended, pext: extended,
                                                received_qty: 0, rqty: 0,
                                                erd: header.expected_receipt_date,
                                                type: 'R',
                                                taxable: false,
                                                message: '', msg: ''
                                            };
                                        }
                                    });

                                    setLines(new_lines);
                                }
                            }
                        } else {
                            console.error('Prefill failed:', prefill_result.error || 'Unknown error');
                        }
                    } catch (error) {
                        console.error('Error calling prefill:', error);
                    }
                }

                // Only add empty line if we didn't prepopulate
                if (!merged_config.mode || merged_config.mode !== 'parked_order_populate') {
                    add_line();
                }
            } else {
                // Existing PO - load it
                await load_existing_po();
            }
        };

        init();
    }, []);

    // Load existing PO
    const load_existing_po = async () => {
        if (!poNumber) return;
        
        setLoading(true);
        setLoadingMessage('Loading purchase order...');

        try {
            const result = await api_call('get', 'PurchaseOrder', {
                po_number: poNumber
            });

            if (result.success) {
                const cleaned_data = clean_po_data(result);
                setHeader(map_header_data(cleaned_data.header || {}));
                setLines(cleaned_data.lines || []);

                // Load vendor info if we have vendor code
                if (cleaned_data.header?.vendor_code) {
                    await load_vendor_details(cleaned_data.header.vendor_code);
                }
            } else {
                show_error('Failed to load purchase order: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading PO:', error);
            show_error('Failed to load purchase order');
        } finally {
            setLoading(false);
        }
    };

    // Vendor handling
    const handle_vendor_change = async (vendor_data) => {
        if (!vendor_data) {
            setVendor(null);
            setHeader(prev => ({
                ...prev,
                vendor_code: '',
                vendor_name: '',
                billing: {
                    name: '',
                    address1: '',
                    address2: '',
                    city: '',
                    state: '',
                    zip: '',
                    country: 'USA'
                }
            }));
            return;
        }
        
        setVendor(vendor_data);

        // Update header
        setHeader(prev => ({
            ...prev,
            vendor_code: vendor_data.code || '',
            vendor_name: vendor_data.name || '',
            billing: {
                name: vendor_data.name || '',
                address1: vendor_data.add1 || '',
                address2: vendor_data.add2 || '',
                city: vendor_data.city || '',
                state: vendor_data.state || '',
                zip: vendor_data.zip_ || vendor_data.zip || '',
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
        if (!vendor_code) return;
        
        console.log('Loading vendor details for:', vendor_code);
        
        try {
            // Try exact match first
            let result = await api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
                filters: {
                    code: {
                        operator: "eq",
                        value: vendor_code
                    }
                },
                start: 0,
                length: 1
            });

            // If no exact match, try case-insensitive search
            if (!result.success || !result.data || result.data.length === 0) {
                result = await api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
                    filters: {
                        code: {
                            operator: "ilike",
                            value: vendor_code
                        }
                    },
                    start: 0,
                    length: 1
                });
            }

            if (result.success && result.data && result.data.length > 0) {
                console.log('Found vendor:', result.data[0]);
                await handle_vendor_change(result.data[0]);
                return result.data[0];
            } else {
                console.log('No vendor found for code:', vendor_code);
            }
        } catch (error) {
            console.error('Error loading vendor details:', error);
        }
        return null;
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
            type: 'X',
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
            if (line.type !== 'X' && ['quantity', 'price', 'discount'].includes(field)) {
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

        try {
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
        } catch (error) {
            console.error('Error fetching virtual inventory:', error);
            setVirtualInventory(prev => ({ ...prev, [index]: [] }));
        } finally {
            setInventoryLoading(prev => ({ ...prev, [index]: false }));
        }
    };

    const select_vendor_from_inventory = async (vendor_code, line_index) => {
        const vendor_data = await load_vendor_details(vendor_code);
        // Return the vendor data so the VendorSelect component can update
        return vendor_data;
    };

    // Save PO
    const save_po = async () => {
        if (!validate_po()) return;

        setLoading(true);
        setLoadingMessage('Saving purchase order...');

        try {
            // Add line numbers to each line
            const lines_with_numbers = lines.map((line, index) => ({
                ...line,
                line_number: index + 1
            }));

            const save_data = {
                header: header,
                lines: lines_with_numbers,
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
                console.log('SAVE SUCCESS - Before state updates:', {
                    current_poNumber: poNumber,
                    current_isSaved: isSaved,
                    new_po_number: result.data?.po_number
                });
    
                show_toast('Purchase order saved successfully!', 'success');
                setIsSaved(true);
    
                if (!isEditMode && result.data?.po_number) {
                    // Set the PO number for the current session
                    setPoNumber(result.data.po_number);
                    console.log('SAVE SUCCESS - After setPoNumber:', {
                        poNumber: result.data.po_number,
                        isSaved: true
                    });
                }
    
                console.log('SAVE SUCCESS - Final state (may not be updated yet):', {
                    poNumber,
                    isSaved,
                    isEditMode
                });
    
                setDeletedLineIds([]);
            } else {
                show_toast(result.error || result.message || 'Failed to save purchase order', 'error');

            }
        } catch (error) {
            console.error('Error saving PO:', error);
            show_toast('Failed to save purchase order', 'error');
        } finally {
            setLoading(false);
        }
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

    // Sync calculated totals back to header
    useEffect(() => {
        setHeader(prev => ({
            ...prev,
            subtotal: totals.subtotal,
            total: totals.total
        }));
    }, [totals.subtotal, totals.total]);

    // Sync line count to header
    useEffect(() => {
        setHeader(prev => ({
            ...prev,
            line_count: lines.length
        }));
    }, [lines.length]);

    
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
        show_toast(message, 'error');
    };

    const show_success = (message) => {
        show_toast(message, 'success');
    };

    const show_toast = (message, type = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 5000);
    };

    // Render helpers
    const is_partially_received = lines.some(line => line.rqty > 0);
    const can_edit_header = !is_partially_received && !isSaved && !is_view_mode;
    const can_edit_lines = !isSaved && !is_view_mode;

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
                                        vendor_name={header.vendor_name}
                                        vendors={availableVendors}
                                        onVendorChange={handle_vendor_change}
                                        api_call={api_call}
                                        disabled={!can_edit_header || is_view_mode}
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label">Ordered By</label>
                                    <input
                                        type="text"
                                        className="form-control form-control-sm"
                                        value={header.ordered_by_customer || ''}
                                        onChange={(e) => setHeader(prev => ({ ...prev, ordered_by_customer: e.target.value }))}
                                        placeholder="Name..."
                                        disabled={is_view_mode}
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
                                        disabled={!can_edit_header}  // Add disabled prop
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
                                        onChange={(e) => {
                                            const val = parseFloat(e.target.value) || 0;
                                            setHeader(prev => ({ ...prev, freight: Math.max(0, val) }));
                                        }}
                                        min="0"
                                        step="0.01"
                                        disabled={is_view_mode}

                                    />
                                </div>
                                <div className="col-md-12">
                                    <label className="form-label">Location</label>
                                    <LocationSelect
                                        value={header.location}
                                        onChange={(value) => setHeader(prev => ({ ...prev, location: value }))}
                                        api_call={api_call}
                                        company={merged_config.company}
                                        disabled={!can_edit_header}  // Add disabled prop

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
                        readonly={!can_edit_header || is_view_mode}
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
                        readonly={is_view_mode}

                    />
                </div>
            </div>

            {/* Line Items */}
            <div className="card mb-3">
                <div className="card-header d-flex justify-content-between align-items-center">
                    <h6 className="mb-0">Line Items</h6>
                    <div>
                        <AddLineButton
                            onClick={add_line}
                            label="Add Line"
                            icon={Plus}
                            disabled={isSaved || is_view_mode}
                        />
                        <button
                            className="btn btn-secondary btn-sm ms-2"
                            onClick={add_note_line}
                            disabled={isSaved || is_view_mode}
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
                                onSelectVendor={select_vendor_from_inventory}
                                readonly={isSaved || is_view_mode}
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
                {!isSaved && !is_view_mode && (
                    <button
                        className="btn btn-success me-2"
                        onClick={save_po}
                        disabled={loading}
                    >
                        <Save size={16} className="me-1" />
                        {isEditMode ? 'Update PO' : 'Create PO'}
                    </button>
                )}

{isSaved && poNumber && !is_view_mode && (
    <button
        className="btn btn-primary me-2"
        onClick={async () => {
            setLoading(true);
            setLoadingMessage('Processing receive and invoice...');
            
            try {
                // Debug: Check all possible user locations
                console.log('=== USER DEBUG ===', {
                    config: config,
                    config_user: config.user,
                    window_user: window.user,
                    window_app: window.app,
                    window_app_user: window.app?.user,
                    window_app_state: window.app?.state,
                    window_app_state_user: window.app?.state?.user,
                    merged_config: merged_config,
                    merged_config_user: merged_config.user,
                    localStorage_user: localStorage.getItem('user'),
                    sessionStorage_user: sessionStorage.getItem('user')
                });
                
                // Try multiple sources for user
                const user = config.user || 
                           window.user || 
                           window.app?.user || 
                           window.app?.state?.user ||
                           merged_config.user ||
                           (localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null) ||
                           null;
                
                console.log('Final user found:', user);
                
                const result = await api_call('rni_inv', 'PurchaseOrder', {
                    po_number: poNumber,
                    parked_order_id: merged_config.order || merged_config.parked_order_id || null,
                    parked_order_line: merged_config.line || null,
                    user: user,
                    user_id: user?.id || user?.user_id || null,
                    user_name: user?.name || user?.username || null
                });
                
                if (result.success) {
                    show_toast('Successfully received and invoiced PO', 'success');
                    // Navigate back to parked order or PO list
                    if (merged_config.order || merged_config.parked_order_id) {
                        const order_id = merged_config.order || merged_config.parked_order_id;
                        if (navigation) {
                            navigation.navigate_to('ParkedOrderDetail', { id: order_id });
                        }
                    } else {
                        if (navigation) {
                            navigation.navigate_to('PurchaseOrders');
                        }
                    }
                } else {
                    show_error(result.message || 'Failed to receive and invoice PO');
                }
            } catch (error) {
                console.error('Error processing receive and invoice:', error);
                show_error('Failed to receive and invoice PO');
            } finally {
                setLoading(false);
            }
        }}
        disabled={loading}
    >
        <Truck size={16} className="me-1" />
        Receive & Invoice
    </button>
)}

                <CancelButton 
                    navigation={navigation}
                    merged_config={merged_config}
                />
            </div>


        </div>
    );
};

// Sub-components

const CancelButton = ({ navigation, merged_config }) => {
    const handle_cancel = () => {
        // If we came from a parked order, go back to it
        if (merged_config.order || merged_config.parked_order_id) {
            const order_id = merged_config.order || merged_config.parked_order_id;
            if (navigation) {
                navigation.navigate_to('ParkedOrderDetail', { id: order_id });
            }
        } else {
            // Otherwise go to purchase orders list
            if (navigation) {
                navigation.navigate_to('PurchaseOrders');
            }
        }
    };

    // In view mode, you might want to show "Back" instead of "Cancel"
    const button_label = merged_config.mode === 'view' ? 'Back' : 'Cancel';

    return (
        <button
            className="btn btn-secondary"
            onClick={handle_cancel}
        >
            <X size={16} className="me-1" />
            {button_label}
        </button>
    );
};

const VendorSelect = ({ value, vendor_name, vendors, onVendorChange, api_call, disabled }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);

    // Update search term when value changes (e.g., when selected from virtual inventory)
    useEffect(() => {
        if (value && vendor_name) {
            setSearchTerm(`${value} - ${vendor_name}`);
        } else if (value) {
            setSearchTerm(value);
        }
    }, [value, vendor_name]);

    // Search vendors function
    const search_vendors = async (term) => {
        if (term.length < 2) {
            setSuggestions([]);
            return;
        }

        setLoading(true);
        try {
            const result = await api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
                filters: {
                    name: { operator: "ilike", value: `%${term}%` }
                },
                start: 0,
                length: 10
            });

            if (result.success && result.data) {
                setSuggestions(result.data);
            }
        } catch (error) {
            console.error('Error searching vendors:', error);
            setSuggestions([]);
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
    }, [searchTerm, value]);

    // Static vendors mode
    if (vendors && vendors.length > 0) {
        return (
            <select
                className="form-select form-select-sm"
                value={value || ''}
                onChange={async (e) => {
                    const vendor_code = e.target.value;
                    if (!vendor_code) {
                        onVendorChange(null);
                        return;
                    }

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
    return (
        <div className="position-relative">
            <input
                type="text"
                className="form-control form-control-sm"
                value={searchTerm}
                onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowDropdown(true);
                    if (!e.target.value) {
                        onVendorChange(null);
                    }
                }}
                onFocus={() => setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Search vendor by code or name..."
                disabled={disabled}
                required
            />

            {showDropdown && (suggestions.length > 0 || loading) && (
                <div className="dropdown-menu d-block position-absolute mt-1" style={{ minWidth: '400px', maxHeight: '300px', overflowY: 'auto' }}>
                    {loading && (
                        <div className="dropdown-item-text text-center">
                            <small className="text-muted">Loading...</small>
                        </div>
                    )}
                    {!loading && suggestions.map(vendor => (
                        <button
                            key={vendor.code}
                            className="dropdown-item text-truncate"
                            type="button"
                            onClick={() => {
                                onVendorChange(vendor);
                                setSearchTerm(`${vendor.code} - ${vendor.name}`);
                                setShowDropdown(false);
                            }}
                            title={`${vendor.code} - ${vendor.name}`}
                        >
                            <strong>{vendor.code}</strong> - {vendor.name}
                        </button>
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
            const result = await api_call('list', 'GPACIFIC_dbo_BKSYTERM', {
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

const LocationSelect = ({ value, onChange, api_call, company, disabled }) => {
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
            disabled={disabled}  // Add disabled prop
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
    const ship_options = ['UPS', 'FEDEX', 'WILL CALL', 'LOCAL', 'FREIGHT', 'USPS', 'DHL'];

    return (
        <select
            className="form-select form-select-sm"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
        >
            <option value="">Select ship via...</option>
            {ship_options.map(opt => (
                <option key={opt} value={opt}>
                    {opt}
                </option>
            ))}
        </select>
    );
};

const AddressCard = ({ title, address, onChange, readonly, showCopyButton, onCopy }) => {
    return (
        <div className="card h-100">
            <div className="card-header d-flex justify-content-between align-items-center">
                <h6 className="mb-0">{title}</h6>
                {showCopyButton && !readonly && (
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
                                readOnly={readonly}
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

const LineItem = ({ line, index, onUpdate, onRemove, api_call, virtualInventory, inventoryLoading, onFetchInventory, onSelectVendor, readonly }) => {

    const is_received = parseFloat(line.rqty || 0) > 0;
    const is_historical = line._source === 'historical';
    const is_readonly = is_received || is_historical || readonly;

    const line_number = index + 1;
    const is_note_line = line.type === 'X' || (!line.pcode && !line.part && line.msg);

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
                        <RemoveLineButton 
                            onRemove={() => onRemove(index)}
                        />
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
                            readonly={is_readonly || readonly}  // Add the parent readonly prop
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
                            onChange={(e) => {
                                const val = parseFloat(e.target.value) || 0;
                                onUpdate(index, 'quantity', Math.max(0, val));
                            }}
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
                            onChange={(e) => {
                                const val = parseFloat(e.target.value) || 0;
                                onUpdate(index, 'price', Math.max(0, val));
                            }}
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
                            onChange={(e) => {
                                const val = parseFloat(e.target.value) || 0;
                                onUpdate(index, 'discount', Math.max(0, val));
                            }}
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
                            readOnly={is_readonly || readonly}  // Add parent readonly prop
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
                                                            <UseVendorButton
                                                                vendor_code={(item.company || '').toUpperCase()}
                                                                onSelectVendor={onSelectVendor}
                                                            />
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
    const [searchTerm, setSearchTerm] = useState(value || '');
    const [suggestions, setSuggestions] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
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
                order: [{ column: 0, dir: 'asc' }],
                columns: [{ name: 'part' }, { name: 'inventory_description' }],
                filters: {
                    part: { operator: "ilike", value: `${term}%` }
                },
                start: 0,
                length: 20
            });

            if (result.success && result.data) {
                setSuggestions(result.data);
            } else {
                setSuggestions([]);
            }
        } catch (error) {
            console.error('Error searching parts:', error);
            setSuggestions([]);
        }
        setLoading(false);
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchTerm) {
                search_parts(searchTerm);
            } else {
                setSuggestions([]);
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
                    const new_value = e.target.value;
                    setSearchTerm(new_value);
                    onChange(new_value);
                    setShowDropdown(true);
                }}
                onFocus={() => {
                    setShowDropdown(true);
                    if (searchTerm && suggestions.length === 0) {
                        search_parts(searchTerm);
                    }
                }}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="Search part..."
                readOnly={readonly}
            />

            {showDropdown && (searchTerm.length >= 2 || suggestions.length > 0) && (
                <div className="dropdown-menu d-block position-absolute w-100 mt-1" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {loading && (
                        <div className="dropdown-item-text text-center">
                            <small className="text-muted">Searching parts...</small>
                        </div>
                    )}
                    {!loading && suggestions.length === 0 && searchTerm.length >= 2 && (
                        <div className="dropdown-item-text text-center">
                            <small className="text-muted">No parts found</small>
                        </div>
                    )}
                    {!loading && suggestions.map(part => (
                        <button
                            key={part.part}
                            className="dropdown-item"
                            type="button"
                            onClick={() => {
                                onPartSelect(part);
                                setSearchTerm(part.part);
                                setShowDropdown(false);
                                setSuggestions([]);
                            }}
                        >
                            <strong>{part.part}</strong>
                            {part.inventory_description && (
                                <div className="small text-muted">{part.inventory_description}</div>
                            )}
                        </button>
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

const RemoveLineButton = ({ onRemove }) => {
    return (
        <button
            className="btn btn-sm btn-danger"
            onClick={onRemove}
        >
            <Trash2 size={16} />
        </button>
    );
};

const UseVendorButton = ({ vendor_code, onSelectVendor }) => {
    const handle_click = async () => {
        await onSelectVendor(vendor_code);
    };
    
    return (
        <button
            className="btn btn-sm btn-primary"
            onClick={handle_click}
        >
            Use
        </button>
    );
};

const AddLineButton = ({ onClick, label, icon: Icon, disabled }) => {
    return (
        <button
            className="btn btn-sm btn-primary"
            onClick={onClick}
            disabled={disabled}
        >
            <Icon size={16} className="me-1" />
            {label}
        </button>
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
        ordered_by_customer: '',
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
            // Clean null characters from messages
            if (line.msg) {
                const clean_msg = line.msg.split('\x00')[0].trim();
                line.msg = clean_msg;
            }
            if (line.message) {
                const clean_message = line.message.split('\x00')[0].trim();
                line.message = clean_message;
            }
            
            // Clean null characters from other fields
            ['gla', 'gldpta', 'tskcod', 'cat'].forEach(field => {
                if (line[field] && typeof line[field] === 'string') {
                    line[field] = line[field].replace(/\x00/g, '').trim();
                }
            });
            
            
            // Ensure both message formats are populated
            if (line.message && !line.msg) {
                line.msg = line.message;
            } else if (line.msg && !line.message) {
                line.message = line.msg;
            }
            
            return line;
        });
    }

    return {
        header: data.header || {},
        lines: data.lines || [],
        source_info: data.source_info || {},
        expected_receipt_date: data.expected_receipt_date || ''
    };
}

function map_header_data(header) {
    // For existing POs, check if we already have the modern structure
    const has_modern_structure = header.billing && typeof header.billing === 'object';
    
    return {
        vendor_code: header.vendor_code || header.vndcod || '',
        vendor_name: header.vendor_name || header.vndnme || '',
        order_date: format_date(header.order_date || header.orddte),
        expected_receipt_date: format_date(header.expected_receipt_date || header.erd),
        location: header.location || header.loc || 'TAC',
        entered_by: header.entered_by || header.entby || '',
        terms: header.terms || header.termd || '',
        ship_via: header.ship_via || header.shpvia || 'UPS',
        freight: parseFloat(header.freight || header.frght || 0),
        subtotal: parseFloat(header.subtotal || header.subtot || 0),
        tax_amount: parseFloat(header.tax_amount || header.taxamt || 0),
        total: parseFloat(header.total || 0),
        printed: header.printed || header.prtd === 'Y' || false,
        ordered_by_customer: header.ordered_by_customer || header.obycus || '',
        
        // Handle billing - use modern structure if available, otherwise map old fields
        billing: has_modern_structure && header.billing ? header.billing : {
            name: header.vendor_name || header.vndnme || '',
            address1: header.vnda1 || '',
            address2: header.vnda2 || '',
            city: header.vndcty || '',
            state: header.vndst || '',
            zip: header.vndzip || '',
            country: header.vndctry || 'USA'
        },
        
        // Handle shipping - use modern structure if available, otherwise map old fields
        shipping: has_modern_structure && header.shipping ? header.shipping : {
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

export default PurchaseOrder;