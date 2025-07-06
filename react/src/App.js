// react/src/App.js
import React, { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SiteProvider, useSite } from './contexts/SiteContext';
import Login from './components/Login';
import DynamicPage from './components/DynamicPage';
import LoadingScreen from './components/LoadingScreen';
import DefaultLayout from './components/DefaultLayout';

// Navigation context for state-based routing
const NavigationContext = React.createContext();

export const useNavigation = () => {
    const context = React.useContext(NavigationContext);
    if (!context) throw new Error('useNavigation must be used within NavigationProvider');
    return context;
};

// Protected app wrapper
const ProtectedApp = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return <LoadingScreen />;
    }

    if (!isAuthenticated) {
        return <Login />;
    }

    return children;
};

// Wire up the auth and site contexts
const ContextConnector = ({ children }) => {
    const { register_clear_site } = useAuth();
    const { clear_context } = useSite();

    useEffect(() => {
        // Register the site clear function with auth context
        register_clear_site(clear_context);
    }, [register_clear_site, clear_context]);

    return children;
};

// Main app content - layout stays stable, only content changes
const AppContent = () => {
    const [current_view, setCurrentView] = useState('home');
    const [view_params, setViewParams] = useState({});
    const { initialize_context, fetch_site_config, current_context } = useSite();

    // Initialize context and fetch site config on mount
    useEffect(() => {
        const init_app = async () => {
            // First check for stored context
            const stored_context = sessionStorage.getItem('current_context') || localStorage.getItem('default_context');
            
            if (stored_context) {
                console.log('Initializing with stored context:', stored_context);
                initialize_context(stored_context);
            }
            
            // Always fetch site config to get menu items and available contexts
            console.log('Fetching initial site config...');
            await fetch_site_config('/');
        };
        
        init_app();
    }, []); // Run only on mount

    // Prevent browser back button from actually navigating
    useEffect(() => {
        // Push initial state at current URL
        window.history.pushState(null, '', window.location.href);

        // Handle browser back button
        const handle_pop_state = (e) => {
            // Push state again to prevent actual navigation but keep current URL
            window.history.pushState(null, '', window.location.href);
        };

        // Prevent navigation
        window.addEventListener('popstate', handle_pop_state);

        // Cleanup
        return () => {
            window.removeEventListener('popstate', handle_pop_state);
        };
    }, []);

    // Navigation function
    const navigate_to = (view, params = {}) => {
        console.log('Navigating to:', view, params);
        setCurrentView(view);
        setViewParams(params);
    };

    // Make navigate_to globally available for context switching
    useEffect(() => {
        window.navigate_to = navigate_to;
        return () => {
            delete window.navigate_to;
        };
    }, []);

    const navigation_value = {
        current_view,
        view_params,
        navigate_to
    };

    return (
        <NavigationContext.Provider value={navigation_value}>
            <ProtectedApp>
                <DefaultLayout>
                    <DynamicPage />
                </DefaultLayout>
            </ProtectedApp>
        </NavigationContext.Provider>
    );
};

const App = () => {
    // Don't change the URL - just leave it wherever it was loaded
    return (
        <AuthProvider>
            <SiteProvider>
                <ContextConnector>
                    <AppContent />
                </ContextConnector>
            </SiteProvider>
        </AuthProvider>
    );
};

export default App;
export { NavigationContext };