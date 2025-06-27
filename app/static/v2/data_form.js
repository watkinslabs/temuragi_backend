// data_form.js
class DataForm {
    constructor(form_id, options = {}) {
        this.form_element = document.getElementById(form_id);
        if (!this.form_element) {
            throw new Error(`Form with id ${form_id} not found`);
        }
        
        this.model_name = this.form_element.dataset.model;
        this.prefix = this.form_element.dataset.prefix || '';
        this.api_url = window.app.config.api_url;
        this.redirect_url = options.redirect_url;
        this.options = {
            show_success_toast: true,
            show_error_toast: true,
            validate_on_blur: true,
            load_fk_on_init: true,
            ...options
        };
        
        // Track loading states
        this.loading_states = {
            form: false,
            fk_selects: new Set(),
            initial_data: false
        };
        
        this.init();
        
        // Self-register if window.app exists
        if (window.app && window.app.register) {
            window.app.register(`form_${form_id}`, this);
        }
    }
    
    async init() {
        // Prevent default form submission
        this.form_element.addEventListener('submit', (e) => this.handle_submit(e));
        
        // Check if we have an ID for edit mode
        const id_field = this.form_element.querySelector(`#${this.prefix}id`);
        const id = id_field ? id_field.value : null;
        
        // Load FK options first if enabled
        if (this.options.load_fk_on_init) {
            await this.load_all_fk_options();
        }
        
        // Then load form data if we have an ID
        if (id) {
            await this.get_data(id);
        }
        
        // Setup field validation if enabled
        if (this.options.validate_on_blur) {
            this.setup_field_validation();
        }
        
        // Setup any field watchers
        this.setup_field_watchers();
    }
    
    async get_data(id) {
        if (this.loading_states.initial_data) {
            return; // Already loading
        }
        
        this.loading_states.initial_data = true;
        
        try {
            // Show loading state
            this.set_loading_state(true);
            
            const payload = {
                model: this.model_name,
                operation: 'read',
                id: id
            };
            
            const result = await window.app.api.post(this.api_url, payload);
            
            if (result.success && result.data) {
                // Populate form with data
                this.set_values(result.data);
                
                // Trigger custom data loaded event
                this.form_element.dispatchEvent(new CustomEvent('form:data_loaded', {
                    detail: { data: result.data }
                }));
            } else {
                const error_message = result.error || 'Failed to load data';
                this.handle_error(error_message);
                
                // Optionally disable form if we can't load data
                console.error(`Failed to load ${this.model_name} with id ${id}:`, error_message);
            }
        } catch (error) {
            const error_message = error.message || 'Network error loading data';
            this.handle_error(error_message);
            console.error(`Failed to load ${this.model_name} with id ${id}:`, error);
        } finally {
            this.loading_states.initial_data = false;
            this.set_loading_state(false);
        }
    }
    
    async handle_submit(e) {
        e.preventDefault();
        
        if (this.loading_states.form) {
            return; // Prevent double submission
        }
        
        // Validate form
        if (!this.validate_form()) {
            return;
        }
        
        // Get form data
        const form_data = this.get_form_data();
        
        // Determine operation
        const id_field = this.form_element.querySelector(`#${this.prefix}id`);
        const id = id_field ? id_field.value : null;
        const operation = id ? 'update' : 'create';
        
        // Build payload
        const payload = {
            model: this.model_name,
            operation: operation,
            data: form_data
        };
        
        if (id) {
            payload.id = id;
        }
        
        // Show loading state
        this.set_loading_state(true);
        
        try {
            const result = await window.app.api.post(this.api_url, payload);
            
            if (result.success) {
                this.handle_success(result, operation);
            } else {
                this.handle_error(result.error || 'Failed to save');
            }
        } catch (error) {
            this.handle_error(error.message || 'Network error occurred');
        } finally {
            this.set_loading_state(false);
        }
    }
    
    get_form_data() {
        const form_data = new FormData(this.form_element);
        const data = {};
        
        // Get all form elements
        const elements = this.form_element.elements;
        
        for (let element of elements) {
            if (!element.name) continue;
            
            const key = element.name;
            
            // Handle different input types
            if (element.type === 'checkbox') {
                data[key] = element.checked;
            } else if (element.type === 'number') {
                data[key] = element.value ? parseFloat(element.value) : null;
            } else if (element.type === 'select-multiple') {
                data[key] = Array.from(element.selectedOptions).map(opt => opt.value);
            } else {
                data[key] = element.value || null;
            }
        }
        
        return data;
    }
    
    async load_all_fk_options() {
        const fk_selects = this.form_element.querySelectorAll('.fk-select');
        
        // Load all FK options in parallel
        const promises = Array.from(fk_selects).map(select => this.load_fk_options(select));
        await Promise.all(promises);
    }
    
    async load_fk_options(select_element) {
        const model = select_element.dataset.model;
        const display_field = select_element.dataset.displayField || 'display_name';
        const select_id = select_element.id;
        
        if (!model) {
            console.warn('FK select missing data-model attribute:', select_element);
            return;
        }
        
        // Track loading state
        this.loading_states.fk_selects.add(select_id);
        
        try {
            // Show loading state
            this.set_select_loading(select_element, true);
            
            const result = await window.app.api.post(this.api_url, {
                model: model,
                operation: 'list',
                length: 1000,  // Get all records
                order: [{ column: display_field, dir: 'asc' }]
            });
            
            if (result.success && result.data) {
                // Clear existing options
                select_element.innerHTML = '';
                
                // Create the placeholder option
                const placeholder_option = document.createElement('option');
                placeholder_option.value = '';
                
                if (result.data.length === 0) {
                    // No options available
                    placeholder_option.textContent = '-- None Available --';
                    placeholder_option.disabled = true;
                    placeholder_option.selected = true;
                    select_element.appendChild(placeholder_option);
                    select_element.disabled = true; // Disable the entire select
                } else {
                    // Options are available
                    placeholder_option.textContent = '-- Select One --';
                    select_element.appendChild(placeholder_option);
                    
                    // Add the actual options
                    result.data.forEach(item => {
                        const option = document.createElement('option');
                        option.value = item.id;
                        
                        // Try display_field, fallback to name, then id
                        option.textContent = item[display_field] || item.name || item.display || item.id;
                        
                        select_element.appendChild(option);
                    });
                    
                    select_element.disabled = false; // Ensure select is enabled
                }
                
                // Restore selected value if any
                const current_value = select_element.getAttribute('data-value') || 
                                    select_element.dataset.currentValue;
                if (current_value && result.data.length > 0) {
                    select_element.value = current_value;
                }
            } else {
                // API call succeeded but no data property - treat as empty
                select_element.innerHTML = '<option value="" disabled selected>-- None Available --</option>';
                select_element.disabled = true;
            }
        } catch (error) {
            console.error(`Failed to load options for ${model}:`, error);
            this.show_notification(`Failed to load ${model} options`, 'error');
            
            // On error, show error state
            select_element.innerHTML = '<option value="" disabled selected>-- Error Loading Options --</option>';
            select_element.disabled = true;
        } finally {
            this.loading_states.fk_selects.delete(select_id);
            this.set_select_loading(select_element, false);
        }
    }
    
    set_select_loading(select_element, is_loading) {
        if (is_loading) {
            // Store current state
            select_element.dataset.was_disabled = select_element.disabled;
            select_element.disabled = true;
            
            const loading_option = document.createElement('option');
            loading_option.textContent = 'Loading...';
            loading_option.disabled = true;
            loading_option.selected = true;
            loading_option.className = 'loading-option';
            select_element.insertBefore(loading_option, select_element.firstChild);
        } else {
            const loading_option = select_element.querySelector('.loading-option');
            if (loading_option) {
                loading_option.remove();
            }
            
            // Only restore disabled state if it wasn't set by load_fk_options
            if (select_element.dataset.was_disabled === 'false' && 
                select_element.options.length > 1) {
                select_element.disabled = false;
            }
            delete select_element.dataset.was_disabled;
        }
    }
    
    validate_form() {
        const is_valid = this.form_element.checkValidity();
        
        if (!is_valid) {
            // Show validation errors
            this.form_element.classList.add('was-validated');
            
            // Focus first invalid field
            const first_invalid = this.form_element.querySelector(':invalid');
            if (first_invalid) {
                first_invalid.focus();
                first_invalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        
        return is_valid;
    }
    
    setup_field_validation() {
        const inputs = this.form_element.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (this.form_element.classList.contains('was-validated')) {
                    this.validate_field(input);
                }
            });
            
            input.addEventListener('input', () => {
                if (this.form_element.classList.contains('was-validated')) {
                    this.validate_field(input);
                }
            });
        });
    }
    
    validate_field(field) {
        const is_valid = field.checkValidity();
        
        if (is_valid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
        
        // Update custom error message if needed
        const error_element = field.nextElementSibling;
        if (error_element && error_element.classList.contains('invalid-feedback')) {
            error_element.textContent = field.validationMessage;
        }
    }
    
    setup_field_watchers() {
        // Override in subclasses to add custom field watchers
        // Example: watch a field and update another based on its value
    }
    
    set_loading_state(is_loading) {
        this.loading_states.form = is_loading;
        
        const submit_btn = this.form_element.querySelector('[type="submit"]');
        if (submit_btn) {
            submit_btn.disabled = is_loading;
            
            if (is_loading) {
                submit_btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
            } else {
                submit_btn.innerHTML = '<i class="fas fa-save"></i> Save';
            }
        }
        
        // Disable all form inputs
        const inputs = this.form_element.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            if (input.type !== 'submit') {
                input.disabled = is_loading;
            }
        });
    }
    
    handle_success(result, operation) {
        if (this.options.show_success_toast) {
            const message = operation === 'create' 
                ? `${this.model_name} created successfully!`
                : `${this.model_name} updated successfully!`;
            this.show_notification(message, 'success');
        }
        
        // Handle redirect
        if (this.redirect_url) {
            setTimeout(() => {
                window.location.href = this.redirect_url;
            }, 1000);
        } else if (result.data && result.data.id && operation === 'create') {
            // Update form to edit mode
            const id_field = this.form_element.querySelector(`#${this.prefix}id`);
            if (id_field) {
                id_field.value = result.data.id;
            }
            
            // Update URL without reload
            if (window.history.pushState) {
                const new_url = window.location.pathname + '?id=' + result.data.id;
                window.history.pushState({ id: result.data.id }, '', new_url);
            }
        }
        
        // Trigger custom success event
        this.form_element.dispatchEvent(new CustomEvent('form:success', {
            detail: { result, operation }
        }));
    }
    
    handle_error(error_message) {
        if (this.options.show_error_toast) {
            this.show_notification(error_message, 'error');
        }
        
        // Trigger custom error event
        this.form_element.dispatchEvent(new CustomEvent('form:error', {
            detail: { error: error_message }
        }));
    }
    
    show_notification(message, type) {
        // Use the toast system if available
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            console[type === 'error' ? 'error' : 'log'](`[${type}] ${message}`);
        }
    }
    
    // Public methods
    
    reset() {
        this.form_element.reset();
        this.form_element.classList.remove('was-validated');
        
        // Clear validation states
        const inputs = this.form_element.querySelectorAll('.is-valid, .is-invalid');
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
    }
    
    set_values(data) {
        Object.entries(data).forEach(([key, value]) => {
            const field = this.form_element.elements[key];
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = !!value;
                } else {
                    field.value = value || '';
                }
            }
        });
    }
    
    async refresh_fk_select(select_id) {
        const select = this.form_element.querySelector(`#${select_id}`);
        if (select && select.classList.contains('fk-select')) {
            await this.load_fk_options(select);
        }
    }
    
    enable_field(field_name) {
        const field = this.form_element.elements[field_name];
        if (field) field.disabled = false;
    }
    
    disable_field(field_name) {
        const field = this.form_element.elements[field_name];
        if (field) field.disabled = true;
    }
}

// Auto-initialize forms with data-auto-init="true"
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form[data-auto-init="true"]').forEach(form => {
        new DataForm(form.id);
    });
});