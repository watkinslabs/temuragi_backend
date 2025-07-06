import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSite } from '../contexts/SiteContext';
import NineDotMenu from './layout/NineDotMenu';
import Breadcrumbs from './layout/Breadcrumbs';
import SidebarMenu from './layout/SidebarMenu';

const DefaultLayout = ({ children }) => {
    const location = useLocation();
    const { user, logout } = useAuth();
    const {
        current_context,
        available_contexts,
        context_loading,
        site_config,
        initialize_context,
        switch_context,
        fetch_site_config
    } = useSite();

    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('theme_preference') || 'light';
    });
    const [sidebar_collapsed, setSidebarCollapsed] = useState(false);

    // Initialize context from stored default if needed
    useEffect(() => {
        const stored_context = sessionStorage.getItem('current_context');
        if (stored_context && !current_context) {
            initialize_context(stored_context);
        }
    }, []);

    // Fetch site config when location changes AND we have a context
    useEffect(() => {
        if (current_context) {
            fetch_site_config(location.pathname);
        }
    }, [location.pathname, current_context]);

    // Apply theme
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme_preference', theme);
    }, [theme]);

    const handle_theme_toggle = () => {
        setTheme(prev => prev === 'light' ? 'dark' : 'light');
    };

    const toggle_sidebar = () => {
        setSidebarCollapsed(!sidebar_collapsed);
    };

    const handle_logout = () => {
        logout();
    };

    if (context_loading || !site_config) {
        return (
            <div className="d-flex justify-content-center align-items-center min-vh-100">
                <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    const site_data = site_config;
    const menu_data = { items: site_config?.menu_items || [] };

    return (
        <div id="app-content">
            <div className="topbar htmx-indicator"></div>

            <header className="header">
                <div className="header_brand">
                    <div className="logo_wrapper">
                        {theme === 'light' ? (
                            site_data.logo_desktop && (
                                <img
                                    src={site_data.logo_desktop}
                                    alt={`${site_data.name || 'Site'} logo`}
                                    className="header_logo"
                                />
                            )
                        ) : (
                            site_data.logo_desktop_dark && (
                                <img
                                    src={site_data.logo_desktop_dark}
                                    alt={`${site_data.name || 'Site'} logo`}
                                    className="header_logo"
                                />
                            )
                        )}
                    </div>
                    <h1>{site_data.name || 'Dashboard'}</h1>
                </div>

                <div className="header_actions">
                    {site_data.maintenance_mode && (
                        <div className="maintenance_indicator me-3">
                            <span className="badge bg-warning text-dark">
                                <i className="fas fa-tools me-1"></i>
                                Maintenance Mode
                            </span>
                        </div>
                    )}

                    <NineDotMenu
                        theme={theme}
                        user={user}
                        available_contexts={available_contexts || []}
                        current_context={current_context}
                        onSwitchContext={switch_context}
                        onToggleTheme={handle_theme_toggle}
                        onLogout={logout}
                    />
                </div>
            </header>

            <Breadcrumbs 
                site_config={site_config}
                current_section={current_context}
                available_sections={available_contexts}
            />

            <div className={`content_area ${sidebar_collapsed ? 'collapsed' : ''}`}>
                <SidebarMenu 
                    menu_items={menu_data.items}
                    collapsed={sidebar_collapsed}
                    onToggleCollapse={toggle_sidebar}
                />

                <div className="main_content" id="main-content">
                    {children}
                </div>
            </div>

            <footer className="footer">
                <div className="footer_content">
                    <p>{site_data.footer_text || `© ${new Date().getFullYear()} ${site_data.name || 'Your Company'}. All rights reserved.`}</p>
                    {site_data.tagline && (
                        <p className="tagline">{site_data.tagline}</p>
                    )}
                </div>
            </footer>
        </div>
    );
};

export default DefaultLayout;