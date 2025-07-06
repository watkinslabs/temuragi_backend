import React from 'react';
import { useNavigation } from '../../App';
import { useSite } from '../../contexts/SiteContext';

const Breadcrumbs = () => {
    const { current_view, navigate_to } = useNavigation();
    const { site_info, current_context, available_contexts } = useSite();

    // Get current context display name
    const get_context_display_name = () => {
        if (!current_context || !available_contexts || available_contexts.length === 0) {
            return 'Home';
        }

        const context = available_contexts.find(c => c.name === current_context);
        return context ? context.display : current_context;
    };

    // Parse the current view into breadcrumb items
    const get_breadcrumb_items = () => {
        const items = [];

        // Always start with the context name
        items.push({
            label: get_context_display_name(),
            view: 'home',
            is_last: current_view === 'home'
        });

        // Add view segments if not on home
        if (current_view !== 'home') {
            // Convert view name to readable format (snake_case to Title Case)
            const label = current_view
                .split('_')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');

            items.push({
                label: label,
                view: current_view,
                is_last: true
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
                                <button
                                    onClick={() => navigate_to(item.view)}
                                    style={{
                                        background: 'none',
                                        border: 'none',
                                        color: 'var(--bs-link-color)',
                                        cursor: 'pointer',
                                        padding: 0,
                                        textDecoration: 'underline'
                                    }}
                                >
                                    {item.label}
                                </button>
                            )}
                        </li>
                    ))}
                </ol>
            </nav>
        </div>
    );
};

export default Breadcrumbs;