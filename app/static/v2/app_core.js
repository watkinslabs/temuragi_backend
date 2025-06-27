// app_core.js - This creates the window.app namespace
window.app = {
    managers: {},
    config: {},
    
    // Method for classes to register themselves
    register: function(name, instance) {
        this.managers[name] = instance;
        // Also expose directly on app for convenience
        this[name] = instance;
        console.log(`Registered ${name} to window.app`);
        return instance;
    },
    
    // Get manager by name
    get: function(name) {
        return this.managers[name] || this[name];
    },
    
    // Check if a manager exists
    has: function(name) {
        return !!(this.managers[name] || this[name]);
    }
};