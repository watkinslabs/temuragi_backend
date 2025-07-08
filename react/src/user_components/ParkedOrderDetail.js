/**
 * @routes ["ParkedOrderDetail"]
*/

const ParkedOrderDetail = () => {
    // Get React from window
    const React = window.React;
    const { useState, useEffect } = React;
    
    // Get hooks from window
    const useNavigation = window.useNavigation;
    const useSite = window.useSite;
    const config = window.config;
    
    // State
    const [loading, set_loading] = useState(true);
    const [order, set_order] = useState(null);
    const [error, set_error] = useState(null);
    
    // Now use the hooks
    const { navigate_to, view_params } = useNavigation();
    const { current_context } = useSite();
    
    // Get the order_id from view_params
    const order_id = view_params?.id;

    // Load order data
    useEffect(() => {
        const load_order = async () => {
            try {
                set_loading(true);
                const response = await config.apiCall('/v2/api/data', {
                    method: 'POST',
                    headers: config.getAuthHeaders(),
                    body: JSON.stringify({
                        model: 'ParkedOrderDetails',
                        operation:'get',
                        company: 'PACIFIC',
                        pr_repair_order_id: order_id,  
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to load order details');
                }
                
                const data = await response.json();
                if (data.success) {
                    set_order(data.order);
                } else {
                    throw new Error(data.error || 'Failed to load order');
                }
            } catch (err) {
                console.error('Error loading order:', err);
                set_error(err.message);
            } finally {
                set_loading(false);
            }
        };
        
        if (order_id) {  // Only load if we have an order_id
            load_order();
        }
    }, [order_id, current_context]);

    
    // Handle navigation actions
    const handle_create_po = (part) => {
        navigate_to('PurchaseOrder', {
            line: part.line,
            order: order.order_info.pr_repair_order_id,
            warehouse_code:order.closest_warehouse.code,
            mode: 'parked_order_populate'
        });
    };

    const handle_view_po = (po_number) => {
        navigate_to('PurchaseOrder', {
            po_number: po_number,
            mode:'view',
            order: order.order_info.pr_repair_order_id,
        });
    };

    const handle_view_so = (so_number) => {
        navigate_to('SalesOrderDetail', {
            so_number: so_number,
            mode: 'view',
            from: {
                view: "ParkedOrderDetails",
                order_id: order.order_info.pr_repair_order_id,
            }
        });
    };

    const handle_back_to_list = () => {
        navigate_to('ParkedOrders');
    };
    
    // Get part status badge
    const get_part_status_badge = (part) => {
        if (part.status === 'FULLY_INVOICED') {
            return <span className="badge bg-success">FULLY INVOICED</span>;
        } else if (part.quantity_ordered > 0 && part.quantity_ordered < part.quantity_needed) {
            return <span className="badge bg-warning">PARTIAL</span>;
        } else if (part.quantity_ordered === 0) {
            return <span className="badge bg-danger">NOT ORDERED</span>;
        } else {
            return <span className="badge bg-secondary">{part.status}</span>;
        }
    };

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                <div className="text-center">
                    <div className="spinner-border text-primary mb-3" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p>Loading order details...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container-fluid">
                <div className="alert alert-danger">
                    <i className="fas fa-exclamation-circle me-2"></i>
                    {error}
                </div>
            </div>
        );
    }

    if (!order) {
        return (
            <div className="container-fluid">
                <div className="alert alert-warning">
                    <i className="fas fa-exclamation-triangle me-2"></i>
                    No order data found
                </div>
            </div>
        );
    }

    return (
        <div className="container-fluid">
            {/* Header */}
            <div className="row mb-4">
                <div className="col-12">
                    <h1 className="h2">
                        <i className="fas fa-clipboard-list me-3"></i>
                        Parked Order #{order.order_info.pt_order_id}
                    </h1>
                </div>
            </div>
            
            {/* Order Info Cards */}
            <div className="row mb-4">
                {/* Order Information Card */}
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="mb-0">
                                <i className="fas fa-file-alt me-2"></i>
                                Order Information
                            </h5>
                        </div>
                        <div className="card-body">
                            <table className="table table-sm table-borderless mb-0">
                                <tbody>
                                    <tr>
                                        <td className="text-muted small">Parts Trader Order</td>
                                        <td className="fw-bold text-end">{order.order_info.pt_order_id}</td>
                                    </tr>
                                    <tr>
                                        <td className="text-muted small">Performance Radiator RO</td>
                                        <td className="fw-bold text-end">#{order.order_info.pr_repair_order_id}</td>
                                    </tr>
                                    <tr>
                                        <td className="text-muted small">Status</td>
                                        <td className="fw-bold text-end">{order.order_info.status}</td>
                                    </tr>
                                    <tr>
                                        <td className="text-muted small">Created Date</td>
                                        <td className="fw-bold text-end">{order.order_info.created_at}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                {/* Performance Radiator Customer Card */}
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="mb-0">
                                <i className="fas fa-building me-2"></i>
                                Performance Radiator Customer
                            </h5>
                        </div>
                        <div className="card-body">
                            {order.customer ? (
                                <>
                                    {/* Customer Section */}
                                    <div className="customer-section mb-3">
                                        <div className="customer-details">
                                            <p className="mb-1">
                                                <strong>{order.customer.name}</strong>
                                            </p>
                                            <p className="mb-1">{order.customer.address_1}</p>
                                            {order.customer.address_2 && (
                                                <p className="mb-1">{order.customer.address_2}</p>
                                            )}
                                            <p className="mb-1">
                                                {order.customer.city}, {order.customer.state} {order.customer.zip}
                                            </p>
                                            <p className="mb-1">
                                                <span className="text-muted">Customer Code:</span>{' '}
                                                <strong>{order.customer.customer_code}</strong>
                                            </p>
                                            {order.customer.phone && (
                                                <p className="mb-0">
                                                    <i className="fas fa-phone me-2 text-muted"></i>
                                                    <a href={`tel:${order.customer.phone}`}>{order.customer.phone}</a>
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    
                                    <hr className="my-3" />
                                    
                                    {/* Warehouse Section */}
                                    {order.closest_warehouse ? (
                                        <div className="warehouse-section">
                                            <h6 className="text-muted small mb-2">Customer Assigned Location</h6>
                                            <div className="warehouse-details">
                                                <p className="mb-1">
                                                    <strong>
                                                        {order.closest_warehouse.name} ({order.closest_warehouse.code})
                                                    </strong>
                                                </p>
                                                <p className="mb-1">{order.closest_warehouse.address}</p>
                                                <p className="mb-1">
                                                    {order.closest_warehouse.city}, {order.closest_warehouse.state}{' '}
                                                    {order.closest_warehouse.zip}
                                                </p>
                                                {order.closest_warehouse.distance_miles && (
                                                    <p className="mb-0">
                                                        <span className="text-muted">Distance:</span>{' '}
                                                        <strong>{order.closest_warehouse.distance_miles} miles</strong>
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="alert alert-warning mb-0">
                                            <i className="fas fa-exclamation-triangle me-2"></i>
                                            <strong>No warehouse assigned</strong>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="alert alert-danger">
                                    <i className="fas fa-exclamation-circle me-2"></i>
                                    <strong>NEEDS CUSTOMER MAPPING</strong>
                                    <p className="mb-0 mt-2 small">
                                        Customer information is missing. PO creation is disabled until customer is mapped.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
                
                {/* PartsTrader Customer Card */}
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="mb-0">
                                <i className="fas fa-user me-2"></i>
                                PartsTrader Customer
                            </h5>
                        </div>
                        <div className="card-body">
                            <div className="row">
                                <div className="col-md-12">
                                    {/* Repairer Section */}
                                    <div className="repairer-section mb-4">
                                        <div className="repairer-details">
                                            <p className="mb-1">
                                                <strong>{order.repairer.name}</strong>
                                            </p>
                                            <p className="mb-1">{order.repairer.address}</p>
                                            {order.repairer.address2 && (
                                                <p className="mb-1">{order.repairer.address2}</p>
                                            )}
                                            <p className="mb-2">
                                                {order.repairer.city}, {order.repairer.state_province},{' '}
                                                {order.repairer.postal_code}
                                            </p>
                                            <p className="mb-0">
                                                <span className="text-muted">Customer Code:</span>{' '}
                                                <strong>{order.repairer.customer_code}</strong>
                                            </p>
                                        </div>
                                    </div>
                                    
                                    {/* Requester Section */}
                                    <div className="requester-section">
                                        <div className="requester-details">
                                            <p className="mb-2">
                                                <strong>{order.requester.name}</strong>
                                            </p>
                                            <p className="mb-1">
                                                <i className="fas fa-envelope me-2 text-muted"></i>
                                                <a href={`mailto:${order.requester.email}`}>
                                                    {order.requester.email}
                                                </a>
                                            </p>
                                            <p className="mb-0">
                                                <i className="fas fa-phone me-2 text-muted"></i>
                                                <a href={`tel:${order.requester.phone}`}>
                                                    {order.requester.phone}
                                                </a>
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Order Summary Stats */}
            <div className="row mb-4">
                <div className="col-12">
                    <div className="alert alert-info">
                        <i className="fas fa-info-circle me-2"></i>
                        <strong>Order Summary:</strong>
                        {' '}Total Parts: {order.order_summary.total_parts} |
                        {' '}POs Created: {order.order_summary.total_pos_created}
                        {order.order_summary.parts_fully_ordered > 0 && (
                            <> | Fully Ordered: {order.order_summary.parts_fully_ordered}</>
                        )}
                        {order.order_summary.parts_partially_ordered > 0 && (
                            <> | Partially Ordered: {order.order_summary.parts_partially_ordered}</>
                        )}
                        {order.order_summary.parts_not_ordered > 0 && (
                            <> | Not Ordered: {order.order_summary.parts_not_ordered}</>
                        )}
                    </div>
                </div>
            </div>
            
            {/* Parts Table */}
            <div className="row mb-4">
                <div className="col-12">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="mb-0">
                                <i className="fas fa-boxes me-2"></i>
                                Parts Details
                            </h5>
                        </div>
                        <div className="card-body p-0">
                            <div className="table-responsive">
                                <table className="table table-hover mb-0">
                                    <thead>
                                        <tr>
                                            <th>Line</th>
                                            <th>Part Number</th>
                                            <th>Description</th>
                                            <th className="text-center">Qty</th>
                                            <th>Status</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {order.parts.map((part) => (
                                            <React.Fragment key={part.line}>
                                                <tr>
                                                    <td>{part.line}</td>
                                                    <td><strong>{part.part_number}</strong></td>
                                                    <td>{part.description || 'N/A'}</td>
                                                    <td className="text-center">{part.quantity_needed}</td>
                                                    <td>{get_part_status_badge(part)}</td>
                                                    <td>
                                                        {part.quantity_ordered < part.quantity_needed && (
                                                            <>
                                                                {order.customer && order.closest_warehouse ? (
                                                                    <button
                                                                        className="btn btn-sm btn-success"
                                                                        onClick={() => handle_create_po(part)}
                                                                    >
                                                                        <i className="fas fa-plus me-1"></i>
                                                                        Create PO
                                                                    </button>
                                                                ) : (
                                                                    <button
                                                                        className="btn btn-sm btn-danger"
                                                                        disabled
                                                                        title="Customer mapping required"
                                                                    >
                                                                        <i className="fas fa-exclamation-circle me-1"></i>
                                                                        No Customer
                                                                    </button>
                                                                )}
                                                            </>
                                                        )}
                                                    </td>
                                                </tr>
                                                
                                                {/* Purchase Orders for this part */}
                                                {part.purchase_orders && part.purchase_orders.map((po) => (
                                                    <tr key={`po-${po.po_number}`} className="table-secondary">
                                                        <td></td>
                                                        <td colSpan="5">
                                                            <i className="fas fa-level-up-alt me-2"></i>
                                                            <strong>PO #{po.po_number}</strong> - 
                                                            Quantity: {po.quantity}
                                                            <button
                                                                className="btn btn-sm btn-outline-primary ms-3"
                                                                onClick={() => handle_view_po(po.po_number)}
                                                            >
                                                                <i className="fas fa-eye me-1"></i>
                                                                View PO
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                                
                                                {/* Sales Orders for this part */}
                                                {part.sales_orders && part.sales_orders.map((so) => (
                                                    <tr key={`so-${so.so_number}`} className="table-info">
                                                        <td></td>
                                                        <td colSpan="5">
                                                            <i className="fas fa-level-up-alt me-2"></i>
                                                            <strong>SO #{so.so_number}</strong> - 
                                                            Quantity: {so.quantity} | 
                                                            Status: {so.status}
                                                            {so.inv_number && so.inv_number !== 999999 && (
                                                                <> | Invoice #{so.inv_number}</>
                                                            )}
                                                            <button
                                                                className="btn btn-sm btn-outline-info ms-3"
                                                                onClick={() => handle_view_so(so.so_number)}
                                                            >
                                                                <i className="fas fa-eye me-1"></i>
                                                                View SO
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </React.Fragment>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Action Bar */}
            <div className="row">
                <div className="col-12">
                    <button
                        className="btn btn-secondary"
                        onClick={handle_back_to_list}
                    >
                        <i className="fas fa-arrow-left me-2"></i>
                        Back to List
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ParkedOrderDetail;