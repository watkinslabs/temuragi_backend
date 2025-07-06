// react/component-wrapper.js
// Custom webpack loader to wrap components
module.exports = function(source) {
    const component_name = this.resourcePath.split('/').pop().replace('.js', '');
    
    // Only wrap component files, not the main app files
    if (this.resourcePath.includes('/components/') && 
        this.resourcePath.includes('/user_components/') && 
        !this.resourcePath.includes('DynamicPage') &&
        !this.resourcePath.includes('LoadingScreen') &&
        !this.resourcePath.includes('Login') &&
        !this.resourcePath.includes('HtmlRenderer')) {
        
        return `
${source}

// Auto-generated wrapper for component registration
if (typeof window !== 'undefined') {
    window.${component_name} = exports.default || exports;
}
`;
    }
    
    return source;
};