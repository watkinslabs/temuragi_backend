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

    // Separate state for different parts of site config
    const [site_info, setSiteInfo] = useState(null); // Name, logo, footer - doesn't change
    const [menu_items, setMenuItems] = useState([]); // Menu - changes per context

    // Track what we're currently fetching to prevent duplicate requests
    const fetching_context = useRef(null);
    const has_initial_fetch = useRef(false);

    // Initialize default context from login
    const initialize_context = (default_context) => {
        console.log('SiteContext: Initializing context:', default_context);
        if (default_context) {
            setCurrentContext(default_context);
            sessionStorage.setItem('current_context', default_context);
        }
    };

    // Get the current context, with fallback to default
    const get_current_context = () => {
        const context = current_context || sessionStorage.getItem('current_context') || localStorage.getItem('default_context') || 'default';
        console.log('SiteContext: Getting current context:', context);
        return context;
    };

    const fetch_site_config = useCallback(async (path = '/') => {
        const context = get_current_context();
        console.log('SiteContext: Fetching config for context:', context, 'path:', path);

        // Don't fetch if we're already fetching the same context
        if (fetching_context.current === context && has_initial_fetch.current) {
            console.log('SiteContext: Already fetching this context, skipping');
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

            console.log('SiteContext: Making API call with body:', request_body);

            const response = await config.apiCall(config.getUrl('/site/config'), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify(request_body)
            });

            if (response.ok) {
                const data = await response.json();
                console.log('SiteContext: Received site config:', data);

                // Always set site info
                setSiteInfo({
                    name: data.site.name,
                    logo_desktop: data.site.logo_desktop,
                    logo_desktop_dark: data.site.logo_desktop_dark,
                    footer_text: data.site.footer_text,
                    tagline: data.site.tagline,
                    maintenance_mode: data.site.maintenance_mode
                });

                // Always update menu items (they change per context)
                console.log('SiteContext: Setting menu items:', data.menu?.items);
                setMenuItems(data.menu?.items || []);

                if (data.contexts) {
                    console.log('SiteContext: Setting available contexts:', data.contexts);
                    setAvailableContexts(data.contexts);
                }

                // Update current context if server says it's different
                if (data.current_context && data.current_context !== context) {
                    console.log('SiteContext: Server returned different context:', data.current_context);
                    setCurrentContext(data.current_context);
                    sessionStorage.setItem('current_context', data.current_context);
                }

                has_initial_fetch.current = true;
            } else {
                console.error('SiteContext: Failed to fetch site config:', response.status);
            }
        } catch (error) {
            console.error('SiteContext: Site config fetch error:', error);
        } finally {
            setContextLoading(false);
            fetching_context.current = null;
        }
    }, [current_context]);

    // Context switch - fetch new menu items
    const switch_context = async (context_name) => {
        console.log('SiteContext: Switching context from', current_context, 'to', context_name);

        // Don't switch if it's the same context
        if (context_name === current_context) {
            console.log('SiteContext: Same context, not switching');
            return;
        }

        // Update the context immediately
        setCurrentContext(context_name);
        sessionStorage.setItem('current_context', context_name);

        // Clear main content by navigating to home
        if (window.navigate_to) {
            window.navigate_to('home');
        }

        // Fetch new menu items for this context
        setContextLoading(true);

        try {
            const request_body = {
                path: '/',
                context: context_name,
                include_contexts: false // Don't need contexts again
            };

            console.log('SiteContext: Fetching menu for new context:', request_body);

            const response = await config.apiCall(config.getUrl('/site/config'), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify(request_body)
            });

            if (response.ok) {
                const data = await response.json();
                console.log('SiteContext: Received menu items for new context:', data.menu?.items);

                // Update menu items
                setMenuItems(data.menu?.items || []);

                // If server returned different context, update it
                if (data.current_context && data.current_context !== context_name) {
                    console.log('SiteContext: Server corrected context to:', data.current_context);
                    setCurrentContext(data.current_context);
                    sessionStorage.setItem('current_context', data.current_context);
                }
            }
        } catch (error) {
            console.error('SiteContext: Context switch error:', error);
        } finally {
            setContextLoading(false);
        }
    };

    // Clear context data on logout
    const clear_context = () => {
        console.log('SiteContext: Clearing all context data');
        setCurrentContext(null);
        setAvailableContexts([]);
        setSiteInfo(null);
        setMenuItems([]);
        sessionStorage.removeItem('current_context');
        has_initial_fetch.current = false;
    };

    // Debug log state changes
    useEffect(() => {
        console.log('SiteContext state updated:', {
            current_context,
            available_contexts: available_contexts.length,
            menu_items: menu_items.length,
            site_info: !!site_info
        });
    }, [current_context, available_contexts, menu_items, site_info]);

    // Provide combined site_config for backward compatibility
    const site_config = site_info ? {
        ...site_info,
        menu_items,
        contexts: available_contexts,
        current_context
    } : null;

    return (
        <SiteContext.Provider value={{
            current_context,
            available_contexts,
            context_loading,
            site_config,
            site_info,
            menu_items,
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