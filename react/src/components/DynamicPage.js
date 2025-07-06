import React, { useState, useEffect, Suspense } from 'react';
import { useSite } from '../contexts/SiteContext';
import { useNavigation } from '../App';
import config from '../config';
import LoadingScreen from './LoadingScreen';
import HtmlRenderer from './HtmlRenderer';

// Cache for loaded components
const component_cache = {};

const DynamicPage = () => {
    const { current_view, view_params } = useNavigation();
    const { get_current_context, current_context } = useSite();
    const [page_data, setPageData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [DynamicComponent, setDynamicComponent] = useState(null);

    useEffect(() => {
        loadPage();
    }, [current_view, current_context]);

    const loadPage = async () => {
        setLoading(true);
        setError(null);
        setDynamicComponent(null);

        try {
            // Ask backend what component/template to load for this view
            const response = await config.apiCall(config.getUrl(config.api.endpoints.routes.resolve), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({
                    path: `/${current_view}`, // Convert view to path format
                    params: view_params,
                    context: get_current_context()
                })
            });

            if (!response.ok) {
                // If 404 or route cannot be resolved
                if (response.status === 404) {
                    console.log('View not found:', current_view);
                    setError('Page not found');
                    setLoading(false);
                    return;
                }
                throw new Error('Failed to load page');
            }

            const data = await response.json();
            setPageData(data);

            // If it's a component route, load the component bundle
            if (data.component_name && data.bundle_url) {
                await loadComponentBundle(data.component_name, data.bundle_url, data.component_version);
            }
        } catch (err) {
            setError(err.message || 'Failed to load page');
        } finally {
            setLoading(false);
        }
    };

    const loadComponentBundle = async (component_name, bundle_url, version) => {
        const cache_key = `${component_name}_${version || 'latest'}`;

        // Check cache first
        if (component_cache[cache_key]) {
            setDynamicComponent(() => component_cache[cache_key]);
            return;
        }

        try {
            // Load the component bundle
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = bundle_url;
                script.async = true;

                // The bundle should attach the component to window.Components
                script.onload = () => {
                    const loaded_component = window.Components?.[component_name];

                    if (loaded_component) {
                        // Cache it
                        component_cache[cache_key] = loaded_component;
                        resolve();
                    } else {
                        reject(new Error(`Component ${component_name} not found after loading`));
                    }
                };

                script.onerror = () => {
                    reject(new Error(`Failed to load component bundle: ${bundle_url}`));
                };

                document.head.appendChild(script);
            });

            setDynamicComponent(() => component_cache[cache_key]);
        } catch (err) {
            console.error(`Failed to load component ${component_name}:`, err);
            setError(`Failed to load component: ${component_name}`);
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
    if (DynamicComponent && page_data) {
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
                <DynamicComponent {...component_props} />
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