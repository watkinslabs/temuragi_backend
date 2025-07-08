import React from 'react';
import ReactDOM from 'react-dom/client';
import App, { NavigationContext, useNavigation } from './App';
import { SiteContext, useSite } from './contexts/SiteContext';
import config from './config';
import register_default_components from './component_registry';

window.React = React;
window.ReactDOM = ReactDOM;

// Make contexts and hooks available for dynamic components
window.NavigationContext = NavigationContext;
window.useNavigation = useNavigation;
window.SiteContext = SiteContext;
window.useSite = useSite;
window.config = config;

// Ensure they're available on the global object too
if (typeof global !== 'undefined') {
    global.React = React;
    global.ReactDOM = ReactDOM;
}

// Initialize Components namespace
window.Components = window.Components || {};

// Register all default components
register_default_components();

// Debug helper
window.list_components = () => {
    console.log('Available components:', Object.keys(window.Components));
    return window.Components;
};

// Wait for any existing app initialization if needed
const init_react = () => {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init_react);
} else {
    init_react();
}