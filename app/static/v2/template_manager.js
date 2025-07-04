class PurchaseOrderBuilder {
    constructor(config) {
        // Only need the data API URL now
        this.data_api_url = config.data_api;
        
        
        // Configuration
        this.po_number = config.po_number || null;
        this.is_edit_mode = !!this.po_number && this.po_number !== 'NEW';
        this.company = config.company || 'PACIFIC';
        this.location = config.location || 'TAC';
        this.container_id = config.container_id || 'main-content';
        
        // Pre-population data for new POs
        this.pre_populate_data = {
            location: config.location,
            ship_via: config.ship_via,
            shipping_address: config.shipping_address,
            initial_items: config.initial_items || [],
            vendors:config.vendors || false,
            parked_order_id : config.parked_order_id || 0
        };
        // Model names for API calls
        this.models = {
            purchase_order: 'PurchaseOrder',
            vendors: 'GPACIFIC_dbo_BKAPVEND',
            parts: 'JADVDATA_dbo_part_meta',
            ship_methods: 'BKSYSSHIP',
            locations: 'JADVDATA_dbo_locations',
            terms: 'GPACIFIC_dbo_BKSYTERM',
            icmstr: 'GPACIFIC_dbo_BKICMSTR'
        };

        // State
        this.po_data = {
            header: this.get_default_header(),
            lines: [],
            source_info: {
                active_line_count: 0,
                has_active_lines: true,
                has_historical_lines: false,
                historical_line_count: 0,
                is_active: true,
                is_partially_received: false
            }
        };

        // Track deleted lines for backend sync
        this.deleted_line_ids = [];

        // Register globally
        window.purchaseOrderBuilder = this;

        // Initialize
        this.init();
    }

    // Central API function for all data operations
    async api_call(operation, model, params = {}) {
        const request_data = {
            operation: operation,
            model: model,
            company: this.company,
            ...params
        };

        const result = await window.app.api.post(this.data_api_url, request_data);
        
        if (!result.success) {
            console.error(`API call failed: ${operation} ${model}`, result);
        }
        
        return result;
    }

    async init() {
        // Build the UI first
        this.build_ui();
        
        // Set today's date for order date
        const today = new Date();
        const todayString = today.toISOString().split('T')[0];
        $('#order_date').val(todayString);

        // Set expected receipt date to +2 days
        const expectedDate = new Date(today);
        expectedDate.setDate(expectedDate.getDate() + 2);
        const expectedDateString = expectedDate.toISOString().split('T')[0];
        $('#expected_receipt_date').val(expectedDateString);

        // Setup event handlers
        this.setup_event_handlers();
        await this.load_terms_and_locations();

        // If in NEW mode, just show the form without loading data
        if (this.po_number === 'NEW') {
            this.is_edit_mode = false;
            this.po_number = null;
            
            this.apply_pre_population();
    
            // Add first empty line only if no initial items
            if (this.pre_populate_data.initial_items.length === 0) {
                this.add_line();
            }
            
            // Update UI state
            this.update_ui_state();
            
            console.log('Purchase Order Builder initialized in NEW mode');
            return;
        }
        
        // Otherwise, load data
        this.show_loading(true);

        // If editing, load existing PO
        if (this.is_edit_mode) {
            await this.load_existing_po();
        } else {
            // Add first empty line for new PO
            this.add_line();
        }

        // Update UI state
        this.update_ui_state();

        console.log('Purchase Order Builder initialized successfully');
        this.show_loading(false);
    }

    build_ui() {
        const container = $(`#${this.container_id}`);
        
        // Check if we should use select or input for vendor
        const vendor_field_html = this.pre_populate_data.vendors && this.pre_populate_data.vendors.length > 0
            ? `<select class="form-select form-select-sm" id="vendor_code" required>
                   <option value="">Select vendor...</option>
               </select>`
            : `<input type="text" class="form-control form-control-sm" id="vendor_code" placeholder="Search vendor..." required>`;
        
        const html = `
            <!-- Loading overlay -->
            <div id="loadingOverlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                 background: rgba(0,0,0,0.5); display: none; z-index: 9999; align-items: center; justify-content: center;">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>

            <div class="container-fluid mt-3">
                <h4 class="mb-3">Purchase Order <span id="po_number_display">${this.po_number ? '#' + this.po_number : ''}</span></h4> 
                
                <!-- Header Section -->
                <div class="row g-3">
                    <!-- Order Details Card -->
                    <div class="col-lg-6 mb-3">
                        <div class="card h-100 mb-3">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">Order Details</h6>
                                <span id="printed_badge" class="badge bg-success" style="display: none;">Printed</span>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-md-6">
                                        <label for="vendor_code" class="form-label">Vendor <span class="text-danger">*</span></label>
                                        ${vendor_field_html}
                                    </div>
                                    <div class="col-md-6">
                                        <label for="ordered_by" class="form-label">Ordered By</label>
                                        <input type="text" class="form-control form-control-sm" id="ordered_by" placeholder="Name...">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="order_date" class="form-label">Order Date <span class="text-danger">*</span></label>
                                        <input type="date" class="form-control form-control-sm" id="order_date" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="expected_receipt_date" class="form-label">Expected Date <span class="text-danger">*</span></label>
                                        <input type="date" class="form-control form-control-sm" id="expected_receipt_date" required>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Shipping Details Card -->
                    <div class="col-lg-6 mb-3">
                        <div class="card h-100 mb-3">
                            <div class="card-header">
                                <h6 class="mb-0">Shipping Details</h6>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-md-4">
                                        <label for="terms" class="form-label">Terms</label>
                                        <select class="form-select form-select-sm" id="terms">
                                            <option value="">Select Terms...</option>
                                        </select>
                                    </div>
                                    <div class="col-md-4">
                                        <label for="ship_via" class="form-label">Ship Via</label>
                                        <input type="text" class="form-control form-control-sm" id="ship_via" value="UPS" placeholder="Ship...">
                                    </div>
                                    <div class="col-md-4">
                                        <label for="freight" class="form-label">Freight</label>
                                        <input type="number" class="form-control form-control-sm" id="freight" value="0" min="0" step="0.01">
                                    </div>
                                    <div class="col-md-12">
                                        <label for="location" class="form-label">Location</label>
                                        <select class="form-select form-select-sm" id="location">
                                            <option value="">Select Location...</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Vendor Comments Warning -->
                <div id="vendor_comments_alert" class="alert alert-warning" style="display: none;">
                    <h6 class="alert-heading">Vendor Notes:</h6>
                    <div id="vendor_comments_content"></div>
                </div>
      
                <!-- Split Addresses Section -->
                <div class="row g-3 mb-3">
                    <!-- Billing Address Card -->
                    <div class="col-lg-6">
                        <div class="card h-100">
                            <div class="card-header">
                                <h6 class="mb-0">Billing Address</h6>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_name" placeholder="Company Name">
                                    </div>
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_address1" placeholder="Address Line 1">
                                    </div>
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_address2" placeholder="Address Line 2">
                                    </div>
                                    <div class="col-6">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_city" placeholder="City">
                                    </div>
                                    <div class="col-2">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_state" placeholder="ST" maxlength="2">
                                    </div>
                                    <div class="col-4">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_zip" placeholder="ZIP">
                                    </div>
                                    <div class="col-12" style="display:none;">
                                        <input type="text" class="form-control form-control-sm billing-field" id="billing_country" value="USA">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Shipping Address Card -->
                    <div class="col-lg-6">
                        <div class="card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">Shipping Address</h6>
                                <button type="button" class="btn btn-sm btn-secondary" id="copy_billing_btn">
                                    Copy from Billing
                                </button>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_name" placeholder="Company Name">
                                    </div>
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_attention" placeholder="Attention">
                                    </div>
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_address1" placeholder="Address Line 1">
                                    </div>
                                    <div class="col-12">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_address2" placeholder="Address Line 2">
                                    </div>
                                    <div class="col-6">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_city" placeholder="City">
                                    </div>
                                    <div class="col-2">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_state" placeholder="ST" maxlength="2">
                                    </div>
                                    <div class="col-4">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_zip" placeholder="ZIP">
                                    </div>
                                    <div class="col-12" style="display:none;">
                                        <input type="text" class="form-control form-control-sm shipping-field" id="shipping_country" value="USA">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Line Items Section -->
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">Line Items</h6>
                        <div>
                            <button type="button" class="btn btn-primary btn-sm" id="add_line_btn">
                                <i class="fas fa-plus"></i> Add Line
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" id="add_note_btn">
                                <i class="fas fa-comment"></i> Add Note
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="po_lines_container">
                            <!-- Lines will be rendered here -->
                        </div>
                    </div>
                </div>

                <!-- Totals Section -->
                <div class="row mb-3">
                    <div class="col-md-4 offset-md-8">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between mb-2">
                                    <span>Subtotal:</span>
                                    <strong id="subtotal_display">$0.00</strong>
                                </div>
                                <div class="d-flex justify-content-between mb-2">
                                    <span>Tax:</span>
                                    <strong id="tax_display">$0.00</strong>
                                </div>
                                <div class="d-flex justify-content-between mb-2">
                                    <span>Freight:</span>
                                    <strong id="freight_display">$0.00</strong>
                                </div>
                                <hr>
                                <div class="d-flex justify-content-between">
                                    <span class="h5">Total:</span>
                                    <strong class="h5" id="total_display">$0.00</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="mb-4">
                    <button type="button" class="btn btn-success" id="save_po_btn">
                        <i class="fas fa-save"></i> <span id="save_button_text">Create PO</span>
                    </button>
                    <button type="button" class="btn btn-primary" id="receive_po_btn" style="display:none;">
                        <i class="fas fa-truck"></i> Receive
                    </button>

                    
                    <a class="btn btn-secondary" 
                                href="/v2/parked_orders/manage" 
                                hx-indicator=".htmx-indicator"  
                                hx-post="/v2/parked_orders/manage" 
                                hx-ext="json-enc"
                                hx-swap="innerHTML" 
                                hx-target="#main-content"  
                                hx-vals='{"id":${this.pre_populate_data.parked_order_id}}'>
                        <i class="fas fa-times"></i> Cancel
                    </a>
                </div>
            </div>
        `;

        container.html(html);

        // Add minimal styles - only what's absolutely necessary
        const styles = `
            <style>
                .readonly-line {
                    background-color: #f8f9fa;
                    opacity: 0.9;
                }
                
                .readonly-line input {
                    background-color: #e9ecef;
                    cursor: not-allowed;
                }
                
                .received-badge {
                    background-color: #28a745;
                    color: white;
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.25rem;
                    font-size: 0.875rem;
                    margin-left: 0.5rem;
                }
                
                #loadingOverlay.show {
                    display: flex !important;
                }
                
                .line-number {
                    font-weight: bold;
                    color: #6c757d;
                    margin-right: 0.5rem;
                }
            </style>
        `;
        
        $('head').append(styles);
    }

    setup_event_handlers() {
        const self = this;

        // Check if we have static vendors
        if (this.pre_populate_data.vendors && this.pre_populate_data.vendors.length > 0) {
            // Populate vendor select dropdown
            const $vendor_select = $('#vendor_code');
            this.pre_populate_data.vendors.forEach(vendor => {
                $vendor_select.append(`<option value="${vendor.company}">${vendor.code} - ${vendor.company}</option>`);
            });
            
            // Handle select change
            $vendor_select.on('change', async function() {
                const selected_code = $(this).val();
                if (selected_code) {
                    // Show loading
                    self.show_loading(true);
                    
                    try {
                        // Fetch full vendor details from API
                        const result = await self.api_call('list', self.models.vendors, {
                            filters: {
                                code: {
                                    operator: "eq",
                                    value: selected_code
                                }
                            },
                            start: 0,
                            length: 1
                        });
                        
                        if (result.success && result.data && result.data.length > 0) {
                            const vendor = result.data[0];
                            self.on_vendor_change(vendor);
                        } else {
                            self.show_error('Failed to load vendor details');
                        }
                    } catch (error) {
                        console.error('Error fetching vendor details:', error);
                        self.show_error('Error loading vendor details');
                    } finally {
                        self.show_loading(false);
                    }
                }
            });
        } else {
            // Use autocomplete for dynamic vendor search
            $('#vendor_code').autocomplete({
                source: async (request, response) => {
                    const result = await self.api_call('list', self.models.vendors, {
                        "filters": {
                            "name": {
                                "operator": "ilike",
                                "value": request.term
                            }
                        }
                    });
                    
                    if (result.success && result.data) {
                        response(result.data.map(vendor => ({
                            label: `${vendor.code} - ${vendor.name}`,
                            value: vendor.code,
                            vendor: vendor
                        })));
                    } else {
                        response([]);
                    }
                },
                minLength: 2,
                select: (event, ui) => {
                    self.on_vendor_change(ui.item.vendor);
                    return true;
                }
            });
        }

        // Ship Via autocomplete
        $('#ship_via').autocomplete({
            source: async (request, response) => {
                const result = await self.api_call('list', self.models.ship_methods, {
                    search: request.term
                });
                
                if (result.success && result.data) {
                    response(result.data);
                } else {
                    // Fallback to common options
                    response(['UPS', 'FEDEX', 'USPS', 'DHL', 'FREIGHT', 'PICKUP']);
                }
            },
            minLength: 0
        }).on('focus', function() {
            // Show all options on focus if empty
            if ($(this).val() === '') {
                $(this).autocomplete('search', '');
            }
        });

        // Header fields
        $('#order_date, #expected_receipt_date').on('change', () => self.update_header_from_form());
        $('#ship_via, #location, #terms').on('change', () => self.update_header_from_form());
        $('#freight').on('input', () => {
            self.update_header_from_form();
            self.calculate_totals();
        });

        // Address fields
        $('.billing-field, .shipping-field').on('input', () => self.update_header_from_form());

        // Buttons
        $('#add_line_btn').on('click', () => self.add_line());
        $('#add_note_btn').on('click', () => self.add_note_line());
        $('#save_po_btn').on('click', () => self.save_po());
        $('#receive_po_btn').on('click', () => self.show_receive_modal());
        $('#copy_billing_btn').on('click', () => self.copy_billing_to_shipping());
    }

    async load_terms_and_locations() {
        // Load terms
        const terms_result = await this.api_call('list', 
            window.purchaseOrderBuilder.models.terms,
            {start:0,
            length:0,
            return_columns: ["num", "desc"],
            order:[{'column':0,'dir':'asc'}],
            columns:[{'name':'num'},{'name':'desc'}]
            }
        );

        if (terms_result.success && terms_result.data) {
            const $terms = $('#terms');
            terms_result.data.forEach(term => {
                $terms.append(`<option value="${term.num}">${term.desc}</option>`);
            });
              /*  $terms.selectpicker({
                    size: 10,  // Shows scrollbar after 10 items
                    style: 'btn-sm',
                    width: 'fit',
                    container: 'body'
                });*/
        }
        
        // Load locations  
        const locations_result = await this.api_call('list', window.purchaseOrderBuilder.models.locations,
                {
                    start:0,
                    length:0,
                    return_columns: ["location", "location_name"],
                    order:[{'column':1,'dir':'asc'}],
                    columns:[{'name':'location'},{'name':'location_name'}],
                    "filters": {
                        "company": {
                            "operator": "eq",
                            "value": "PACIFIC"
                        },
                        "warehouse": {
                            "operator": "eq",
                            "value": "1"
                        },
                        "active": {
                            "operator": "eq",
                            "value": "1"
                        }                    
                    }
                }
            );
    
        if (locations_result.success && locations_result.data) {
            const $location = $('#location');
            locations_result.data.forEach(loc => {
                $location.append(`<option value="${loc.location}">${loc.location}  -  ${loc.location_name}</option>`);
            });
            $location.val(this.location); // Set default
            /*$location.selectpicker({
                size: 10,  // Shows scrollbar after 10 items
                style: 'btn-sm',
                width: 'fit',
                container: 'body'
            });*/

        }
    }
    async on_vendor_change(vendor) {
        if (!vendor) return;

        // Update header
        this.po_data.header.vendor_code = vendor.code;
        this.po_data.header.vendor_name = vendor.name;

        // Update billing address
        this.po_data.header.billing = {
            name: vendor.name,
            address1: vendor.add1 || '',
            address2: vendor.add2 || '',
            city: vendor.city || '',
            state: vendor.state || '',
            zip: vendor.zip_ || '',
            country: vendor.country || 'USA'
        };

        // Update form
        $('#billing_name').val(vendor.name);
        $('#billing_address1').val(vendor.add1 || '');
        $('#billing_address2').val(vendor.add2 || '');
        $('#billing_city').val(vendor.city || '');
        $('#billing_state').val(vendor.state || '');
        $('#billing_zip').val(vendor.zip_ || '');
        $('#billing_country').val(vendor.country || 'USA');

        // Update terms if vendor has specific terms
        if (vendor.terms_num) {
            $('#terms').val(vendor.terms_num);
            this.po_data.header.terms = vendor.terms_num;
        }
        this.po_data.vendor=vendor
        this.display_vendor_comments();
    }


    display_vendor_comments() {
        const comments1 = this.po_data.vendor.comments1;
        const comments2 = this.po_data.vendor.comments2;
        
        if (comments1 || comments2) {
            let content = '';
            if (comments1) {
                content += `<p class="mb-2">${comments1}</p>`;
            }
            if (comments2) {
                content += `<p class="mb-0">${comments2}</p>`;
            }
            
            $('#vendor_comments_content').html(content);
            $('#vendor_comments_alert').show();
        } else {
            $('#vendor_comments_alert').hide();
        }
    }

    init_part_search() {
        // Initialize autocomplete for part search using jQuery UI
        $('.part-search:not([readonly])').each(function() {
            const $input = $(this);
            
            // Skip if already initialized
            if ($input.hasClass('ui-autocomplete-input')) {
                return;
            }
            
            $input.autocomplete({
                source: async (request, response) => {
                    const result = await window.purchaseOrderBuilder.api_call('list', window.purchaseOrderBuilder.models.parts,
                        {
                            return_columns: ["part", "inventory_description"],
                            order:[{'column':0,'dir':'asc'}],
                            columns:[{'name':'part'},{'name':'inventory_description'}],
                            "filters": {
                                "part": {
                                    "operator": "ilike",
                                    "value": request.term
                                }
                            }
                        }
                    );
                    
                    if (result.success && result.data) {
                        response(result.data.slice(0, 20).map(part => ({
                            label: `${part.part} - ${part.inventory_description}`,
                            value: part.part,
                            part: part
                        })));
                    } else {
                        response([]);
                    }
                },
                select: async (event, ui) => {
                    const index = $(event.target).data('index');
                    const part = ui.item.part;
                    
                    // Update line with part info
                    window.purchaseOrderBuilder.update_line(index, 'part', part.part);
                    window.purchaseOrderBuilder.update_line(index, 'description', part.inventory_description);
                    
                    // Update display
                    $(`.po-line[data-index="${index}"] input[data-field="description"]`).val(part.inventory_description);
                    
                    // Fetch the cost for this part
                    const cost_result = await window.purchaseOrderBuilder.api_call('list', window.purchaseOrderBuilder.models.icmstr, {
                        return_columns: ["code", "lstc"],
                        order:[{'column':0,'dir':'asc'}],
                        columns:[{'name':'code'},{'name':'lstc'}],
                        start: 0,
                        length:1,
                        "filters": {
                            "code": {
                                "operator": "eq",
                                "value": part.part
                            }
                        }
                    });
                    
                    if (cost_result.success && cost_result.data && cost_result.data.length > 0) {
                        const cost = cost_result.data[0].lstc || 0;
                        window.purchaseOrderBuilder.update_line(index, 'price', cost);
                        $(`.po-line[data-index="${index}"] input[data-field="price"]`).val(cost);
                    }
                    
                    // Recalculate
                    window.purchaseOrderBuilder.calculate_totals();
                    
                    return true;
                },
                minLength: 2
            });
        });
    }

    async load_existing_po() {
        const result = await this.api_call('get', window.purchaseOrderBuilder.models.purchase_order, {
            po_number: this.po_number
        });

        if (result.success) {
            // Clean binary data from the response
            this.po_data = this.clean_po_data(result);
            
            // Populate form
            this.populate_form_from_data();
            
            // Render lines
            this.render_lines();
            
            // Update UI state based on PO status
            this.update_ui_state();
        } else {
            this.show_error('Failed to load purchase order');
        }
    }

    update_printed_badge() {
        const is_printed = this.po_data.header.printed === true || this.po_data.header.printed === 'Y';
        if (is_printed) {
            $('#printed_badge').show();
        } else {
            $('#printed_badge').hide();
        }
    }

    async save_po() {
        if (!this.validate_po()) return;

        this.show_loading(true);

        // Update from form one more time
        this.update_header_from_form();

        const save_data = {
            header: this.po_data.header,
            lines: this.po_data.lines,
            deleted_line_ids: this.deleted_line_ids
        };

        // Only add po_number if in edit mode
        if (this.is_edit_mode) {
            save_data.po_number = this.po_number;
        }

        // Determine operation based on mode
        const operation = this.is_edit_mode ? 'update' : 'create';

        const result = await this.api_call(operation, window.purchaseOrderBuilder.models.purchase_order, {
            data: save_data
        });

        if (result.success) {
            this.show_success('Purchase order saved successfully!');
            
            // If creating new, switch to edit mode
            if (!this.is_edit_mode && result.data.po_number) {
                this.po_number = result.data.po_number;
                this.is_edit_mode = true;
                window.history.replaceState({}, '', `/purchase_orders/edit/${this.po_number}`);
                $('#po_number_display').text('#' + this.po_number);
                
                // Show receive button immediately
                $('#receive_po_btn').show();
            }

            // Clear deleted lines tracker
            this.deleted_line_ids = [];

            // Update UI state
            this.update_ui_state();

            // Reload to get updated data
            await this.load_existing_po();
        } else {
            this.show_error(result.message || 'Failed to save purchase order');
        }
        
        this.show_loading(false);
    }
    async process_receive() {
        const receive_lines = [];

        // Collect selected lines
        $('.receive-line-check:checked').each(function() {
            const index = parseInt($(this).data('index'));
            receive_lines.push(index);
        });

        if (receive_lines.length === 0) {
            this.show_error('Please select at least one line to receive');
            return;
        }

        this.show_loading(true);

        const result = await this.api_call('update', window.purchaseOrderBuilder.models.purchase_order, {
            po_number: this.po_number,
            action: 'receive_lines',
            line_indices: receive_lines
        });

        if (result.success) {
            this.show_success(`Successfully received ${receive_lines.length} line(s)`);
            
            // Close modal
            $('#receiveModal').modal('hide');
            
            // Reload PO to get updated data
            await this.load_existing_po();
        } else {
            this.show_error(result.message || 'Failed to process receipt');
        }
        
        this.show_loading(false);
    }

    // Keep all other methods the same (get_default_header, clean_po_data, etc.)
    get_default_header() {
        const today = new Date().toISOString().split('T')[0];
        
        return {
            vendor_code: '',
            vendor_name: '',
            order_date: today,
            expected_receipt_date: today,
            location: this.location,
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

    clean_po_data(data) {
        // Clean binary data from message fields and other fields
        if (data.lines) {
            data.lines = data.lines.map(line => {
                if (line.msg) {
                    // Extract readable part before null bytes
                    const clean_msg = line.msg.split('\x00')[0].trim();
                    line.msg = clean_msg;
                }
                // Clean other binary fields
                ['gla', 'gldpta', 'tskcod', 'cat'].forEach(field => {
                    if (line[field] && typeof line[field] === 'string') {
                        line[field] = line[field].replace(/\x00/g, '').trim();
                    }
                });
                return line;
            });
        }
        
        // Map the data structure to our expected format
        return {
            header: this.map_header_data(data.header || {}),
            lines: data.lines || [],
            source_info: data.source_info || this.po_data.source_info
        };
    }

    map_header_data(header) {
        return {
            vendor_code: header.vndcod || header.vendor_code || '',
            vendor_name: header.vndnme || header.vendor_name || '',
            order_date: this.format_date(header.orddte || header.order_date),
            expected_receipt_date: this.format_date(header.erd || header.expected_receipt_date),
            location: header.loc || header.location || this.location,
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

    format_date(date) {
        if (!date) return '';
        if (typeof date === 'string') return date;
        
        // Handle Python datetime objects
        if (date.year && date.month && date.day) {
            const year = date.year;
            const month = String(date.month).padStart(2, '0');
            const day = String(date.day).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
        
        return '';
    }

    populate_form_from_data() {
        const header = this.po_data.header;
        
        // Basic fields
        $('#vendor_code').val(header.vendor_code);
        $('#order_date').val(header.order_date);
        $('#expected_receipt_date').val(header.expected_receipt_date);
        $('#freight').val(header.freight);
        $('#terms').val(header.terms);
        $('#ship_via').val(header.ship_via);
        $('#location').val(header.location);
        
        // Billing address
        $('#billing_name').val(header.billing.name);
        $('#billing_address1').val(header.billing.address1);
        $('#billing_address2').val(header.billing.address2);
        $('#billing_city').val(header.billing.city);
        $('#billing_state').val(header.billing.state);
        $('#billing_zip').val(header.billing.zip);
        $('#billing_country').val(header.billing.country);
        
        // Shipping address
        $('#shipping_name').val(header.shipping.name);
        $('#shipping_attention').val(header.shipping.attention);
        $('#shipping_address1').val(header.shipping.address1);
        $('#shipping_address2').val(header.shipping.address2);
        $('#shipping_city').val(header.shipping.city);
        $('#shipping_state').val(header.shipping.state);
        $('#shipping_zip').val(header.shipping.zip);
        $('#shipping_country').val(header.shipping.country);
        
        this.display_vendor_comments();
        this.update_printed_badge();
        this.calculate_totals();
        this.update_totals_display();

    }

    render_lines() {
        const container = $('#po_lines_container');
        container.empty();

        if (this.po_data.lines.length === 0) {
            container.html('<div class="text-muted text-center p-4">No lines added. Click "Add Line" to start.</div>');
            return;
        }

        this.po_data.lines.forEach((line, index) => {
            const line_html = this.create_line_html(line, index);
            container.append(line_html);
        });

        // Initialize part search for new lines
        this.init_part_search();
    }

    create_line_html(line, index) {
        const is_received = parseFloat(line.rqty || 0) > 0;
        const is_historical = line._source === 'historical';
        const is_readonly = is_received || is_historical;
        const line_number = index + 1;
        
        // Check if this is a note line
        const is_note_line = line.type === 'N' || (!line.pcode && !line.part && line.msg);
        
        if (is_note_line) {
            // Simple note line - just type and message
            const message = line.msg || line.message || '';
            
            return `
                <div class="po-line card mb-2 ${is_readonly ? 'readonly-line' : ''}" data-index="${index}">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-auto">
                                <span class="line-number">Line ${line_number}</span>
                                ${is_received ? '<span class="received-badge">RECEIVED</span>' : ''}
                            </div>
                            <div class="col-auto">
                                <span class="badge bg-info">NOTE</span>
                            </div>
                            <div class="col">
                                <input type="text" class="form-control form-control-sm" 
                                       data-field="message" data-index="${index}"
                                       value="${message}"
                                       maxlength="30"
                                       placeholder="Note (max 30 characters)"
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                            ${!is_readonly ? `
                                <div class="col-auto">
                                    <button class="btn btn-sm btn-outline-danger remove-line-btn" data-index="${index}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Regular part line
            const part_code = line.pcode || line.part || '';
            const description = line.pdesc || line.description || '';
            const quantity = line.pqty || line.quantity || 0;
            const price = line.pprce || line.price || 0;
            const discount = line.pdisc || line.discount || 0;
            const extended = line.pext || line.extended || 0;
            const erd = this.format_date(line.erd || line.expected_receipt_date);
            
            return `
                <div class="po-line card mb-2 ${is_readonly ? 'readonly-line' : ''}" data-index="${index}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div>
                                <span class="line-number">Line ${line_number}</span>
                                ${is_received ? '<span class="received-badge">RECEIVED</span>' : ''}
                            </div>
                            ${!is_readonly ? `
                                <button class="btn btn-sm btn-outline-danger remove-line-btn" data-index="${index}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                        
                        <div class="row g-2">
                            <div class="col-md-2">
                                <label class="form-label small mb-1">Part #</label>
                                <input type="text" class="form-control form-control-sm part-search" 
                                       data-field="part" data-index="${index}"
                                       value="${part_code}" 
                                       placeholder="Search..."
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label small mb-1">Description</label>
                                <input type="text" class="form-control form-control-sm" 
                                       data-field="description" data-index="${index}"
                                       value="${description}"
                                       placeholder="Part description"
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                            <div class="col-md-1">
                                <label class="form-label small mb-1">Qty</label>
                                <input type="number" class="form-control form-control-sm" 
                                       data-field="quantity" data-index="${index}"
                                       value="${quantity}" min="0" step="1"
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                            <div class="col-md-1">
                                <label class="form-label small mb-1">Price</label>
                                <input type="number" class="form-control form-control-sm" 
                                       data-field="price" data-index="${index}"
                                       value="${price}" min="0" step="0.01"
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                            <div class="col-md-1">
                                <label class="form-label small mb-1">Disc</label>
                                <input type="number" class="form-control form-control-sm" 
                                       data-field="discount" data-index="${index}"
                                       value="${discount}" min="0"
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                            <div class="col-md-1">
                                <label class="form-label small mb-1">Extended</label>
                                <input type="text" class="form-control form-control-sm" 
                                       value="$${extended.toFixed(2)}" 
                                       readonly>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label small mb-1">Expected Date</label>
                                <input type="date" class="form-control form-control-sm" 
                                       data-field="erd" data-index="${index}"
                                       value="${erd}"
                                       ${is_readonly ? 'readonly' : ''}>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    add_line() {
        const new_line = {
            _source: 'active',
            part: '',
            description: '',
            quantity: 1,
            price: 0,
            discount: 0,
            extended: 0,
            received_qty: 0,
            erd: this.po_data.header.expected_receipt_date || new Date().toISOString().split('T')[0],
            type: 'R',
            taxable: false,
            message: ''
        };

        this.po_data.lines.push(new_line);
        this.render_lines();
        this.update_line_counts();
        
        // Focus on the new line's part field
        setTimeout(() => {
            const new_index = this.po_data.lines.length - 1;
            $(`.po-line[data-index="${new_index}"] input[data-field="part"]`).focus();
        }, 100);
    }

    add_note_line() {
        const new_note = {
            _source: 'active',
            type: 'N',  // Note type
            part: '',
            pcode: '',
            description: '',
            pdesc: '',
            quantity: 0,
            pqty: 0,
            price: 0,
            pprce: 0,
            discount: 0,
            pdisc: 0,
            extended: 0,
            pext: 0,
            received_qty: 0,
            rqty: 0,
            erd: this.po_data.header.expected_receipt_date || new Date().toISOString().split('T')[0],
            taxable: false,
            message: '',
            msg: ''
        };

        this.po_data.lines.push(new_note);
        this.render_lines();
        this.update_line_counts();
        
        // Focus on the new note's message field
        setTimeout(() => {
            const new_index = this.po_data.lines.length - 1;
            $(`.po-line[data-index="${new_index}"] input[data-field="message"]`).focus();
        }, 100);
    }

    remove_line(index) {
        const line = this.po_data.lines[index];
        
        // Check if line can be removed
        if (line.rqty > 0) {
            this.show_error('Cannot remove received lines');
            return;
        }

        if (confirm('Remove this line?')) {
            // Track deletion if it has an ID
            if (line.record) {
                this.deleted_line_ids.push(line.record);
            }
            
            // Remove only the specific line at this index
            this.po_data.lines.splice(index, 1);
            
            // Re-render all lines to update indices
            this.render_lines();
            this.calculate_totals();
            this.update_line_counts();
        }
    }

    update_line(index, field, value) {
        const line = this.po_data.lines[index];
        
        // Check if this is a note line
        const is_note_line = line.type === 'N';
        
        // Map fields based on which format we're using
        const field_map = {
            'part': 'pcode',
            'description': 'pdesc',
            'quantity': 'pqty',
            'price': 'pprce',
            'discount': 'pdisc',
            'message': 'msg',
            'erd': 'erd'
        };

        const target_field = field_map[field] || field;
        
        // Update both possible field names
        line[field] = value;
        line[target_field] = value;

        // For note lines, we don't calculate extended prices
        if (!is_note_line) {
            // Calculate extended price if quantity or price changed
            if (field === 'quantity' || field === 'price' || field === 'discount') {
                const qty = parseFloat(line.quantity || line.pqty || 0);
                const price = parseFloat(line.price || line.pprce || 0);
                const discount = parseFloat(line.discount || line.pdisc || 0);
                
                const extended = qty * (price - discount);
                line.extended = extended;
                line.pext = extended;
                
                // Update extended display
                $(`.po-line[data-index="${index}"] input[readonly]`).val(`$${extended.toFixed(2)}`);
                
                // Recalculate totals
                this.calculate_totals();
            }
        }
    }

    calculate_totals() {
        let subtotal = 0;
        
        this.po_data.lines.forEach(line => {
            const extended = parseFloat(line.extended || line.pext || 0);
            subtotal += extended;
        });

        const freight = parseFloat(this.po_data.header.freight || 0);
        const tax_amount = parseFloat(this.po_data.header.tax_amount || 0);
        const total = subtotal + freight + tax_amount;

        this.po_data.header.subtotal = subtotal;
        this.po_data.header.total = total;

        this.update_totals_display();
    }

    update_totals_display() {
        $('#subtotal_display').text(`$${this.po_data.header.subtotal.toFixed(2)}`);
        $('#tax_display').text(`$${this.po_data.header.tax_amount.toFixed(2)}`);
        $('#freight_display').text(`$${this.po_data.header.freight.toFixed(2)}`);
        $('#total_display').text(`$${this.po_data.header.total.toFixed(2)}`);
    }

    update_line_counts() {
        let active_count = 0;
        let historical_count = 0;
        let has_received = false;

        this.po_data.lines.forEach(line => {
            if (line._source === 'historical' || line.rqty > 0) {
                historical_count++;
                has_received = true;
            } else {
                active_count++;
            }
        });

        this.po_data.source_info = {
            active_line_count: active_count,
            has_active_lines: active_count > 0,
            has_historical_lines: historical_count > 0,
            historical_line_count: historical_count,
            is_active: true,
            is_partially_received: has_received
        };
    }

    copy_billing_to_shipping() {
        const billing = this.po_data.header.billing;
        
        this.po_data.header.shipping = {
            name: billing.name,
            attention: $('#shipping_attention').val() || '',
            address1: billing.address1,
            address2: billing.address2,
            city: billing.city,
            state: billing.state,
            zip: billing.zip,
            country: billing.country
        };

        // Update form
        $('#shipping_name').val(billing.name);
        $('#shipping_address1').val(billing.address1);
        $('#shipping_address2').val(billing.address2);
        $('#shipping_city').val(billing.city);
        $('#shipping_state').val(billing.state);
        $('#shipping_zip').val(billing.zip);
        $('#shipping_country').val(billing.country);
    }

    update_header_from_form() {
        this.po_data.header = {
            ...this.po_data.header,
            vendor_code: $('#vendor_code').val(),
            order_date: $('#order_date').val(),
            expected_receipt_date: $('#expected_receipt_date').val(),
            terms: $('#terms').val(),
            ship_via: $('#ship_via').val(),
            location: $('#location').val(),
            freight: parseFloat($('#freight').val() || 0),
            billing: {
                name: $('#billing_name').val(),
                address1: $('#billing_address1').val(),
                address2: $('#billing_address2').val(),
                city: $('#billing_city').val(),
                state: $('#billing_state').val(),
                zip: $('#billing_zip').val(),
                country: $('#billing_country').val()
            },
            shipping: {
                name: $('#shipping_name').val(),
                attention: $('#shipping_attention').val(),
                address1: $('#shipping_address1').val(),
                address2: $('#shipping_address2').val(),
                city: $('#shipping_city').val(),
                state: $('#shipping_state').val(),
                zip: $('#shipping_zip').val(),
                country: $('#shipping_country').val()
            }
        };
    }

    validate_po() {
        const errors = [];

        if (!this.po_data.header.vendor_code) {
            errors.push('Please select a vendor');
        }

        if (!this.po_data.header.order_date) {
            errors.push('Order date is required');
        }

        if (!this.po_data.header.expected_receipt_date) {
            errors.push('Expected receipt date is required');
        }

        if (this.po_data.lines.length === 0) {
            errors.push('At least one line item is required');
        }

        // Check line items
        let has_valid_line = false;
        this.po_data.lines.forEach((line, index) => {
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
            this.show_error('Please fix the following errors:\n' + errors.join('\n'));
            return false;
        }

        return true;
    }

    update_ui_state() {
        const is_partially_received = this.po_data.source_info.is_partially_received;
        
        // Show/hide receive button
        if (this.is_edit_mode) {
            $('#receive_po_btn').show();
        } else {
            $('#receive_po_btn').hide();
        }

        // Disable header fields if any line is received
        if (is_partially_received) {
            $('#vendor_code, #order_date, #terms, #ship_via').prop('disabled', true);
            $('.billing-field').prop('readonly', true);
        } else {
            $('#vendor_code, #order_date, #terms, #ship_via').prop('disabled', false);
            $('.billing-field').prop('readonly', false);
        }

        // Update save button text
        $('#save_button_text').text(this.is_edit_mode ? 'Update PO' : 'Create PO');

        // Update page title
        if (this.is_edit_mode) {
            document.title = `Edit PO #${this.po_number}`;
        } else {
            document.title = 'Create Purchase Order';
        }
    }

    show_receive_modal() {
        // Get non-received lines
        const receivable_lines = [];
        this.po_data.lines.forEach((line, index) => {
            const received = parseFloat(line.rqty || line.received_qty || 0);
            if (received === 0) {
                receivable_lines.push({ line, index });
            }
        });

        if (receivable_lines.length === 0) {
            this.show_info('All lines have been received');
            return;
        }

        let receive_html = `
            <div class="modal fade" id="receiveModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Receive Purchase Order Lines</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted">Select which lines to receive. Each selected line will be fully received.</p>
                            <div class="table-responsive">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th width="50">
                                                <input type="checkbox" id="select_all_receive" class="form-check-input">
                                            </th>
                                            <th>Line</th>
                                            <th>Part</th>
                                            <th>Description</th>
                                            <th>Quantity</th>
                                        </tr>
                                    </thead>
                                    <tbody>
        `;

        receivable_lines.forEach(({ line, index }) => {
            const part = line.pcode || line.part;
            const desc = line.pdesc || line.description;
            const quantity = line.pqty || line.quantity || 0;
            const line_number = index + 1;

            receive_html += `
                <tr>
                    <td>
                        <input type="checkbox" class="form-check-input receive-line-check" 
                               data-index="${index}" value="${index}">
                    </td>
                    <td>${line_number}</td>
                    <td>${part}</td>
                    <td>${desc}</td>
                    <td>${quantity}</td>
                </tr>
            `;
        });

        receive_html += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="process_receive_btn">
                                <i class="fas fa-check"></i> Receive Selected Lines
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        $('#receiveModal').remove();
        $('body').append(receive_html);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('receiveModal'));
        modal.show();

        // Setup event handlers
        $('#select_all_receive').on('change', function() {
            $('.receive-line-check').prop('checked', $(this).is(':checked'));
        });

        $('#process_receive_btn').on('click', () => {
            this.process_receive();
            modal.hide();
        });
    }

    // Utility methods
    show_loading(show) {
        if (show) {
            $('#loadingOverlay').addClass('show');
        } else {
            $('#loadingOverlay').removeClass('show');
        }
    }

    show_error(message) {
        if (window.showToast) {
            window.showToast(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    }

    show_success(message) {
        if (window.showToast) {
            window.showToast(message, 'success');
        } else {
            console.log('Success: ' + message);
            alert('Success: ' + message);
        }
    }

    show_info(message) {
        if (window.showToast) {
            window.showToast(message, 'info');
        } else {
            alert('Info: ' + message);
        }
    }

    // Add after show_info() method:

apply_pre_population() {
    const data = this.pre_populate_data;
    
    // Apply location if provided
    if (data.location) {
        $('#location').val(data.location);
        this.po_data.header.location = data.location;
    }
    
    // Apply ship_via if provided
    if (data.ship_via) {
        $('#ship_via').val(data.ship_via);
        this.po_data.header.ship_via = data.ship_via;
    }
    
    // Apply shipping address if provided
    if (data.shipping_address) {
        const addr = data.shipping_address;
        $('#shipping_name').val(addr.name || '');
        $('#shipping_attention').val(addr.attention || '');
        $('#shipping_address1').val(addr.address1 || '');
        $('#shipping_address2').val(addr.address2 || '');
        $('#shipping_city').val(addr.city || '');
        $('#shipping_state').val(addr.state || '');
        $('#shipping_zip').val(addr.zip || '');
        $('#shipping_country').val(addr.country || 'USA');
        
        // Update header
        this.po_data.header.shipping = {
            name: addr.name || '',
            attention: addr.attention || '',
            address1: addr.address1 || '',
            address2: addr.address2 || '',
            city: addr.city || '',
            state: addr.state || '',
            zip: addr.zip || '',
            country: addr.country || 'USA'
        };
    }
    
    // Add initial items if provided
    if (data.initial_items && data.initial_items.length > 0) {
        data.initial_items.forEach(item => {
            if (item.type === 'part' && item.part) {
                const new_line = {
                    _source: 'active',
                    part: item.part,
                    pcode: item.part,
                    description: item.description,
                    pdesc: item.description,
                    quantity: item.qty || 1,
                    pqty: item.qty || 1,
                    pprce: item.price,
                    discount: 0,
                    pdisc: 0,
                    extended: item.price*item.qty,
                    pext: item.price*item.qty,
                    received_qty: 0,
                    rqty: 0,
                    erd: this.po_data.header.expected_receipt_date || new Date().toISOString().split('T')[0],
                    type: 'R',
                    taxable: false,
                    message: '',
                    msg: ''
                };
                this.po_data.lines.push(new_line);
                
            } else if (item.type === 'note' && item.message) {
                const new_note = {
                    _source: 'active',
                    type: 'N',
                    part: '',
                    pcode: '',
                    description: '',
                    pdesc: '',
                    quantity: 0,
                    pqty: 0,
                    price: 0,
                    pprce: 0,
                    discount: 0,
                    pdisc: 0,
                    extended: 0,
                    pext: 0,
                    received_qty: 0,
                    rqty: 0,
                    erd: this.po_data.header.expected_receipt_date || new Date().toISOString().split('T')[0],
                    taxable: false,
                    message: item.message,
                    msg: item.message
                };
                this.po_data.lines.push(new_note);
            }
        });
        
        // Render the pre-populated lines
        this.render_lines();
        this.update_line_counts();
    }
}
}

// Event delegation for dynamic elements
$(document).on('input change', '.po-line input:not([readonly])', function() {
    const field = $(this).data('field');
    const index = $(this).data('index');
    const value = $(this).val();
    
    if (window.purchaseOrderBuilder) {
        window.purchaseOrderBuilder.update_line(index, field, value);
    }
});

$(document).on('click', '.remove-line-btn', function() {
    const index = $(this).data('index');
    if (window.purchaseOrderBuilder) {
        window.purchaseOrderBuilder.remove_line(index);
    }
});