// react/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Disable browser navigation warnings
window.addEventListener('beforeunload', (e) => {
    // Cancel the event to prevent navigation
    e.preventDefault();
    // Chrome requires returnValue to be set
    e.returnValue = '';
});

// Wait for any existing app initialization if needed
const initReact = () => {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReact);
} else {
    initReact();
}