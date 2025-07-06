import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigation } from '../App';
import NineDotMenu from './layout/NineDotMenu';
import Breadcrumbs from './layout/Breadcrumbs';
import SidebarMenu from './layout/SidebarMenu';
import config from '../config';

const DefaultLayout = ({ children }) => {
    const { user, logout } = useAuth();
    
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('theme_preference') || 'light';
    });
    const [sidebar_collapsed, setSidebarCollapsed] = useState(false);

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

    // Static site info - load once and cache
    const [static_site_info, setStaticSiteInfo] = useState(() => {
        const cached = sessionStorage.getItem('static_site_info');
        return cached ? JSON.parse(cached) : null;
    });

    // Load site info ONCE on mount
    useEffect(() => {
        if (!static_site_info) {
            config.apiCall(config.getUrl('/site/config'), {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({ path: '/', include_contexts: false })
            })
            .then(res => res.json())
            .then(data => {
                const info = {
                    name: data.site.name,
                    logo_desktop: data.site.logo_desktop,
                    logo_desktop_dark: data.site.logo_desktop_dark,
                    footer_text: data.site.footer_text,
                    tagline: data.site.tagline,
                    maintenance_mode: data.site.maintenance_mode
                };
                setStaticSiteInfo(info);
                sessionStorage.setItem('static_site_info', JSON.stringify(info));
            })
            .catch(error => {
                console.error('Failed to load site config:', error);
            });
        }
    }, []);

    if (!static_site_info) {
        return (
            <div className="d-flex justify-content-center align-items-center min-vh-100">
                <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    return (
        <div id="app-content">
            <div className="topbar htmx-indicator"></div>

            <header className="header">
                <div className="header_brand">
                    <div className="logo_wrapper">
                        {theme === 'light' ? (
                            static_site_info.logo_desktop && (
                                <img
                                    src={static_site_info.logo_desktop}
                                    alt={`${static_site_info.name || 'Site'} logo`}
                                    className="header_logo"
                                />
                            )
                        ) : (
                            static_site_info.logo_desktop_dark && (
                                <img
                                    src={static_site_info.logo_desktop_dark}
                                    alt={`${static_site_info.name || 'Site'} logo`}
                                    className="header_logo"
                                />
                            )
                        )}
                    </div>
                    <h1>{static_site_info.name || 'Dashboard'}</h1>
                </div>

                <div className="header_actions">
                    {static_site_info.maintenance_mode && (
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
                        onToggleTheme={handle_theme_toggle}
                        onLogout={logout}
                    />
                </div>
            </header>

            <Breadcrumbs />

            <div className={`content_area ${sidebar_collapsed ? 'collapsed' : ''}`}>
                <SidebarMenu
                    collapsed={sidebar_collapsed}
                    onToggleCollapse={toggle_sidebar}
                />

                <div className="main_content" id="main-content">
                    {children}
                </div>
            </div>

            <footer className="footer">
                <div className="footer_content">
                    <p>{static_site_info.footer_text || `© ${new Date().getFullYear()} ${static_site_info.name || 'Your Company'}. All rights reserved.`}</p>
                    {static_site_info.tagline && (
                        <p className="tagline">{static_site_info.tagline}</p>
                    )}
                </div>
            </footer>
        </div>
    );
};

export default React.memo(DefaultLayout);