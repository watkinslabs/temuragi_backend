import React, { useState, useEffect, Suspense } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { useSite } from '../contexts/SiteContext';
import config from '../config';
import LoadingScreen from './LoadingScreen';
import HtmlRenderer from './HtmlRenderer';

// Cache for loaded components
const component_cache = {};

const DynamicPage = () => {
    const location = useLocation();
    const params = useParams();
    const navigate = useNavigate();
    const { get_current_section, current_section } = useSite();
    const [page_data, setPageData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [DynamicComponent, setDynamicComponent] = useState(null);

    useEffect(() => {
        loadPage();
    }, [location.pathname, current_section]);

    const loadPage = async () => {
        setLoading(true);
        setError(null);
        setDynamicComponent(null);

        try {1
            // Ask backend what component/template to load for this route
            const response = await fetch(config.getUrl(config.api.endpoints.routes.resolve), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({
                    path: location.pathname,
                    params: Object.fromEntries(new URLSearchParams(location.search)),
                    section: get_current_section()
                })
            });

            if (!response.ok) {
                // If 404 or route cannot be resolved, redirect to /home
                if (response.status === 404) {
                    console.log('Route not found, redirecting to /home');
                    // Only redirect if we're not already on /home (to avoid infinite loop)
                    if (location.pathname !== '/home') {
                        navigate('/home');
                        return;
                    } else {
                        // If even /home fails, show error
                        setError('Page not found');
                        setLoading(false);
                        return;
                    }
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
                    <hr />
                    <p className="mb-0">
                        <button 
                            className="btn btn-outline-danger btn-sm" 
                            onClick={() => navigate('/')}
                        >
                            Go to Dashboard
                        </button>
                    </p>
                </div>
            </div>
        );
    }

    // Render dynamic component
    if (DynamicComponent && page_data) {
        // Merge route params with configured props
        const component_props = {
            ...page_data.props,
            route_params: params,
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