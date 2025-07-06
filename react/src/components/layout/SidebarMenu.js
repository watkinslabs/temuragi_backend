import React, { useState, useEffect } from 'react';
import { useNavigation } from '../../App';
import { useSite } from '../../contexts/SiteContext';

const SidebarMenu = ({ collapsed, onToggleCollapse }) => {
    const { current_view, navigate_to } = useNavigation();
    const { menu_items = [], current_context } = useSite();
    
    // Debug logging
    useEffect(() => {
        console.log('SidebarMenu: Current context:', current_context);
        console.log('SidebarMenu: Menu items:', menu_items);
    }, [current_context, menu_items]);

    // Initialize expanded menus from localStorage
    const [expanded_menus, setExpandedMenus] = useState(() => {
        const saved = localStorage.getItem('expanded_menus');
        return saved ? JSON.parse(saved) : {};
    });

    // Save expanded menus state to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem('expanded_menus', JSON.stringify(expanded_menus));
    }, [expanded_menus]);

    // Auto-expand active menu sections when view changes
    useEffect(() => {
        if (menu_items.length > 0) {
            auto_expand_active_menus(menu_items);
        }
    }, [current_view, menu_items]);

    // Convert URL to view name (remove leading slash and handle nested paths)
    const url_to_view = (url) => {
        if (!url) return 'home';
        return url.replace(/^\//, '') || 'home';
    };

    // Check if a menu item is active
    const is_item_active = (item) => {
        const item_view = url_to_view(item.url);
        return current_view === item_view;
    };

    // Auto-expand menu sections that contain the current active view
    const auto_expand_active_menus = (items) => {
        const find_and_expand_active = (items, parent_id = null) => {
            for (const item of items) {
                if (is_item_active(item)) {
                    // Found active item, expand its parent
                    if (parent_id && !expanded_menus[parent_id]) {
                        setExpandedMenus(prev => ({
                            ...prev,
                            [parent_id]: true
                        }));
                    }
                    return true;
                }

                if (item.items && item.items.length > 0) {
                    const found = find_and_expand_active(item.items, item.id);
                    if (found && !expanded_menus[item.id]) {
                        setExpandedMenus(prev => ({
                            ...prev,
                            [item.id]: true
                        }));
                    }
                }
            }
            return false;
        };

        find_and_expand_active(items);
    };

    const toggle_menu_expansion = (menu_id) => {
        setExpandedMenus(prev => ({
            ...prev,
            [menu_id]: !prev[menu_id]
        }));
    };

    const handle_navigation = (url) => {
        const view = url_to_view(url);
        navigate_to(view);
    };

    const render_menu_item = (item, depth = 0) => {
        const has_children = item.items && item.items.length > 0;
        const is_expanded = expanded_menus[item.id];
        const is_active = is_item_active(item);

        // Check if any child is active
        const has_active_child = (items) => {
            return items?.some(child =>
                is_item_active(child) ||
                (child.items && has_active_child(child.items))
            );
        };

        const is_parent_of_active = has_children && has_active_child(item.items);
        // Handle tier type items (parent categories)
        if (item.type === 'tier') {
            return (
                <div key={item.id} className="sidebar_section">
                    <div
                        className={`sidebar_section_header ${is_parent_of_active ? 'has-active-child' : ''}`}
                        onClick={() => toggle_menu_expansion(item.id)}
                        style={{ 
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}
                    >
                        <h5 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
                            {item.icon && <i className={`fas ${item.icon} me-2`}></i>}
                            {item.display}
                        </h5>
                        <i className={`fas fa-chevron-${is_expanded ? 'down' : 'right'}`}></i>
                    </div>
                    {is_expanded && (
                        <ul className="nav flex-column">
                            {item.items.map(child => render_menu_item(child, depth + 1))}
                        </ul>
                    )}
                </div>
            );
        }

        // Handle link type items
        if (item.type === 'link') {
            const is_external = item.url?.startsWith('http://') || item.url?.startsWith('https://');

            return (
                <li key={item.id} className="nav-item">
                    {has_children ? (
                        <>
                            <button
                                type="button"
                                className={`nav-link d-flex justify-content-between align-items-center ${is_active ? 'active' : ''} ${is_parent_of_active ? 'has-active-child' : ''}`}
                                onClick={(e) => {
                                    e.preventDefault();
                                    toggle_menu_expansion(item.id);
                                }}
                                style={{
                                    width: '100%',
                                    border: 'none',
                                    background: 'transparent',
                                    textAlign: 'left',
                                    padding: 'var(--bs-nav-link-padding-y) var(--bs-nav-link-padding-x)'
                                }}
                            >
                                <span>
                                    {item.icon && <i className={`fas ${item.icon} me-2`}></i>}
                                    {item.display}
                                </span>
                                <i className={`fas fa-chevron-${is_expanded ? 'down' : 'right'}`}></i>
                            </button>
                            {is_expanded && (
                                <ul className="nav flex-column ms-3">
                                    {item.items.map(child => render_menu_item(child, depth + 1))}
                                </ul>
                            )}
                        </>
                    ) : (
                        is_external ? (
                            <a
                                href={item.url}
                                className={`nav-link ${is_active ? 'active' : ''}`}
                                target={item.new_tab ? '_blank' : undefined}
                                rel={item.new_tab ? 'noopener noreferrer' : undefined}
                            >
                                {item.icon && <i className={`fas ${item.icon} me-2`}></i>}
                                {item.display}
                            </a>
                        ) : (
                            <button
                                type="button"
                                className={`nav-link ${is_active ? 'active' : ''}`}
                                onClick={() => handle_navigation(item.url)}
                                style={{
                                    width: '100%',
                                    border: 'none',
                                    background: 'transparent',
                                    textAlign: 'left',
                                    cursor: 'pointer'
                                }}
                            >
                                {item.icon && <i className={`fas ${item.icon} me-2`}></i>}
                                {item.display}
                            </button>
                        )
                    )}
                </li>
            );
        }

        return null;
    };

    return (
        <div className="sidebar_container">
            <aside className="sidebar">
                <div className="sidebar_toggle" onClick={onToggleCollapse}>
                    <i className="fas fa-chevron-left"></i>
                </div>
                <nav className="sidebar_nav">
                    {menu_items && menu_items.length > 0 ? (
                        menu_items.map(item => render_menu_item(item))
                    ) : (
                        <div className="sidebar_section">
                            <h5>Navigation</h5>
                            <ul className="nav flex-column">
                                <li className="nav-item">
                                    <button
                                        type="button"
                                        className="nav-link"
                                        onClick={() => navigate_to('home')}
                                        style={{
                                            width: '100%',
                                            border: 'none',
                                            background: 'transparent',
                                            textAlign: 'left',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        <i className="fas fa-home me-2"></i>Dashboard
                                    </button>
                                </li>
                            </ul>
                        </div>
                    )}
                </nav>
            </aside>
        </div>
    );
};

// Memoize but include menu_items in dependency check
export default React.memo(SidebarMenu, (prevProps, nextProps) => {
    // Re-render if collapsed state changes
    return prevProps.collapsed === nextProps.collapsed;
});