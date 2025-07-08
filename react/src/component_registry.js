// react/src/component_registry.js
import React from 'react';

// Import all default components that should be part of the main bundle
// These are the core components from your webpack ignore list
import DynamicPage from './components/DynamicPage';
import LoadingScreen from './components/LoadingScreen';
import Login from './components/Login';
import HtmlRenderer from './components/HtmlRenderer';
import ComponentBuilder from './components/ComponentBuilder';
import DefaultLayout from './components/DefaultLayout';
import ServerDataTable from './components/ServerDataTable';

// Import any other default components you have
// Add more imports here as needed

// Initialize Components namespace
window.Components = window.Components || {};

// Register all default components
const register_default_components = () => {
    // Register core system components
    window.Components.DynamicPage = DynamicPage;
    window.Components.LoadingScreen = LoadingScreen;
    window.Components.Login = Login;
    window.Components.HtmlRenderer = HtmlRenderer;
    window.Components.ComponentBuilder = ComponentBuilder;
    window.Components.DefaultLayout = DefaultLayout;
    window.Components.ServerDataTable = ServerDataTable;
    
    // Register any other default components here
    
    console.log('Default components registered:', Object.keys(window.Components));
};

// Export for use in index.js
export default register_default_components;