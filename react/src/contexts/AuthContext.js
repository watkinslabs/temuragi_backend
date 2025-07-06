// react/src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import config from '../config';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
};

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState(null);

    // We'll need to access SiteContext's clear_section
    const [clear_site_callback, setClearSiteCallback] = useState(null);

    // Allow SiteProvider to register its clear function
    const register_clear_site = (callback) => {
        setClearSiteCallback(() => callback);
    };

    // Check if we have valid tokens on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        const api_token = localStorage.getItem('api_token');
        const refresh_token = localStorage.getItem('refresh_token');

        if (!api_token || !refresh_token) {
            setLoading(false);
            return;
        }

        try {
            // First try to validate the current token
            const response = await config.apiCall(config.getUrl(config.api.endpoints.auth.validate), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${api_token}`,
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });

            if (response.ok) {
                const data = await response.json();
                setIsAuthenticated(true);
                setUser(data.user_info);

                // Set up periodic token validation
                start_token_check_interval();
            } else if (response.status === 401) {
                // Token is invalid, try to refresh
                const refresh_success = await refreshToken();
                if (refresh_success) {
                    // Retry validation after refresh
                    await checkAuth();
                } else {
                    // Refresh failed, clear auth
                    clearAuth();
                }
            } else {
                // Other error, clear auth
                clearAuth();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            clearAuth();
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password, remember) => {
        try {
            const response = await config.apiCall(config.getUrl(config.api.endpoints.auth.login), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify({ username, password, remember })
            });

            if (response.ok) {
                const data = await response.json();

                // Store tokens
                localStorage.setItem('api_token', data.api_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('user_info', JSON.stringify(data.user_info));

                // Store the ACTUAL default context from login
                if (data.default_context) {
                    localStorage.setItem('default_context', data.default_context);
                    sessionStorage.setItem('current_context', data.default_context);
                    sessionStorage.setItem('current_section', data.default_context); // Also store as section for compatibility
                }

                // Handle remember me
                if (remember) {
                    localStorage.setItem('remembered_username', username);
                } else {
                    localStorage.removeItem('remembered_username');
                }

                setIsAuthenticated(true);
                setUser(data.user_info);

                // Start token check interval after successful login
                start_token_check_interval();

                return {
                    success: true,
                    landing_page: data.landing_page || '/',
                    default_context: data.default_context
                };
            } else {
                const error_data = await response.json();
                return {
                    success: false,
                    message: error_data.message || 'Login failed'
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: 'Login failed' };
        }
    };

    const refreshToken = async () => {
        const refresh_token = localStorage.getItem('refresh_token');
        if (!refresh_token) {
            clearAuth();
            return false;
        }

        try {
            const response = await config.apiCall(config.getUrl(config.api.endpoints.auth.refresh), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify({ refresh_token })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('api_token', data.api_token);

                // Update user info if provided
                if (data.user_info) {
                    localStorage.setItem('user_info', JSON.stringify(data.user_info));
                    setUser(data.user_info);
                }

                setIsAuthenticated(true);
                return true;
            } else {
                // Refresh token is also invalid
                console.log('Refresh token invalid, logging out');
                clearAuth();
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            clearAuth();
            return false;
        }
    };

    const logout = () => {
        clearAuth();
        // Clear site context if callback is registered
        if (clear_site_callback) {
            clear_site_callback();
        }
    };

    const clearAuth = () => {
        // Clear all auth data
        localStorage.removeItem('api_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_info');
        localStorage.removeItem('default_context');  // Changed from default_section

        // Clear state
        setIsAuthenticated(false);
        setUser(null);

        // Stop token check interval
        stop_token_check_interval();
    };

    // Periodic token validation
    let token_check_interval = null;

    const start_token_check_interval = () => {
        // Clear any existing interval
        stop_token_check_interval();

        // Check token every 5 minutes
        token_check_interval = setInterval(async () => {
            const api_token = localStorage.getItem('api_token');
            if (!api_token) {
                clearAuth();
                return;
            }

            try {
                const response = await config.apiCall(config.getUrl(config.api.endpoints.auth.validate), {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${api_token}`,
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    }
                });

                if (!response.ok) {
                    if (response.status === 401) {
                        // Try to refresh
                        const refresh_success = await refreshToken();
                        if (!refresh_success) {
                            // Refresh failed, clear auth but don't redirect here
                            // Let the ProtectedRoute component handle navigation
                            clearAuth();
                        }
                    }
                }
            } catch (error) {
                console.error('Token validation error:', error);
            }
        }, 5 * 60 * 1000); // 5 minutes
    };

    const stop_token_check_interval = () => {
        if (token_check_interval) {
            clearInterval(token_check_interval);
            token_check_interval = null;
        }
    };

    // Clean up interval on unmount
    useEffect(() => {
        return () => {
            stop_token_check_interval();
        };
    }, []);

    // Set up global auth headers helper
    useEffect(() => {
        if (!window.app) window.app = {};

        window.app.getAuthHeaders = () => {
            const token = localStorage.getItem('api_token');
            return {
                'Authorization': token ? `Bearer ${token}` : '',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
            };
        };

        // Add global request interceptor for 401 responses
        const original_fetch = window.fetch;
        window.fetch = async (...args) => {
            const response = await original_fetch(...args);

            // If we get a 401 and we're not already on the login page
            if (response.status === 401 && !window.location.pathname.includes('/login')) {
                const url = typeof args[0] === 'string' ? args[0] : args[0].url;

                // Don't intercept auth endpoints
                if (!url.includes('/auth/')) {
                    // Try to refresh token
                    const refresh_success = await refreshToken();
                    if (refresh_success) {
                        // Retry the original request with new token
                        if (args[1] && args[1].headers) {
                            args[1].headers['Authorization'] = `Bearer ${localStorage.getItem('api_token')}`;
                        }
                        return original_fetch(...args);
                    } else {
                        // Refresh failed, clear auth
                        clearAuth();
                    }
                }
            }

            return response;
        };

        // Restore original fetch on cleanup
        return () => {
            window.fetch = original_fetch;
        };
    }, []);

    return (
        <AuthContext.Provider value={{
            isAuthenticated,
            loading,
            user,
            login,
            logout,
            refreshToken,
            checkAuth,
            register_clear_site
        }}>
            {children}
        </AuthContext.Provider>
    );
};