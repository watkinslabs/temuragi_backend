// react/src/contexts/SiteContext.js
import React, { createContext, useState, useContext, useRef, useCallback, useEffect } from 'react';
import config from '../config';

const SiteContext = createContext(null);

export const useSite = () => {
    const context = useContext(SiteContext);
    if (!context) throw new Error('useSite must be used within SiteProvider');
    return context;
};

export const SiteProvider = ({ children }) => {
    const [current_context, setCurrentContext] = useState(() => {
        // Check session storage for current session's context
        return sessionStorage.getItem('current_context') || null;
    });

    const [available_contexts, setAvailableContexts] = useState([]);
    const [context_loading, setContextLoading] = useState(false);

    // Cache for site configs by context
    const site_config_cache = useRef({});
    const [current_site_config, setCurrentSiteConfig] = useState(() => {
        // Check for initial site config from login
        const initial_config = sessionStorage.getItem('initial_site_config');
        if (initial_config) {
            const config = JSON.parse(initial_config);
            sessionStorage.removeItem('initial_site_config'); // Clean up
            return config;
        }
        return null;
    });

    // Track what we're currently fetching to prevent duplicate requests
    const fetching_context = useRef(null);

    // Initialize cache with initial config if available
    useEffect(() => {
        if (current_site_config && current_context && !site_config_cache.current[current_context]) {
            site_config_cache.current[current_context] = current_site_config;
            if (current_site_config.contexts) {
                setAvailableContexts(current_site_config.contexts);
            }
        }
    }, []); // Empty dependency array - only run once on mount

    // Initialize default context from login
    const initialize_context = (default_context) => {
        console.log('Initializing context:', default_context);
        if (!current_context && default_context) {
            setCurrentContext(default_context);
            sessionStorage.setItem('current_context', default_context);
        }
    };

    // Get the current context, with fallback to default
    const get_current_context = () => {
        return current_context || localStorage.getItem('default_context') || 'default';
    };

    const fetch_site_config = useCallback(async (path = '/') => {
        const context = get_current_context();
    
        // Don't fetch if we're already fetching
        if (fetching_context.current === context) {
            return;
        }
    
        fetching_context.current = context;
        setContextLoading(true);
    
        try {
            const request_body = {
                path: path,
                context: context,
                include_contexts: true
            };
    
            const response = await fetch(config.getUrl('/site/config'), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify(request_body)
            });
    
            if (response.ok) {
                const data = await response.json();
    
                // Create a properly structured site config object
                const site_config_data = {
                    ...data.site,
                    menu_items: data.menu?.items || [],
                    contexts: data.contexts || [],
                    current_context: data.current_context
                };
    
                setCurrentSiteConfig(site_config_data);
    
                if (data.contexts) {
                    setAvailableContexts(data.contexts);
                }
    
                if (data.current_context && data.current_context !== context) {
                    setCurrentContext(data.current_context);
                    sessionStorage.setItem('current_context', data.current_context);
                }
    
                return site_config_data;
            }
        } catch (error) {
            console.error('Site config fetch error:', error);
        } finally {
            setContextLoading(false);
            fetching_context.current = null;
        }
    }, [current_context]);

    // In SiteContext.js, update the switch_context function:
    const switch_context = async (context_name) => {
        console.log('Switching context from', current_context, 'to', context_name);
        
        // Update the context immediately
        setCurrentContext(context_name);
        sessionStorage.setItem('current_context', context_name);
        
        // Clear current config to show loading state
        setCurrentSiteConfig(null);
        
        // Fetch new config
        setContextLoading(true);
    
        try {
            const request_body = {
                path: '/',
                context: context_name,
                include_contexts: true
            };
    
            const response = await fetch(config.getUrl('/site/config'), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify(request_body)
            });
    
            if (response.ok) {
                const data = await response.json();
                
                // Create a properly structured site config object
                const site_config_data = {
                    ...data.site,
                    menu_items: data.menu?.items || [],
                    contexts: data.contexts || [],
                    current_context: data.current_context
                };
    
                // Update everything
                setCurrentSiteConfig(site_config_data);
                
                if (data.contexts) {
                    setAvailableContexts(data.contexts);
                }
    
                // If server returned different context, update it
                if (data.current_context && data.current_context !== context_name) {
                    setCurrentContext(data.current_context);
                    sessionStorage.setItem('current_context', data.current_context);
                }
            }
        } catch (error) {
            console.error('Context switch error:', error);
        } finally {
            setContextLoading(false);
        }
    };
    // Clear context data on logout
    const clear_context = () => {
        setCurrentContext(null);
        setAvailableContexts([]);
        setCurrentSiteConfig(null);
        site_config_cache.current = {};
        sessionStorage.removeItem('current_context');
    };

    return (
        <SiteContext.Provider value={{
            current_context,
            available_contexts,
            context_loading,
            site_config: current_site_config,
            setAvailableContexts,
            setContextLoading,
            initialize_context,
            switch_context,
            clear_context,
            get_current_context,
            fetch_site_config
        }}>
            {children}
        </SiteContext.Provider>
    );
};