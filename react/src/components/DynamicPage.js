// react/src/components/DynamicPage.js
import React, { useState, useEffect, Suspense } from 'react';
import { useSite } from '../contexts/SiteContext';
import { useNavigation } from '../App';
import config from '../config';
import LoadingScreen from './LoadingScreen';
import HtmlRenderer from './HtmlRenderer';

// Cache for loaded components
const component_cache = {};

// Ensure Components namespace exists
window.Components = window.Components || {};

const DynamicPage = () => {
    const { current_view, view_params } = useNavigation();
    const { get_current_context, current_context } = useSite();
    const [page_data, set_page_data] = useState(null);
    const [loading, set_loading] = useState(true);
    const [error, set_error] = useState(null);
    const [dynamic_component, set_dynamic_component] = useState(null);

    useEffect(() => {
        load_page();
    }, [current_view, current_context]);

    const load_page = async () => {
        set_loading(true);
        set_error(null);
        set_dynamic_component(null);

        try {
            // Ask backend what component/template to load for this view
            const response = await config.apiCall(config.getUrl(config.api.endpoints.routes.resolve), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({
                    path: `/${current_view}`,
                    params: view_params,
                    context: get_current_context()
                })
            });

            if (!response.ok) {
                if (response.status === 404) {
                    console.log('View not found:', current_view);
                    set_error('Page not found');
                    set_loading(false);
                    return;
                }
                throw new Error('Failed to load page');
            }

            const data = await response.json();
            set_page_data(data);

            // If it's a component route, load the component bundle
            if (data.component_name && data.bundle_url) {
                await load_component_bundle(data.component_name, data.bundle_url, data.component_version);
            }
        } catch (err) {
            set_error(err.message || 'Failed to load page');
        } finally {
            set_loading(false);
        }
    };

    const wait_for_component = (component_name, timeout = 5000) => {
        return new Promise((resolve, reject) => {
            const start_time = Date.now();
            
            // Check if component is already available
            if (window.Components[component_name]) {
                resolve(window.Components[component_name]);
                return;
            }
            
            // Listen for component registration event
            const handle_registration = (event) => {
                if (event.detail.name === component_name) {
                    window.removeEventListener('component_registered', handle_registration);
                    resolve(event.detail.component);
                }
            };
            
            window.addEventListener('component_registered', handle_registration);
            
            // Also poll for component availability
            const check_interval = setInterval(() => {
                // Check multiple possible locations
                const component = window.Components[component_name] || 
                                window[component_name] ||
                                window.Components[`components/${component_name}`];
                
                if (component) {
                    clearInterval(check_interval);
                    window.removeEventListener('component_registered', handle_registration);
                    
                    // Ensure it's registered in the standard location
                    if (!window.Components[component_name]) {
                        window.Components[component_name] = component;
                    }
                    
                    resolve(component);
                } else if (Date.now() - start_time > timeout) {
                    clearInterval(check_interval);
                    window.removeEventListener('component_registered', handle_registration);
                    reject(new Error(`Component ${component_name} not found after ${timeout}ms`));
                }
            }, 50);
        });
    };

    const load_component_bundle = async (component_name, bundle_url, version) => {
        const cache_key = `${component_name}_${version || 'latest'}`;

        // Check cache first
        if (component_cache[cache_key]) {
            set_dynamic_component(() => component_cache[cache_key]);
            return;
        }

        try {
            // Ensure React is available globally
            if (!window.React) {
                window.React = React;
                console.warn('React was not available globally, setting it now');
            }

            console.log(`Loading component bundle: ${component_name} from ${bundle_url}`);

            // Load the script
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = bundle_url;
                script.async = true;

                script.onload = () => {
                    console.log(`Script loaded for ${component_name}`);
                    resolve();
                };

                script.onerror = (e) => {
                    console.error(`Failed to load script: ${bundle_url}`, e);
                    reject(new Error(`Failed to load script: ${bundle_url}`));
                };

                document.head.appendChild(script);
            });

            // Wait for component to be registered
            console.log(`Waiting for component ${component_name} to be registered...`);
            const loaded_component = await wait_for_component(component_name);
            
            console.log(`Component ${component_name} loaded successfully`);
            
            // Cache it
            component_cache[cache_key] = loaded_component;
            set_dynamic_component(() => loaded_component);
            
        } catch (err) {
            console.error(`Failed to load component ${component_name}:`, err);
            set_error(`Failed to load component: ${component_name} - ${err.message}`);
        }
    };

    // Show loading inside the layout
    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    // Show error
    if (error) {
        return (
            <div className="container mt-4">
                <div className="alert alert-danger">
                    <h4 className="alert-heading">Error</h4>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    // Render dynamic component
    if (dynamic_component && page_data) {
        // Create component element with proper casing
        const DynamicComponentElement = dynamic_component;
        
        // Merge route params with configured props
        const component_props = {
            ...page_data.props,
            route_params: view_params,
            route_config: page_data.config || {},
            meta: {
                title: page_data.title,
                description: page_data.description
            }
        };

        return (
            <Suspense fallback={
                <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                </div>
            }>
                <DynamicComponentElement {...component_props} />
            </Suspense>
        );
    }

    // Render HTML template
    if (page_data?.html) {
        return <HtmlRenderer html={page_data.html} config={page_data.config} />;
    }

    // Default: show warning
    return <div className="alert alert-warning m-3">Unknown page type</div>;
};

export default DynamicPage;