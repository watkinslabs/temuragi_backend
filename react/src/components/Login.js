import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import config from '../config';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [remember, setRemember] = useState(false);
    const [show_password, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [site_config, setSiteConfig] = useState(null);
    const [config_loading, setConfigLoading] = useState(true);

    const { login } = useAuth();

    useEffect(() => {
        // CLEAR ALL AUTH DATA when login page loads
        localStorage.removeItem('api_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_info');
        sessionStorage.clear();

        // Clear cookies by making a logout request to the server
        // This ensures server-side session is destroyed
        const clearServerSession = async () => {
            try {
                await config.apiCall(config.getUrl(config.api.endpoints.auth.logout), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    },
                    credentials: 'same-origin'
                });
            } catch (e) {
                // Ignore errors - we're logging out anyway
            }
        };

        clearServerSession().then(() => {
            // Fetch site config for branding AFTER clearing session
            fetch_site_config();
        });

        // Apply theme
        const saved_theme = localStorage.getItem('theme_preference') || 'light';
        document.documentElement.setAttribute('data-theme', saved_theme);
        document.documentElement.setAttribute('data-bs-theme', saved_theme);

        // Check remembered username
        const remembered_username = localStorage.getItem('remembered_username');
        if (remembered_username) {
            setUsername(remembered_username);
            setRemember(true);
        }

        // Check login reason
        const params = new URLSearchParams(window.location.search);
        const reason = params.get('reason');

        if (reason) {
            setError(get_reason_message(reason));
        }
    }, []);

    // In Login.js fetch_site_config function:
    const fetch_site_config = async () => {
        try {
            console.log('Login page fetching site config from:', config.getUrl('/site/config'));

            const response = await config.apiCall(config.getUrl('/site/config'), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                credentials: 'omit'
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Site config response:', data);

                // The site config is nested in data.site
                setSiteConfig(data.site);
            }
        } catch (error) {
            console.error('Failed to fetch site config:', error);
        } finally {
            setConfigLoading(false);
        }
    };

    const get_reason_message = (reason) => {
        const messages = {
            'token_expired': 'Your session has expired. Please log in again.',
            'logout': 'You have been logged out successfully.',
            'unauthorized': 'Please log in to access that page.',
            'csrf_invalid': 'Security token expired. Please log in again.'
        };
        return messages[reason] || 'Please log in to continue.';
    };

    const handle_submit = async (e) => {
        e.preventDefault();
        setError(null);

        if (!username.trim() || !password) {
            setError('Please enter both username and password.');
            return;
        }

        setLoading(true);

        const result = await login(username.trim(), password, remember);

        if (result.success) {
            // Only use the default_context from login response
            if (result.default_context) {
                sessionStorage.setItem('current_context', result.default_context);
            }

            // If you need to navigate to a specific view based on landing_page:
            // Parse the landing_page URL to extract the view
            if (result.landing_page && result.landing_page !== '/') {
                const view = result.landing_page.replace(/^\//, '') || 'home';
                // Store it for the app to use after mounting
                sessionStorage.setItem('initial_view', view);
            }
            
            // Don't set loading to false - let the component unmount naturally
        } else {
            setError(result.message || 'Invalid username or password.');
            setLoading(false);
        }
    };


    const toggle_password = () => {
        setShowPassword(!show_password);
    };

    const theme = localStorage.getItem('theme_preference') || 'light';
    const logo = theme === 'dark'
        ? (site_config?.logo_desktop_dark || site_config?.logo_desktop)
        : site_config?.logo_desktop;

    // Debug logging
    useEffect(() => {
        if (site_config) {
            console.log('Site config loaded:', site_config);
            console.log('Logo URL:', logo);
        }
    }, [site_config, logo]);

    return (
        <div className="login-container">
            <style dangerouslySetInnerHTML={{ __html: `
                .login-container {
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--theme-background);
                    padding: 20px;
                }
                .login-wrapper {
                    width: 100%;
                    max-width: 440px;
                }
                .login-wrapper .card {
                    width: 100%;
                    border: none;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                    margin-bottom: 1.5rem;
                }
                .login-wrapper .card-header {
                    background: var(--bs-white);
                    border-bottom: 1px solid var(--bs-gray-200);
                    padding: 2rem;
                    text-align: center;
                }
                .logo-container {
                    margin-bottom: 1rem;
                }
                .site-logo {
                    max-height: 60px;
                    margin-bottom: 1rem;
                }
                .logo-container h2 {
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                    color: var(--bs-gray-800);
                }
                .security-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: var(--bs-success);
                    font-size: 0.875rem;
                }
                .login-wrapper .card-body {
                    padding: 2rem;
                    position: relative;
                }
                .loading-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s, visibility 0.3s;
                }
                .loading-overlay.active {
                    opacity: 1;
                    visibility: visible;
                }
                .form-floating {
                    margin-bottom: 1rem;
                }
                .password-field-wrapper {
                    position: relative;
                }
                .password-toggle {
                    position: absolute;
                    right: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    cursor: pointer;
                    color: var(--bs-gray-600);
                    z-index: 5;
                }
                .remember-forgot {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1.5rem;
                }
                .btn-login {
                    width: 100%;
                    padding: 0.75rem;
                    font-weight: 600;
                    position: relative;
                }
                .btn-login .spinner-border {
                    display: none;
                    margin-right: 0.5rem;
                }
                .btn-login.loading .spinner-border {
                    display: inline-block;
                }
                .btn-login.loading .button-text {
                    opacity: 0.7;
                }
                .login-footer {
                    text-align: center;
                    color: var(--bs-gray-600);
                    font-size: 0.875rem;
                }
                .login-footer a {
                    color: var(--bs-gray-600);
                    margin: 0 0.5rem;
                }
                .login-footer a:hover {
                    color: var(--bs-primary);
                }
            `}} />

            <div className="login-wrapper">
                <div className="card">
                    <div className="card-header">
                        <div className="logo-container">
                            {!config_loading && logo && (
                                <img
                                    src={logo}
                                    alt={`${site_config?.name || 'Site'} logo`}
                                    className="site-logo"
                                />
                            )}
                            <h2>{site_config?.name || 'Welcome'}</h2>
                            <div className="security-badge">
                                <i className="fas fa-lock"></i>
                                <span>Secure Authentication</span>
                            </div>
                        </div>
                    </div>

                    <div className="card-body">
                        <div className={`loading-overlay ${loading ? 'active' : ''}`}>
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">Loading...</span>
                            </div>
                        </div>

                        {error && (
                            <div className="alert alert-danger alert-dismissible fade show" role="alert">
                                {error}
                                <button
                                    type="button"
                                    className="btn-close"
                                    onClick={() => setError(null)}
                                ></button>
                            </div>
                        )}

                        <form onSubmit={handle_submit} noValidate>
                            <div className="form-floating">
                                <input
                                    type="text"
                                    className="form-control"
                                    id="username"
                                    name="username"
                                    placeholder="Username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    autoComplete="username"
                                    required
                                    disabled={loading}
                                />
                                <label htmlFor="username">Username</label>
                            </div>

                            <div className="form-floating password-field-wrapper">
                                <input
                                    type={show_password ? 'text' : 'password'}
                                    className="form-control"
                                    id="password"
                                    name="password"
                                    placeholder="Password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    autoComplete="current-password"
                                    required
                                    disabled={loading}
                                />
                                <label htmlFor="password">Password</label>
                                <span className="password-toggle" onClick={toggle_password}>
                                    <i className={`fas fa-eye${show_password ? '-slash' : ''}`}></i>
                                </span>
                            </div>

                            <div className="remember-forgot">
                                <div className="form-check">
                                    <input
                                        className="form-check-input"
                                        type="checkbox"
                                        id="remember"
                                        name="remember"
                                        checked={remember}
                                        onChange={(e) => setRemember(e.target.checked)}
                                        disabled={loading}
                                    />
                                    <label className="form-check-label" htmlFor="remember">
                                        Remember me
                                    </label>
                                </div>
                                <a href="/not_found" className="forgot-link text-decoration-none">
                                    Forgot password?
                                </a>
                            </div>

                            <button
                                type="submit"
                                className={`btn btn-primary btn-login ${loading ? 'loading' : ''}`}
                                disabled={loading}
                            >
                                <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                                <span className="button-text">Sign In</span>
                            </button>
                        </form>
                    </div>
                </div>

                <div className="login-footer">
                    <div>© {new Date().getFullYear()} {site_config?.name || 'Your Company'}. All rights reserved.</div>
                    <div>
                        <a href="#" className="text-decoration-none">Privacy Policy</a>
                        <a href="#" className="text-decoration-none">Terms of Service</a>
                        <a href="#" className="text-decoration-none">Security</a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;