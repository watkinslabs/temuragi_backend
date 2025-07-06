import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const SidebarMenu = ({ menu_items = [], collapsed, onToggleCollapse }) => {
    const location = useLocation();
    
    // Initialize expanded menus from localStorage
    const [expanded_menus, setExpandedMenus] = useState(() => {
        const saved = localStorage.getItem('expanded_menus');
        return saved ? JSON.parse(saved) : {};
    });

    // Save expanded menus state to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem('expanded_menus', JSON.stringify(expanded_menus));
    }, [expanded_menus]);

    // Auto-expand active menu sections when location changes
    useEffect(() => {
        if (menu_items.length > 0) {
            auto_expand_active_menus(menu_items);
        }
    }, [location.pathname, menu_items]);

    // Auto-expand menu sections that contain the current active route
    const auto_expand_active_menus = (items) => {
        const find_and_expand_active = (items, parent_id = null) => {
            for (const item of items) {
                if (item.url === location.pathname) {
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

    const render_menu_item = (item, depth = 0) => {
        const has_children = item.items && item.items.length > 0;
        const is_expanded = expanded_menus[item.id];
        const is_active = location.pathname === item.url;

        // Check if any child is active
        const has_active_child = (items) => {
            return items?.some(child =>
                child.url === location.pathname ||
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
                        style={{ cursor: 'pointer' }}
                    >
                        <h5>
                            {item.icon && <i className={`fas ${item.icon} me-2`}></i>}
                            {item.display}
                            <i className={`fas fa-chevron-${is_expanded ? 'down' : 'right'} float-end`}></i>
                        </h5>
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
                            <Link
                                to={item.url}
                                className={`nav-link ${is_active ? 'active' : ''}`}
                            >
                                {item.icon && <i className={`fas ${item.icon} me-2`}></i>}
                                {item.display}
                            </Link>
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
                                    <Link to="/" className="nav-link">
                                        <i className="fas fa-home me-2"></i>Dashboard
                                    </Link>
                                </li>
                            </ul>
                        </div>
                    )}
                </nav>
            </aside>
        </div>
    );
};

export default SidebarMenu;