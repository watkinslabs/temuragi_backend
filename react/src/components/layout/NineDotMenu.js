import React, { useState, useEffect, useRef } from 'react';

const NineDotMenu = ({
    theme,
    user,
    available_contexts,
    current_context,
    onSwitchContext,
    onToggleTheme,
    onLogout
}) => {
    const [is_open, setIsOpen] = useState(false);
    const menu_ref = useRef(null);

    // Handle outside clicks
    useEffect(() => {
        if (!is_open) return;

        const handle_outside_click = (e) => {
            if (menu_ref.current && !menu_ref.current.contains(e.target)) {
                setIsOpen(false);
            }
        };

        // Add delay to prevent immediate trigger
        const timer = setTimeout(() => {
            document.addEventListener('click', handle_outside_click);
        }, 100);

        return () => {
            clearTimeout(timer);
            document.removeEventListener('click', handle_outside_click);
        };
    }, [is_open]);

    const handle_context_switch = (context_name) => {
        onSwitchContext(context_name);
        setIsOpen(false);
    };

    const handle_theme_toggle = () => {
        onToggleTheme();
    };

    const handle_logout = (e) => {
        e.preventDefault();
        onLogout();
        setIsOpen(false);
    };

    // Debug current state
    useEffect(() => {
        console.log('NineDotMenu state:', {
            current_context,
            available_contexts,
            user,
            contexts_type: Array.isArray(available_contexts) ? 'array' : typeof available_contexts,
            contexts_content: available_contexts
        });
    }, [current_context, available_contexts, user]);

    return (
        <div className="nine_dot_menu" ref={menu_ref} style={{ position: 'relative' }}>
            <button
                className="nine_dot_btn"
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setIsOpen(prev => !prev);
                }}
                type="button"
                style={{
                    background: 'none',
                    border: 'none',
                    padding: '8px',
                    cursor: 'pointer',
                    fontSize: '20px',
                    color: 'inherit'
                }}
                aria-label="Settings menu"
                aria-expanded={is_open}
            >
                <i className="fas fa-th"></i>
            </button>

            {is_open && (
                <div
                    className="nine_dot_dropdown"
                    style={{
                        position: 'absolute',
                        right: 0,
                        top: '100%',
                        marginTop: '8px',
                        minWidth: '250px',
                        backgroundColor: theme === 'dark' ? 'var(--theme-surface-dark)' : 'var(--theme-surface)',
                        border: `1px solid ${theme === 'dark' ? 'var(--theme-border-color-dark)' : 'var(--theme-border-color)'}`,
                        borderRadius: 'var(--theme-card-border-radius)',
                        boxShadow: 'var(--theme-shadow-lg)',
                        zIndex: 1000,
                        padding: '16px',
                        color: theme === 'dark' ? 'var(--theme-text-dark)' : 'var(--theme-text)'
                    }}
                >
                    {/* Context Switcher */}
                    {console.log('Contexts check:', {
                        available_contexts,
                        length: available_contexts?.length,
                        show: available_contexts && available_contexts.length > 1
                    })}
                    {available_contexts && available_contexts.length > 0 && (
                        <>
                            <div className="dropdown_section mb-3">
                                <h6 className="mb-2" style={{
                                    color: theme === 'dark' ? 'var(--theme-text-muted-dark)' : 'var(--theme-text-muted)'
                                }}>
                                    Application Switcher
                                </h6>
                                <div className="context_switcher">
                                    {available_contexts.map(context => {
                                        // Compare using the ID field since that's what the server expects
                                        const is_active = current_context === context.name ||
                                                         // Also check if current_context matches the context field
                                                         (context.context && current_context === context.context);

                                        // Debug logging
                                        console.log('Context comparison:', {
                                            context,
                                            current_context,
                                            is_active,
                                            checks: {
                                                name_match: current_context === context.name,
                                                context_match: context.context && current_context === context.context
                                            }
                                        });

                                        return (
                                            <button
                                                key={context.name}
                                                type="button"
                                                className={`btn btn-sm w-100 mb-2 ${
                                                    is_active
                                                        ? 'btn-primary'
                                                        : 'btn-outline-secondary'
                                                }`}
                                                onClick={() => handle_context_switch(context.name)}
                                                disabled={is_active}
                                            >
                                                {context.icon && <i className={`${context.icon} me-2`}></i>}
                                                {context.display || context.name}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                            <hr className="my-2" style={{
                                borderColor: theme === 'dark' ? 'var(--theme-border-color-dark)' : 'var(--theme-border-color)',
                                opacity: 0.5
                            }} />
                        </>
                    )}

                    {/* Theme Toggle */}
                    <div className="dropdown_section mb-3">
                        <h6 className="mb-2" style={{
                            color: theme === 'dark' ? 'var(--theme-text-muted-dark)' : 'var(--theme-text-muted)'
                        }}>
                            Appearance
                        </h6>
                        <div className="theme_toggle d-flex align-items-center">
                            <div className="form-check form-switch">
                                <input
                                    className="form-check-input"
                                    type="checkbox"
                                    id="dark_mode_toggle"
                                    checked={theme === 'dark'}
                                    onChange={handle_theme_toggle}
                                />
                                <label className="form-check-label ms-2" htmlFor="dark_mode_toggle">
                                    Dark Mode
                                </label>
                            </div>
                        </div>
                    </div>

                    <hr className="my-2" style={{
                        borderColor: theme === 'dark' ? 'var(--theme-border-color-dark)' : 'var(--theme-border-color)',
                        opacity: 0.5
                    }} />

                    {/* Account Section */}
                    <div className="dropdown_section">
                        <h6 className="mb-2" style={{
                            color: theme === 'dark' ? 'var(--theme-text-muted-dark)' : 'var(--theme-text-muted)'
                        }}>
                            Account
                        </h6>
                        {user && (
                            <div className="user_info mb-3 p-2 rounded" style={{
                                backgroundColor: theme === 'dark' ? 'var(--theme-background-dark)' : 'var(--theme-component)',
                                border: `1px solid ${theme === 'dark' ? 'var(--theme-border-color-dark)' : 'var(--theme-border-color)'}`
                            }}>
                                <small className="d-block" style={{
                                    color: theme === 'dark' ? 'var(--theme-text-muted-dark)' : 'var(--theme-text-muted)'
                                }}>
                                    Logged in as:
                                </small>
                                <strong>{user.name || user.username || user.email}</strong>
                            </div>
                        )}
                        <button
                            type="button"
                            className="dropdown_link btn btn-sm btn-outline-danger w-100"
                            onClick={handle_logout}
                            style={{
                                borderColor: 'var(--theme-danger)',
                                color: 'var(--theme-danger)'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.backgroundColor = 'var(--theme-danger)';
                                e.target.style.color = 'white';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.backgroundColor = 'transparent';
                                e.target.style.color = 'var(--theme-danger)';
                            }}
                        >
                            <i className="fas fa-sign-out-alt me-2"></i>Logout
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NineDotMenu;