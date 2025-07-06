import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Breadcrumbs = ({ site_config, current_context, available_contexts }) => {
    const location = useLocation();

    // Get current context display name
    const get_context_display_name = () => {
        if (!current_context || !available_contexts || available_contexts.length === 0) {
            return 'Home';
        }

        const context = available_contexts.find(c => c.name === current_context);
        return context ? context.display : current_context;
    };

    // Parse the current path into breadcrumb items
    const get_breadcrumb_items = () => {
        const path = location.pathname;
        const items = [];

        // Always start with the context name
        items.push({
            label: get_context_display_name(),
            path: '/',
            is_last: path === '/'
        });

        // Add path segments if not on home
        if (path !== '/') {
            const segments = path.split('/').filter(Boolean);
            let accumulated_path = '';

            segments.forEach((segment, index) => {
                accumulated_path += `/${segment}`;
                const is_last = index === segments.length - 1;

                // Convert segment to readable format (snake_case to Title Case)
                const label = segment
                    .split('_')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');

                items.push({
                    label: label,
                    path: accumulated_path,
                    is_last: is_last
                });
            });
        }

        return items;
    };

    const breadcrumb_items = get_breadcrumb_items();

    return (
        <div className="breadcrumbs">
            <nav aria-label="breadcrumb">
                <ol className="breadcrumb">
                    {breadcrumb_items.map((item, index) => (
                        <li
                            key={index}
                            className={`breadcrumb-item ${item.is_last ? 'active' : ''}`}
                            aria-current={item.is_last ? 'page' : undefined}
                        >
                            {item.is_last ? (
                                item.label
                            ) : (
                                <Link to={item.path}>{item.label}</Link>
                            )}
                        </li>
                    ))}
                </ol>
            </nav>
        </div>
    );
};

export default Breadcrumbs;