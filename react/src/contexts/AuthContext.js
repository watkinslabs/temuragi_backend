// react/src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
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

    // Refresh handling state
    const refresh_lock = useRef(false);
    const refresh_promise = useRef(null);
    const token_expiry = useRef(null);
    const refresh_retry_count = useRef(0);
    const max_refresh_retries = 3;

    // Add helper functions for cookie management at the top of AuthProvider
    const set_cookie = (name, value, days = 365 * 10) => {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    };

    const delete_cookie = (name) => {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;SameSite=Lax`;
    };
    
    // Allow SiteProvider to register its clear function
    const register_clear_site = (callback) => {
        setClearSiteCallback(() => callback);
    };

    // Parse JWT to get expiry time
    const get_token_expiry = (token) => {
        if (!token) return null;
        
        try {
            const parts = token.split('.');
            if (parts.length !== 3) return null;
            
            const payload = JSON.parse(atob(parts[1]));
            // JWT exp is in seconds, convert to milliseconds
            return payload.exp ? payload.exp * 1000 : null;
        } catch (error) {
            console.error('Failed to parse token:', error);
            return null;
        }
    };

    // Check if token is expired or about to expire
    const is_token_expired = (expiry_time, buffer_minutes = 2) => {
        if (!expiry_time) return true;
        
        // Add buffer to refresh before actual expiry
        const buffer_ms = buffer_minutes * 60 * 1000;
        return Date.now() >= (expiry_time - buffer_ms);
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

        // Set token expiry
        const expiry = get_token_expiry(api_token);
        token_expiry.current = expiry;

        // Check if token is already expired BEFORE making any API calls
        if (is_token_expired(expiry)) {
            console.log('Token expired on mount, refreshing...');
            const refresh_success = await refreshToken();
            if (!refresh_success) {
                clearAuth();
                setLoading(false);
                return;
            }
            // Get the new token after refresh
            const new_api_token = localStorage.getItem('api_token');
            const new_expiry = get_token_expiry(new_api_token);
            token_expiry.current = new_expiry;
        }

        try {
            // NOW validate the current token (which should be fresh if it was expired)
            const current_token = localStorage.getItem('api_token');
            const response = await config.apiCall(config.getUrl(config.api.endpoints.auth.validate), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${current_token}`,
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
            } else {
                // Validation failed - clear auth
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


                set_cookie('user_id', data.user_id);
                if (data.user_info && data.user_info.email) {
                    set_cookie('email', data.user_info.email);
                }


                // Store token expiry
                const expiry = get_token_expiry(data.api_token);
                token_expiry.current = expiry;

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

                // Reset refresh retry count on successful login
                refresh_retry_count.current = 0;

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
        // If already refreshing, wait for that refresh to complete
        if (refresh_lock.current && refresh_promise.current) {
            console.log('Refresh already in progress, waiting...');
            return refresh_promise.current;
        }

        // Set the lock
        refresh_lock.current = true;

        // Create the refresh promise
        refresh_promise.current = (async () => {
            const refresh_token = localStorage.getItem('refresh_token');
            if (!refresh_token) {
                refresh_lock.current = false;
                refresh_promise.current = null;
                return false;
            }

            try {
                console.log('Attempting token refresh...');
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

                    // Update token expiry
                    const expiry = get_token_expiry(data.api_token);
                    token_expiry.current = expiry;

                    // Update user info if provided
                    if (data.user_info) {
                        localStorage.setItem('user_info', JSON.stringify(data.user_info));
                        setUser(data.user_info);
                    }

                    setIsAuthenticated(true);
                    
                    // Reset retry count on successful refresh
                    refresh_retry_count.current = 0;
                    
                    console.log('Token refresh successful');
                    return true;
                } else {
                    // Check if this is a temporary failure or permanent
                    if (response.status === 401 || response.status === 403) {
                        // Refresh token is invalid, this is permanent
                        console.log('Refresh token is invalid');
                        refresh_retry_count.current = max_refresh_retries; // Don't retry
                        return false;
                    } else if (response.status >= 500) {
                        // Server error, might be temporary
                        refresh_retry_count.current++;
                        console.log(`Refresh failed with server error, retry count: ${refresh_retry_count.current}`);
                        
                        if (refresh_retry_count.current < max_refresh_retries) {
                            // Wait and retry
                            await new Promise(resolve => setTimeout(resolve, 1000 * refresh_retry_count.current));
                            refresh_lock.current = false;
                            refresh_promise.current = null;
                            return refreshToken(); // Recursive retry
                        }
                    }
                    return false;
                }
            } catch (error) {
                console.error('Token refresh failed:', error);
                refresh_retry_count.current++;
                
                if (refresh_retry_count.current < max_refresh_retries) {
                    // Network error, wait and retry
                    await new Promise(resolve => setTimeout(resolve, 1000 * refresh_retry_count.current));
                    refresh_lock.current = false;
                    refresh_promise.current = null;
                    return refreshToken(); // Recursive retry
                }
                
                return false;
            } finally {
                refresh_lock.current = false;
                refresh_promise.current = null;
            }
        })();

        return refresh_promise.current;
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

        // Clear cookies
        delete_cookie('user_id');
        delete_cookie('email');

        // Clear state
        setIsAuthenticated(false);
        setUser(null);

        // Reset refresh state
        refresh_lock.current = false;
        refresh_promise.current = null;
        token_expiry.current = null;
        refresh_retry_count.current = 0;

        // Stop token check interval
        stop_token_check_interval();
    };

    // Periodic token validation
    let token_check_interval = null;

    const start_token_check_interval = () => {
        // Clear any existing interval
        stop_token_check_interval();

        // Check token every minute (more frequently to catch expiry)
        token_check_interval = setInterval(async () => {
            const api_token = localStorage.getItem('api_token');
            if (!api_token) {
                clearAuth();
                return;
            }

            // Check if token is about to expire
            if (is_token_expired(token_expiry.current, 5)) { // 5 minute buffer
                console.log('Token about to expire, refreshing proactively...');
                const refresh_success = await refreshToken();
                if (!refresh_success) {
                    // Only clear auth if we've exhausted retries
                    if (refresh_retry_count.current >= max_refresh_retries) {
                        clearAuth();
                    }
                }
                return; // Don't validate if we just refreshed
            }

            // Validate token health periodically
            try {
                const response = await config.apiCall(config.getUrl(config.api.endpoints.auth.validate), {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${api_token}`,
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    }
                });

                if (!response.ok && response.status === 401) {
                    // Try to refresh
                    const refresh_success = await refreshToken();
                    if (!refresh_success && refresh_retry_count.current >= max_refresh_retries) {
                        clearAuth();
                    }
                }
            } catch (error) {
                console.error('Token validation error:', error);
                // Don't clear auth on network errors
            }
        }, 60 * 1000); // Check every minute
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

    // Set up global auth headers helper - MOVED TO SEPARATE useEffect
    useEffect(() => {
        if (!window.app) window.app = {};

        window.app.getAuthHeaders = () => {
            const token = localStorage.getItem('api_token');
            return {
                'Authorization': token ? `Bearer ${token}` : '',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
            };
        };
    }, []);

    // Global fetch interceptor in separate useEffect with proper dependencies
    useEffect(() => {
        // Only set up interceptor after initial auth check is complete
        if (loading) return;

        const original_fetch = window.fetch;
        window.fetch = async (...args) => {
            let response = await original_fetch(...args);

            // If we get a 401 and we're not already on the login page
            if (response.status === 401 && !window.location.pathname.includes('/login')) {
                const url = typeof args[0] === 'string' ? args[0] : args[0].url;

                // Don't intercept auth endpoints
                if (!url.includes('/auth/')) {
                    // Try to refresh token
                    const refresh_success = await refreshToken();
                    if (refresh_success) {
                        // Retry the original request with new token
                        const new_token = localStorage.getItem('api_token');
                        if (args[1] && args[1].headers) {
                            args[1].headers['Authorization'] = `Bearer ${new_token}`;
                        } else if (args[1]) {
                            args[1].headers = {
                                ...args[1].headers,
                                'Authorization': `Bearer ${new_token}`
                            };
                        } else {
                            args[1] = {
                                headers: {
                                    'Authorization': `Bearer ${new_token}`
                                }
                            };
                        }
                        response = await original_fetch(...args);
                    } else if (refresh_retry_count.current >= max_refresh_retries) {
                        // Only clear auth if we've exhausted retries
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
    }, [loading]); // Only run after loading is complete

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