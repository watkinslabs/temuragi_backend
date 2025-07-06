// react/src/App.js
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SiteProvider, useSite } from './contexts/SiteContext';
import Login from './components/Login';
import DynamicPage from './components/DynamicPage';
import LoadingScreen from './components/LoadingScreen';
import DefaultLayout from './components/DefaultLayout';

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return <LoadingScreen />;
    }

    if (!isAuthenticated) {
        return <Navigate to={`/login?reason=unauthorized&from=${encodeURIComponent(location.pathname)}`} replace />;
    }

    return children;
};

// Layout wrapper for authenticated routes
const LayoutWrapper = ({ children }) => {
    return (
        <DefaultLayout>
            {children}
        </DefaultLayout>
    );
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

// Main app component
const AppContent = () => {
    const { loading } = useAuth();

    if (loading) {
        return <LoadingScreen />;
    }

    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/*" element={
                <ProtectedRoute>
                    <LayoutWrapper>
                        <DynamicPage />
                    </LayoutWrapper>
                </ProtectedRoute>
            } />
        </Routes>
    );
};

const App = () => {
    return (
        <Router>
            <AuthProvider>
                <SiteProvider>
                    <ContextConnector>
                        <AppContent />
                    </ContextConnector>
                </SiteProvider>
            </AuthProvider>
        </Router>
    );
};

export default App;