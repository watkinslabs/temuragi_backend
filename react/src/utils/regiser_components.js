// react/src/utils/register_component.js
// Helper to register components globally for dynamic loading

window.Components = window.Components || {};

export const register_component = (name, component) => {
    if (!component) {
        console.error(`Cannot register component ${name}: component is undefined`);
        return;
    }
    
    console.log(`Registering component: ${name}`);
    window.Components[name] = component;
    
    // Also register on the global scope for UMD compatibility
    if (typeof window[name] === 'undefined') {
        window[name] = component;
    }
    
    // Emit custom event to notify that component is ready
    window.dispatchEvent(new CustomEvent('component_registered', { 
        detail: { name, component } 
    }));
};

// Helper to wrap component exports
export const create_component_export = (name, component) => {
    // Register immediately
    register_component(name, component);
    
    // Return the component for module systems
    return component;
};