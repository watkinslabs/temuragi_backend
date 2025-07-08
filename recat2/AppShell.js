// react/src/components/AppShell.js
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useSiteInfo, useMenu, useContextState } from '../contexts/SiteContext';
import NineDotMenu from './layout/NineDotMenu';
import Breadcrumbs from './layout/Breadcrumbs';
import SidebarMenu from './layout/SidebarMenu';

const AppShell = ({ children }) => {
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

    return (
        <div id="app-content">
            <div className="topbar htmx-indicator"></div>

            <header className="header">
                <HeaderContent theme={theme} />
                
                <div className="header_actions">
                    <MaintenanceIndicator />
                    <NineDotMenuWrapper
                        theme={theme}
                        user={user}
                        onToggleTheme={handle_theme_toggle}
                        onLogout={logout}
                    />
                </div>
            </header>

            <BreadcrumbsWrapper />

            <div className={`content_area ${sidebar_collapsed ? 'collapsed' : ''}`}>
                <SidebarMenu
                    collapsed={sidebar_collapsed}
                    onToggleCollapse={toggle_sidebar}
                />

                <div className="main_content" id="main-content">
                    {children}
                </div>
            </div>

            <FooterContent />
        </div>
    );
};

// Separate components that subscribe to specific contexts
const HeaderContent = React.memo(({ theme }) => {
    const { site_info } = useSiteInfo();
    
    if (!site_info) return null;
    
    return (
        <div className="header_brand">
            <div className="logo_wrapper">
                {theme === 'light' ? (
                    site_info.logo_desktop && (
                        <img
                            src={site_info.logo_desktop}
                            alt={`${site_info.name || 'Site'} logo`}
                            className="header_logo"
                        />
                    )
                ) : (
                    site_info.logo_desktop_dark && (
                        <img
                            src={site_info.logo_desktop_dark}
                            alt={`${site_info.name || 'Site'} logo`}
                            className="header_logo"
                        />
                    )
                )}
            </div>
            <h1>{site_info.name || 'Dashboard'}</h1>
        </div>
    );
});

const MaintenanceIndicator = React.memo(() => {
    const { site_info } = useSiteInfo();
    
    if (!site_info?.maintenance_mode) return null;
    
    return (
        <div className="maintenance_indicator me-3">
            <span className="badge bg-warning text-dark">
                <i className="fas fa-tools me-1"></i>
                Maintenance Mode
            </span>
        </div>
    );
});

const NineDotMenuWrapper = React.memo(({ theme, user, onToggleTheme, onLogout }) => {
    const {
        current_context,
        available_contexts,
        switch_context
    } = useContextState();
    
    return (
        <NineDotMenu
            theme={theme}
            user={user}
            available_contexts={available_contexts || []}
            current_context={current_context}
            onSwitchContext={switch_context}
            onToggleTheme={onToggleTheme}
            onLogout={onLogout}
        />
    );
});

const BreadcrumbsWrapper = React.memo(() => {
    const { site_info } = useSiteInfo();
    const { current_context, available_contexts } = useContextState();
    
    return (
        <Breadcrumbs
            site_config={site_info}
            current_context={current_context}
            available_contexts={available_contexts}
        />
    );
});

const FooterContent = React.memo(() => {
    const { site_info } = useSiteInfo();
    
    if (!site_info) return null;
    
    return (
        <footer className="footer">
            <div className="footer_content">
                <p>{site_info.footer_text || `© ${new Date().getFullYear()} ${site_info.name || 'Your Company'}. All rights reserved.`}</p>
                {site_info.tagline && (
                    <p className="tagline">{site_info.tagline}</p>
                )}
            </div>
        </footer>
    );
});

export default AppShell;